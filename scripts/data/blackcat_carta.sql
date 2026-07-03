-- ============================================================
-- BLACK CAT CAFÉ-BAR-PASTELERÍA — Carga masiva de carta
-- Usa @cid resuelto dinámicamente por slug='cat-black'
-- Seguro para correr en cualquier entorno (local o prod)
-- ============================================================

-- Resolver company_id por slug
SET @cid = (SELECT id FROM food_companies WHERE slug = 'cat-black' LIMIT 1);

-- Verificar que la empresa existe antes de modificar nada
SELECT
    CASE
        WHEN @cid IS NULL THEN 'ERROR: empresa cat-black no encontrada'
        ELSE CONCAT('OK: empresa encontrada con id=', @cid)
    END AS preflight;

-- Borrar datos previos de esta empresa
SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM food_productos  WHERE company_id = @cid;
DELETE FROM food_categorias WHERE company_id = @cid;
SET FOREIGN_KEY_CHECKS = 1;

-- ── CATEGORÍAS ────────────────────────────────────────────
INSERT INTO food_categorias (company_id, nombre, descripcion, orden, activa) VALUES
(@cid, 'Burgers',              'Hamburguesas artesanales',            1,  1),
(@cid, 'Alitas',               'Alitas de pollo',                     2,  1),
(@cid, 'Broaster',             'Pollo broaster',                      3,  1),
(@cid, 'Combos',               'Combos y menus completos',            4,  1),
(@cid, 'Salchipapas',          'Salchipapas y variantes',             5,  1),
(@cid, 'Cafe y Espresso',      'Cafes, espressos e infusiones',       6,  1),
(@cid, 'Frappes',              'Bebidas frappe frias',                7,  1),
(@cid, 'Jugos',                'Jugos naturales y con leche',         8,  1),
(@cid, 'Cocteles',             'Cocteles y tragos',                   9,  1),
(@cid, 'Bebidas',              'Gaseosas, agua, cerveza, jarras',     10, 1),
(@cid, 'Pasteles y Porciones', 'Tortas, kekes y postres por porcion', 11, 1),
(@cid, 'Sandwiches y Bocados', 'Croissants, empanadas y bocados',     12, 1);

-- ── BURGERS ───────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Burgers'), 'Burger Clasica',     'Hamburguesa con carne de res o pollo crispi, lechuga, tomate y papas fritas', 12.00, 1, '🍔'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Burgers'), 'Burger Salsa BBQ',   'Hamburguesa con carne de res con salsa BBQ casera, tocino y papas fritas', 14.00, 1, '🍔'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Burgers'), 'Burger Doble Carne', 'Doble carne de res, queso cheddar, tocino, cebolla caramelizada, papas fritas', 17.00, 1, '🍔'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Burgers'), 'Burger Royal',       'Carne de res, queso, huevo frito, jamon, tomate, lechuga, papas fritas', 15.00, 1, '🍔'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Burgers'), 'Choripan',           'Chorriso artesanal, lechuga, tomate y papas fritas', 18.00, 1, '🌭');

-- ── ALITAS ────────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Alitas'), 'Alitas Clasica',    '5 piezas de alitas, papas fritas + cremas', 10.00, 1, '🍗'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Alitas'), 'Alitas BBQ',        '5 piezas de alitas con salsa BBQ, papas fritas', 12.00, 1, '🍗'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Alitas'), 'Alitas Acevichada', '5 piezas de alitas con crema acevichada, papas fritas', 12.00, 1, '🍗');

-- ── BROASTER ──────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Broaster'), 'Ala Broaster',    'Pollo, ensalada, papas fritas + crema', 10.00, 1, '🍗'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Broaster'), 'Pierna Broaster', 'Pollo, ensalada, papas fritas + crema', 12.00, 1, '🍗'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Broaster'), 'Pecho Broaster',  'Pollo, ensalada, papas fritas + crema', 14.00, 1, '🍗');

-- ── COMBOS ────────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Combos'), 'Combo #1', 'Hamburguesa (res o pollo), lechuga, tomate + papas fritas + gaseosa, refresco o cafe', 14.00, 1, '🍱'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Combos'), 'Combo #2', '2 hamburguesas (res o pollo), lechuga, tomate + papas fritas + 2 vasos de gaseosa, refresco o cafe', 22.00, 1, '🍱'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Combos'), 'Combo #3', 'Broaster Burger, lechuga, tomate + papas fritas + gaseosa, refresco o cafe', 14.00, 1, '🍱'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Combos'), 'Combo #4', '2 salchipapas con hot-dog ahumado + 2 vasos de gaseosa, refresco o cafe', 25.00, 1, '🍱');

-- ── SALCHIPAPAS ───────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Salchipapas'), 'Salchipapa',     NULL, 10.00, 1, '🍟'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Salchipapas'), 'Choripapa',      NULL, 12.00, 1, '🍟'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Salchipapas'), 'Salchibroaster', NULL, 14.00, 1, '🍟');

-- ── CAFE Y ESPRESSO ───────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Latte',                             NULL,  12.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Capuccino',                         NULL,  10.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Americano',                         NULL,   6.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Capuccino con Crema Chantilly',     NULL,  12.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Flat White',                        NULL,   7.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Mocaccino',                         NULL,  13.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Expresso',                          NULL,   5.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Coffee Pasado',                     NULL,   4.00, 1, '☕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cafe y Espresso'), 'Infusiones (Te, Manzanilla, Anis)', 'Te, manzanilla y anis', 3.50, 1, '🍵');

-- ── FRAPPES ───────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappuccino',         NULL, 12.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe Moccaccino',   NULL, 12.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe de Oreo',      NULL, 10.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe de Fresa',     NULL, 10.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe de Chocolate', NULL, 10.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe de Vainilla',  NULL, 10.00, 1, '🧋'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Frappes'), 'Frappe de Caramelo',  NULL, 10.00, 1, '🧋');

-- ── JUGOS ─────────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Papaya',            NULL,  7.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Fresa',             NULL,  7.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Mango',             NULL,  8.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Pina',              NULL,  7.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Chirimoya',         NULL,  8.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Guanabana',         NULL,  8.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo Surtido',              NULL,  8.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo Especial',             NULL, 12.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Fresa con Leche',   NULL, 10.00, 1, '🥛'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Papaya con Leche',  NULL, 10.00, 1, '🥛'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Mango con Leche',   NULL, 10.00, 1, '🥛'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Pina con Leche',    NULL, 10.00, 1, '🥛'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Jugos'), 'Jugo de Guanabana con Leche',NULL, 10.00, 1, '🥛');

-- ── COCTELES ──────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Peru Libre',         NULL, 10.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Black Russian',      NULL, 10.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Chilcano',           NULL, 10.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Mojito Clasico',     NULL, 12.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Mojito de Maracuya', NULL, 12.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Pisco Sunrise',      NULL, 12.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Paloma',             NULL, 12.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Pisco Sour',         NULL, 12.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Pisco Punch Orange', NULL, 13.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Pina Colada',        NULL, 13.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Algarrobina',        NULL, 14.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'White Russian',      NULL, 14.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Margarita',          NULL, 14.00, 1, '🍹'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Cocteles'), 'Margarita Blue',     NULL, 14.00, 1, '🍹');

-- ── BEBIDAS ───────────────────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Jarra Maracuya',        NULL, 7.00, 1, '🧃'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Jarra Chicha',          NULL, 7.00, 1, '🧃'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Gaseosa Personal',      NULL, 4.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Gaseosa Litro y Medio', NULL, 8.00, 1, '🥤'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Agua Personal',         NULL, 2.00, 1, '💧'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Agua de Litro',         NULL, 3.50, 1, '💧'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Bebidas'), 'Cerveza 305 ml',        NULL, 7.00, 1, '🍺');

-- ── PASTELES Y PORCIONES ──────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Keke de Vainilla',              NULL, 7.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Keke Marmoleado',               NULL, 3.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Keke de Platano',               NULL, 7.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Carrot Cake',                   NULL, 8.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Torta de Chocolate',            NULL, 7.00, 1, '🎂'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Torta Helada',                  NULL, 8.00, 1, '🎂'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Cheesecake de Fresa',           NULL, 8.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Burger Cake',                   NULL, 8.00, 1, '🎂'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Torta Red Velvet',              NULL, 7.00, 1, '🎂'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Pionono de Chantilly Confresa', NULL, 7.00, 1, '🍰'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Crema Volteada',                NULL, 5.00, 1, '🍮'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Pie de Limon',                  NULL, 5.00, 1, '🥧'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Pie de Manzana',                NULL, 5.00, 1, '🥧'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Souffle de Manjar y Chantilly', NULL, 6.00, 1, '🍮'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Pasteles y Porciones'), 'Milhojas de Chantilly',         NULL, 6.00, 1, '🍰');

-- ── SANDWICHES Y BOCADOS ──────────────────────────────────
INSERT INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, emoji) VALUES
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Club Sandwich',      NULL, 7.00, 1, '🥪'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Croissant de Pollo', NULL, 7.00, 1, '🥐'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Croissant Mixto',    NULL, 6.00, 1, '🥐'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Empanada de Carne',  NULL, 4.00, 1, '🥟'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Empanada de Pollo',  NULL, 4.00, 1, '🥟'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Empanada Mixta',     NULL, 4.00, 1, '🥟'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), '2 Pan Pizza',        NULL, 5.00, 1, '🍕'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Triple',             NULL, 5.00, 1, '🥪'),
(@cid, (SELECT id FROM food_categorias WHERE company_id=@cid AND nombre='Sandwiches y Bocados'), 'Pan Butifarra',      NULL, 5.00, 1, '🌭');

-- ── Verificación final ────────────────────────────────────
SELECT COUNT(*) AS total_categorias FROM food_categorias WHERE company_id = @cid;
SELECT COUNT(*) AS total_productos  FROM food_productos  WHERE company_id = @cid;

SELECT c.nombre AS categoria, COUNT(p.id) AS productos
FROM food_categorias c
LEFT JOIN food_productos p ON p.categoria_id = c.id AND p.company_id = @cid
WHERE c.company_id = @cid
GROUP BY c.id, c.nombre
ORDER BY c.orden;
