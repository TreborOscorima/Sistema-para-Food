-- Fix double-encoded UTF-8 data in MySQL
-- Run manually: docker exec -i food_mysql mysql -u root -proot food_db < scripts/fix_encoding.sql

-- Productos
UPDATE food_productos
SET nombre = CONVERT(CAST(CONVERT(nombre USING latin1) AS BINARY) USING utf8mb4)
WHERE nombre LIKE '%Ã%';

UPDATE food_productos
SET descripcion = CONVERT(CAST(CONVERT(descripcion USING latin1) AS BINARY) USING utf8mb4)
WHERE descripcion LIKE '%Ã%';

-- Categorías
UPDATE food_categorias
SET nombre = CONVERT(CAST(CONVERT(nombre USING latin1) AS BINARY) USING utf8mb4)
WHERE nombre LIKE '%Ã%';

-- Insumos
UPDATE food_insumos
SET nombre = CONVERT(CAST(CONVERT(nombre USING latin1) AS BINARY) USING utf8mb4)
WHERE nombre LIKE '%Ã%';

-- Clientes
UPDATE food_clientes
SET nombre = CONVERT(CAST(CONVERT(nombre USING latin1) AS BINARY) USING utf8mb4)
WHERE nombre LIKE '%Ã%';

-- Combos
UPDATE food_combos
SET nombre = CONVERT(CAST(CONVERT(nombre USING latin1) AS BINARY) USING utf8mb4)
WHERE nombre LIKE '%Ã%';

SELECT 'Encoding fix completed' AS resultado;
