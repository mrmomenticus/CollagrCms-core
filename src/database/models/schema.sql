-- Создание таблицы товаров
CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL
);

COMMENT ON TABLE product IS 'Таблица с товарами';

COMMENT ON COLUMN product.id IS 'Первичный ключ';

COMMENT ON COLUMN product.name IS 'Название товара';

COMMENT ON COLUMN product.description IS 'Описание товара';

COMMENT ON COLUMN product.category IS 'Категория товара';

-- Создание таблицы изображений
CREATE TABLE image (
    id SERIAL PRIMARY KEY,
    img_path TEXT NOT NULL,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE
);

COMMENT ON TABLE image IS 'Таблица с изображениями';

COMMENT ON COLUMN image.id IS 'Первичный ключ';

COMMENT ON COLUMN image.img_path IS 'Путь к файлу изображения';

COMMENT ON COLUMN image.product_id IS 'Внешний ключ к товару';

-- Создание индекса для ускорения поиска по внешнему ключу
CREATE INDEX idx_image_product_id ON image (product_id);