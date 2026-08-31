#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico READ-ONLY de un turno de caja — reconciliación forense.

Corre dentro del contenedor de la app (reusa las env vars DB_* de la config) y
NO escribe nada: solo SELECTs. Reconstruye el arqueo del turno desde las filas
crudas (pagos, movimientos, pedidos) usando la MISMA lógica que
`calcular_resumen_turno`, lo compara contra el snapshot congelado del turno, y
vuelca la auditoría de la ventana del turno (correcciones/anulaciones/ediciones
de movimientos) para explicar cualquier descuadre.

Parámetros por env (todos opcionales salvo que se necesite ubicar el turno):
  DIAG_TURNO    id del turno (p.ej. 46). Es el "#46" que muestra el cierre.
  DIAG_COMPANY  id o subcadena del nombre de la empresa (p.ej. "CAT BLACK").
  DIAG_FECHA    'YYYY-MM-DD' local — para buscar turnos por fecha si no hay id.
  DIAG_PAIS     código de país para el corte de día local (default 'PE', UTC-5).

Uso:
  DIAG_TURNO=46 python scripts/diagnostico_caja.py
  DIAG_COMPANY="CAT BLACK" DIAG_FECHA=2026-08-29 python scripts/diagnostico_caja.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

# --- Códigos de sistema / mapeos (espejo de caja_turno_mixin._bucket_tipo) ---
_TIPO_A_BALDE = {
    "efectivo": "efectivo",
    "tarjeta": "tarjeta",
    "fiado": "fiado",
    # digital / otro → no deja efectivo en el cajón
}
D0 = Decimal("0.00")


def _dec(v) -> Decimal:
    if v is None:
        return D0
    return Decimal(str(v))


def _s(v) -> str:
    return "S/ %0.2f" % float(_dec(v))


def _bucket(tipo: str) -> str:
    return _TIPO_A_BALDE.get((tipo or "digital").lower(), "qr")


def _build_db_url() -> str:
    user = os.getenv("DB_USER") or "root"
    pw = os.getenv("DB_PASSWORD") or ""
    host = os.getenv("DB_HOST") or "localhost"
    port = int(os.getenv("DB_PORT") or "3306")
    name = os.getenv("DB_NAME") or "food_db"
    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(pw)}@{host}:{port}/{name}"
        f"?charset=utf8mb4"
    )


def _offset_horas(pais: str) -> int:
    # Perú/Colombia/Ecuador UTC-5; suficiente para acotar la búsqueda por fecha.
    return {"PE": 5, "CO": 5, "EC": 5, "BO": 4, "CL": 4, "AR": 3, "MX": 6}.get(
        (pais or "PE").upper(), 5
    )


def main() -> int:
    turno_id = os.getenv("DIAG_TURNO", "").strip()
    company_q = os.getenv("DIAG_COMPANY", "").strip()
    fecha = os.getenv("DIAG_FECHA", "").strip()
    pais = os.getenv("DIAG_PAIS", "PE").strip() or "PE"

    eng = create_engine(_build_db_url(), pool_pre_ping=True)
    with eng.connect() as cx:
        print("=" * 78)
        print("DIAGNÓSTICO DE CAJA (read-only) — TUWAYKIFOOD")
        print("=" * 78)

        # ---- Ubicar el turno --------------------------------------------------
        turno = None
        if turno_id:
            turno = cx.execute(
                text("SELECT * FROM food_turnos_caja WHERE id = :t"),
                {"t": int(turno_id)},
            ).mappings().first()
            if not turno:
                print(f"!! No existe turno id={turno_id}")
                return 2
        else:
            if not company_q:
                print("!! Falta DIAG_TURNO o DIAG_COMPANY+DIAG_FECHA")
                return 2
            comp = _resolver_company(cx, company_q)
            if comp is None:
                return 2
            off = _offset_horas(pais)
            # día local [00:00, 24:00) → ventana UTC-naive, con margen de 1 día.
            d = datetime.strptime(fecha, "%Y-%m-%d") if fecha else None
            if d is None:
                print("!! Falta DIAG_FECHA para buscar por empresa")
                return 2
            ini = d + timedelta(hours=off) - timedelta(days=1)
            fin = d + timedelta(days=1, hours=off) + timedelta(days=1)
            filas = cx.execute(
                text(
                    "SELECT * FROM food_turnos_caja "
                    "WHERE company_id = :c AND abierto_en BETWEEN :i AND :f "
                    "ORDER BY id"
                ),
                {"c": comp["id"], "i": ini, "f": fin},
            ).mappings().all()
            if not filas:
                print(f"!! Sin turnos para {comp['name']} cerca de {fecha}")
                return 2
            if len(filas) > 1:
                print(f"Varios turnos candidatos para {comp['name']} / {fecha}:")
                for t in filas:
                    print(f"  #{t['id']}  {t['abierto_en']} → {t['cerrado_en']}  estado={t['estado']}")
                print("Reintentá con DIAG_TURNO=<id>.")
            turno = filas[-1]

        cid = turno["company_id"]
        comp = cx.execute(
            text("SELECT id, name, slug, plan FROM food_companies WHERE id = :c"),
            {"c": cid},
        ).mappings().first()
        comp_name = comp["name"] if comp else f"(company {cid})"

        print(f"\nEmpresa : {comp_name}  (id={cid}, plan={comp['plan'] if comp else '?'})")
        print(f"Turno   : #{turno['id']}  estado={turno['estado']}")
        print(f"Apertura: {turno['abierto_en']}   Cierre: {turno['cerrado_en']}")
        print(f"Fondo inicial (monto_inicial): {_s(turno['monto_inicial'])}")

        # ---- Mapa método(código) → tipo, para bucketizar ----------------------
        metodos = cx.execute(
            text("SELECT codigo, nombre, tipo FROM food_metodos_pago WHERE company_id = :c"),
            {"c": cid},
        ).mappings().all()
        tipo_de = {m["codigo"].lower(): (m["tipo"] or "digital") for m in metodos}
        nombre_de = {m["codigo"].lower(): m["nombre"] for m in metodos}

        # ---- Pedidos del turno ------------------------------------------------
        pedidos = cx.execute(
            text(
                "SELECT id, estado, tipo_pedido, total, descuento, recargo, propina, "
                "vuelto, metodo_pago, cerrado_en, cancelado_en, motivo_cancelacion "
                "FROM food_pedidos WHERE company_id = :c AND turno_caja_id = :t "
                "ORDER BY id"
            ),
            {"c": cid, "t": turno["id"]},
        ).mappings().all()
        no_cancel = [p for p in pedidos if p["estado"] != "cancelado"]
        cancelados = [p for p in pedidos if p["estado"] == "cancelado"]
        validos = {p["id"] for p in no_cancel}

        # ---- Pagos del turno --------------------------------------------------
        pagos = cx.execute(
            text(
                "SELECT id, pedido_id, metodo, monto FROM food_pagos_pedido "
                "WHERE company_id = :c AND turno_caja_id = :t ORDER BY pedido_id"
            ),
            {"c": cid, "t": turno["id"]},
        ).mappings().all()

        # ---- Recompute (espejo de calcular_resumen_turno) ---------------------
        balde = {"efectivo": D0, "tarjeta": D0, "qr": D0, "fiado": D0}
        por_metodo: dict[str, Decimal] = {}
        ped_con_pago: set[int] = set()
        pagos_huerfanos = []
        for pg in pagos:
            if pg["pedido_id"] not in validos:
                pagos_huerfanos.append(pg)
                continue
            ped_con_pago.add(pg["pedido_id"])
            m = (pg["metodo"] or "efectivo").lower()
            monto = _dec(pg["monto"])
            balde[_bucket(tipo_de.get(m, "digital"))] += monto
            por_metodo[m] = por_metodo.get(m, D0) + monto

        ventas_netas = D0
        propinas = D0
        for p in no_cancel:
            propinas += _dec(p["propina"])
            ventas_netas += _dec(p["total"]) + _dec(p["recargo"]) - _dec(p["descuento"])
            if p["id"] in ped_con_pago:
                continue
            neto = _dec(p["total"]) - _dec(p["descuento"])
            m = (p["metodo_pago"] or "efectivo").lower()
            b = _bucket(tipo_de.get(m, "digital"))
            monto = neto if b == "fiado" else neto + _dec(p["propina"])
            balde[b] += monto
            por_metodo[m] = por_metodo.get(m, D0) + monto

        # ---- Movimientos de caja ---------------------------------------------
        movs = cx.execute(
            text(
                "SELECT id, tipo, categoria, monto, motivo, usuario_id, created_at "
                "FROM food_movimientos_caja WHERE company_id = :c AND turno_id = :t "
                "ORDER BY created_at, id"
            ),
            {"c": cid, "t": turno["id"]},
        ).mappings().all()
        ingresos = sum((_dec(m["monto"]) for m in movs if m["tipo"] == "ingreso"), D0)
        egresos = sum((_dec(m["monto"]) for m in movs if m["tipo"] == "egreso"), D0)

        esperado = _dec(turno["monto_inicial"]) + balde["efectivo"] + ingresos - egresos

        # ---- Reporte ----------------------------------------------------------
        print("\n" + "-" * 78)
        print("PEDIDOS DEL TURNO")
        print("-" * 78)
        print(f"  Cobrados (no cancelados): {len(no_cancel)}   Cancelados: {len(cancelados)}")
        for p in no_cancel:
            extra = ""
            if _dec(p["recargo"]):
                extra += f" +rec {_s(p['recargo'])}"
            if _dec(p["descuento"]):
                extra += f" -desc {_s(p['descuento'])}"
            if _dec(p["propina"]):
                extra += f" prop {_s(p['propina'])}"
            if _dec(p["vuelto"]):
                extra += f" vuelto {_s(p['vuelto'])}"
            print(f"  #{p['id']:<6} {p['estado']:<10} {p['tipo_pedido']:<10} "
                  f"total {_s(p['total'])}  pago={p['metodo_pago']}{extra}")
        if cancelados:
            print("  -- CANCELADOS (no cuentan en el arqueo) --")
            for p in cancelados:
                print(f"  #{p['id']:<6} total {_s(p['total'])}  cancelado_en={p['cancelado_en']} "
                      f"motivo={p['motivo_cancelacion']}")

        print("\n" + "-" * 78)
        print("PAGOS DEL TURNO (food_pagos_pedido)  →  por método")
        print("-" * 78)
        for m in sorted(por_metodo):
            print(f"  {nombre_de.get(m, m):<16} {_s(por_metodo[m])}   (tipo={tipo_de.get(m,'?')})")
        if pagos_huerfanos:
            print("  !! PAGOS de pedidos CANCELADOS aún etiquetados al turno:")
            for pg in pagos_huerfanos:
                print(f"     pago#{pg['id']} pedido#{pg['pedido_id']} {pg['metodo']} {_s(pg['monto'])}")

        print("\n" + "-" * 78)
        print("MOVIMIENTOS DE CAJA")
        print("-" * 78)
        if not movs:
            print("  (ninguno)")
        for m in movs:
            print(f"  {m['created_at']}  {m['tipo']:<8} {m['categoria']:<16} "
                  f"{_s(m['monto'])}  motivo='{m['motivo']}' usuario_id={m['usuario_id']}")
        print(f"  Σ ingresos = {_s(ingresos)}   Σ egresos = {_s(egresos)}")

        # ---- Reconciliación: recompute vs snapshot congelado ------------------
        print("\n" + "=" * 78)
        print("ARQUEO — RECOMPUTE (crudo) vs SNAPSHOT (congelado al cierre)")
        print("=" * 78)
        filas_cmp = [
            ("Ventas netas",        ventas_netas,      None),
            ("Propinas",            propinas,          turno["total_propinas"]),
            ("Efectivo (balde)",    balde["efectivo"], turno["total_efectivo"]),
            ("Tarjeta (balde)",     balde["tarjeta"],  turno["total_tarjeta"]),
            ("QR/digital (balde)",  balde["qr"],       turno["total_qr"]),
            ("Fiado (balde)",       balde["fiado"],    turno["total_fiado"]),
            ("Ingresos caja",       ingresos,          turno["total_ingresos"]),
            ("Egresos caja",        egresos,           turno["total_egresos"]),
            ("Esperado efectivo",   esperado,          turno["esperado_efectivo"]),
        ]
        print(f"  {'Concepto':<22}{'Recompute':>14}{'Snapshot':>14}   Δ")
        for label, calc, snap in filas_cmp:
            if snap is None:
                print(f"  {label:<22}{_s(calc):>14}{'—':>14}")
                continue
            d = _dec(calc) - _dec(snap)
            flag = "  <-- DIFERENCIA" if abs(d) >= Decimal("0.01") else ""
            print(f"  {label:<22}{_s(calc):>14}{_s(snap):>14}   {float(d):+0.2f}{flag}")

        contado = _dec(turno["contado_efectivo"])
        descuadre_snap = _dec(turno["descuadre"])
        descuadre_calc = contado - esperado
        print("\n  Contado en caja (lo que tipeó el cajero): " + _s(contado))
        print(f"  Descuadre snapshot : {float(descuadre_snap):+0.2f}")
        print(f"  Descuadre recompute: {float(descuadre_calc):+0.2f}  (contado - esperado_recompute)")
        if descuadre_snap > 0:
            print(f"  → SOBRA {_s(abs(descuadre_snap))} de efectivo (había más de lo esperado)")
        elif descuadre_snap < 0:
            print(f"  → FALTA {_s(abs(descuadre_snap))} de efectivo")
        else:
            print("  → Caja cuadrada")

        # ---- Auditoría de la ventana del turno --------------------------------
        print("\n" + "=" * 78)
        print("AUDITORÍA en la ventana del turno (ediciones / anulaciones / correcciones)")
        print("=" * 78)
        ini = turno["abierto_en"]
        if turno["cerrado_en"]:
            fin = turno["cerrado_en"] + timedelta(hours=12)
        else:
            # Turno aún abierto: la ventana llega hasta "ahora" (hora del server).
            fin = cx.execute(text("SELECT UTC_TIMESTAMP()")).scalar()
        aud = cx.execute(
            text(
                "SELECT created_at, usuario_nombre, accion, entidad, entidad_id, detalle "
                "FROM food_auditoria WHERE company_id = :c "
                "AND created_at BETWEEN :i AND :f ORDER BY created_at"
            ),
            {"c": cid, "i": ini, "f": fin},
        ).mappings().all()
        sospechosas = ("correccion", "anulacion", "reversion", "eliminacion", "movimiento", "cierre")
        rel = [a for a in aud if any(k in (a["accion"] or "").lower() for k in sospechosas)]
        if not rel:
            print("  (sin acciones de corrección/anulación/edición de movimientos en la ventana)")
        for a in rel:
            det = (a["detalle"] or "").replace("\n", " ")
            if len(det) > 400:
                det = det[:400] + "…"
            print(f"  {a['created_at']}  {a['accion']}  entidad={a['entidad']}#{a['entidad_id']}  "
                  f"por {a['usuario_nombre']}")
            if det:
                print(f"      detalle: {det}")

        print("\n" + "=" * 78)
        print("FIN DEL DIAGNÓSTICO (no se escribió nada)")
        print("=" * 78)
    return 0


def _resolver_company(cx, q: str):
    if q.isdigit():
        row = cx.execute(
            text("SELECT id, name, slug, plan FROM food_companies WHERE id = :i"),
            {"i": int(q)},
        ).mappings().first()
        if not row:
            print(f"!! No existe company id={q}")
        return row
    rows = cx.execute(
        text("SELECT id, name, slug, plan FROM food_companies WHERE name LIKE :q ORDER BY id"),
        {"q": f"%{q}%"},
    ).mappings().all()
    if not rows:
        print(f"!! Ninguna empresa matchea '{q}'")
        return None
    if len(rows) > 1:
        print(f"Varias empresas matchean '{q}':")
        for r in rows:
            print(f"  id={r['id']}  {r['name']}  (plan={r['plan']})")
        print("Reintentá con DIAG_COMPANY=<id>.")
        return None
    return rows[0]


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    raise SystemExit(main())
