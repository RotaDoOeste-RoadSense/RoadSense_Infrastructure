-- Tabela TRIPS
DROP TABLE IF EXISTS "TRIPS";
CREATE TABLE "TRIPS" (
  "trip_id" SERIAL PRIMARY KEY,
  "root_folder" VARCHAR(2000),
  "timestamp" TIMESTAMP
);

-- Tabela IMAGE_DATA
DROP TABLE IF EXISTS "IMAGE_DATA";
CREATE TABLE "IMAGE_DATA" (
  "id" SERIAL PRIMARY KEY,
  "nome_imagem" VARCHAR(200) NOT NULL,
  "latitude" DECIMAL(18,15) NOT NULL,
  "longitude" DECIMAL(18,15) NOT NULL,
  "timestamp" INT NOT NULL,
  "order" BIGINT,
  "trip_id" INT REFERENCES "TRIPS"("trip_id")
);

-- Tabela all_plates_matched
DROP TABLE IF EXISTS "all_plates_matched";
CREATE TABLE "all_plates_matched" (
  "id" SERIAL PRIMARY KEY,
  "image_id" INT REFERENCES "IMAGE_DATA"("id")
);

-- Tabela plate_details
DROP TABLE IF EXISTS "plate_details";
CREATE TABLE "plate_details" (
  "id" SERIAL PRIMARY KEY,
  "class_value" FLOAT,
  "class_name" VARCHAR(30),
  "prob" FLOAT,
  "x1" FLOAT,
  "y1" FLOAT,
  "x2" FLOAT,
  "y2" FLOAT,
  "image_id" INT REFERENCES "all_plates_matched"("id")
);

-- Tabela all_gps_coordinates
DROP TABLE IF EXISTS "all_gps_coordinates";
CREATE TABLE "all_gps_coordinates" (
  "id" SERIAL PRIMARY KEY,
  "plate_details_id" INT REFERENCES "plate_details"("id"),
  "lat" DECIMAL(20,15),
  "lon" DECIMAL(20,15)
);

-- Tabela TRECHO
DROP TABLE IF EXISTS "TRECHO";
CREATE TABLE "TRECHO" (
  "ID_TRECHO" SERIAL PRIMARY KEY,
  "coordenadas_latitude_inicio" FLOAT NOT NULL,
  "coordenadas_longitude_inicio" FLOAT NOT NULL,
  "coordenadas_latitude_fim" FLOAT NOT NULL,
  "coordenadas_longitude_fim" FLOAT NOT NULL,
  "codigo_rodovia" CHAR(14) NOT NULL,
  "quilometragem_trecho" VARCHAR(20) NOT NULL
);

-- Tabela AREA
DROP TABLE IF EXISTS "AREA";
CREATE TABLE "AREA" (
  "ID_AREA" SERIAL PRIMARY KEY,
  "caracteristicas_area" VARCHAR(100) NOT NULL,
  "id_imagem_inicio" INT NOT NULL,
  "id_imagem_fim" INT NOT NULL,
  "ID_TRECHO" INT NOT NULL REFERENCES "TRECHO"("ID_TRECHO")
);

-- Tabela ESTRUTURA
DROP TABLE IF EXISTS "ESTRUTURA";
CREATE TABLE "ESTRUTURA" (
  "ID_ESTRUTURA" SERIAL PRIMARY KEY,
  "descricao_tipo_estrutura" VARCHAR(100) NOT NULL,
  "ID_TRECHO" INT NOT NULL REFERENCES "TRECHO"("ID_TRECHO")
);

-- Tabela MANUTENCAO
DROP TABLE IF EXISTS "MANUTENCAO";
CREATE TABLE "MANUTENCAO" (
  "ID_MANUTENCAO" SERIAL PRIMARY KEY,
  "data" DATE NOT NULL,
  "situacao" FLOAT NOT NULL,
  "ID_AREA" INT NOT NULL REFERENCES "AREA"("ID_AREA")
);

-- Tabela VEGETACAO
DROP TABLE IF EXISTS "VEGETACAO";
CREATE TABLE "VEGETACAO" (
  "ID_VEGETACAO" SERIAL PRIMARY KEY,
  "nome_arquivo_imagem" VARCHAR(200) NOT NULL,
  "classificacao" VARCHAR(20) NOT NULL,
  "score" FLOAT NOT NULL,
  "ID_AREA" INT NOT NULL REFERENCES "AREA"("ID_AREA"),
  "ID_IMAGE_DATA" INT NOT NULL REFERENCES "IMAGE_DATA"("id")
);

-- Tabela placa_km
DROP TABLE IF EXISTS "placa_km";
CREATE TABLE "placa_km" (
  "id_placa_km" SERIAL PRIMARY KEY,
  "km" VARCHAR(20) NOT NULL,
  "BR" VARCHAR(20),
  "id" INT NOT NULL REFERENCES "plate_details"("id")
);

-- Tabela all_guardrail_matched
DROP TABLE IF EXISTS "all_guardrail_matched";
CREATE TABLE "all_guardrail_matched" (
  "id" SERIAL PRIMARY KEY,
  "image_id" INT REFERENCES "IMAGE_DATA"("id")
);

-- Tabela guardrail_details
DROP TABLE IF EXISTS "guardrail_details";
CREATE TABLE "guardrail_details" (
  "id" SERIAL,
  "class_value" FLOAT, 
  "class_name" VARCHAR(30),
  "cam" INT NOT NULL,
  "prob" FLOAT,
  "x1" FLOAT,
  "y1" FLOAT,
  "x2" FLOAT, 
  "y2" FLOAT, 
  "image_id" INT REFERENCES "all_guardrail_matched"("id"),
  PRIMARY KEY ("id", "cam")
);
