-- Migración: Accesos a módulos independientes del rol
-- Fecha: 2026-07-18
-- Agrega campos acceso_mozos, acceso_caja, acceso_cocina, acceso_mostrador
-- a la tabla food_usuarios para permitir acceso multi-módulo por usuario.

ALTER TABLE food_usuarios
    ADD COLUMN acceso_mozos TINYINT(1) NOT NULL DEFAULT 0,
    ADD COLUMN acceso_caja TINYINT(1) NOT NULL DEFAULT 0,
    ADD COLUMN acceso_cocina TINYINT(1) NOT NULL DEFAULT 0,
    ADD COLUMN acceso_mostrador TINYINT(1) NOT NULL DEFAULT 0;

-- Setear defaults según rol actual (para que usuarios existentes
-- conserven acceso a su módulo principal).
UPDATE food_usuarios SET acceso_mozos = 1 WHERE rol = 'Mozo';
UPDATE food_usuarios SET acceso_caja = 1, acceso_mostrador = 1 WHERE rol = 'Caja';
UPDATE food_usuarios SET acceso_cocina = 1 WHERE rol = 'Cocina';
UPDATE food_usuarios SET acceso_mozos = 1, acceso_caja = 1, acceso_cocina = 1, acceso_mostrador = 1 WHERE rol = 'Admin';
