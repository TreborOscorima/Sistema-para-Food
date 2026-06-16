-- Seed data para testing local — company_id=1
-- Mesas
INSERT IGNORE INTO food_mesas (company_id, numero, nombre, capacidad, estado, activa, created_at, updated_at) VALUES
(1, 1, 'Mesa 1', 4, 'libre', 1, NOW(), NOW()),
(1, 2, 'Mesa 2', 4, 'libre', 1, NOW(), NOW()),
(1, 3, 'Mesa 3', 6, 'libre', 1, NOW(), NOW()),
(1, 4, 'Mesa 4', 2, 'libre', 1, NOW(), NOW()),
(1, 5, 'Terraza 1', 4, 'libre', 1, NOW(), NOW());

-- Categorias
INSERT IGNORE INTO food_categorias (company_id, nombre, descripcion, orden, activa, created_at, updated_at) VALUES
(1, 'Entradas', 'Sopas, causas y entradas frias y calientes', 1, 1, NOW(), NOW()),
(1, 'Platos de Fondo', 'Carnes, pastas y platos principales', 2, 1, NOW(), NOW()),
(1, 'Bebidas', 'Jugos, gaseosas y bebidas calientes', 3, 1, NOW(), NOW()),
(1, 'Postres', 'Dulces y helados', 4, 1, NOW(), NOW());

-- Productos
INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Caldo de Gallina', 'Caldo casero con fideos y papa', 12.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Entradas';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Causa Rellena', 'Causa de papa amarilla rellena con pollo', 14.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Entradas';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Lomo Saltado', 'Clasico lomo saltado con papas fritas', 28.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Platos de Fondo';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Pollo a la Brasa 1/4', 'Cuarto de pollo con ensalada y papas', 22.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Platos de Fondo';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Aji de Gallina', 'Aji de gallina cremoso con arroz', 24.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Platos de Fondo';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Chicha Morada', 'Chicha morada natural 500ml', 6.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Bebidas';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Inca Kola 500ml', 'Inca Kola en botella', 5.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Bebidas';

INSERT IGNORE INTO food_productos (company_id, categoria_id, nombre, descripcion, precio, disponible, created_at, updated_at)
SELECT 1, c.id, 'Mazamorra Morada', 'Postre tradicional peruano', 8.00, 1, NOW(), NOW()
FROM food_categorias c WHERE c.company_id=1 AND c.nombre='Postres';

-- Verificacion final
SELECT 'Mesas' as tabla, COUNT(*) as total FROM food_mesas WHERE company_id=1
UNION ALL SELECT 'Categorias', COUNT(*) FROM food_categorias WHERE company_id=1
UNION ALL SELECT 'Productos', COUNT(*) FROM food_productos WHERE company_id=1;
