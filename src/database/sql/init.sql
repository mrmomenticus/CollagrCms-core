CREATE TABLE Product
(
  id          INT     GENERATED ALWAYS AS IDENTITY,
  name        VARCHAR,
  description VARCHAR,
  category    VARCHAR,
  img_path    VARCHAR,
  PRIMARY KEY (id)
);

COMMENT ON TABLE Product IS 'Таблица с товарами ';
