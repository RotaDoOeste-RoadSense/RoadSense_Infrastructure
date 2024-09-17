-- Tabela TRIPS
DROP TABLE IF EXISTS "trips";
CREATE TABLE "trips" (
  "trip_id" SERIAL PRIMARY KEY,
  "root_folder" VARCHAR(2000),
  "timestamp" TIMESTAMP,
  "way" VARCHAR(20),
  "starting_city" VARCHAR(200),
  "ending_city" VARCHAR(200)
);

-- Tabela IMAGE_DATA
DROP TABLE IF EXISTS "image_data";
CREATE TABLE "image_data" (
  "image_id" SERIAL PRIMARY KEY,
  "image_name" VARCHAR(200) NOT NULL,
  "latitude" DECIMAL(18,15) NOT NULL,
  "longitude" DECIMAL(18,15) NOT NULL,
  "timestamp" INT NOT NULL,
  "order" BIGINT,
  "trip_id" INT REFERENCES "trips"("trip_id")
);

-- Tabela all_plates_matched
DROP TABLE IF EXISTS "all_plates_matched";
CREATE TABLE "all_plates_matched" (
  "all_plates_matched_id" SERIAL PRIMARY KEY,
  "image_id" INT REFERENCES "image_data"("image_id")
);

-- Tabela plate_details
DROP TABLE IF EXISTS "plate_details";
CREATE TABLE "plate_details" (
  "plate_details_id" SERIAL PRIMARY KEY,
  "class_value" FLOAT,
  "class_name" VARCHAR(30),
  "prob" FLOAT,
  "x1" FLOAT,
  "y1" FLOAT,
  "x2" FLOAT,
  "y2" FLOAT,
  "all_plates_matched_id" INT REFERENCES "all_plates_matched"("all_plates_matched_id")
);

-- Tabela all_gps_coordinates
DROP TABLE IF EXISTS "all_gps_coordinates";
CREATE TABLE "all_gps_coordinates" (
  "all_gps_coordinates_id" SERIAL PRIMARY KEY,
  "plate_details_id" INT REFERENCES "plate_details"("plate_details_id"),
  "lat" DECIMAL(20,15),
  "lon" DECIMAL(20,15)
);

-- Tabela TRECHO
DROP TABLE IF EXISTS "section";
CREATE TABLE "section" (
  "section_id" SERIAL PRIMARY KEY,
  "start_latitude_coordinates" FLOAT NOT NULL,
  "start_longitude_coordinates" FLOAT NOT NULL,
  "end_latitude_coordinates" FLOAT NOT NULL,
  "end_longitude_coordinates" FLOAT NOT NULL,
  "highway_code" CHAR(50) NOT NULL,
  "section_mileage" VARCHAR(20) NOT NULL
);

-- Tabela AREA
DROP TABLE IF EXISTS "area";
CREATE TABLE "area" (
  "area_id" SERIAL PRIMARY KEY,
  "area_characteristics" VARCHAR(100) NOT NULL,
  "start_image_id" INT NOT NULL,
  "end_image_id" INT NOT NULL,
  "section_id" INT NOT NULL REFERENCES "section"("section_id")
);

-- Tabela ESTRUTURA
DROP TABLE IF EXISTS "structure";
CREATE TABLE "structure" (
  "structure_id" SERIAL PRIMARY KEY,
  "structure_type_description" VARCHAR(100) NOT NULL,
  "section_id" INT NOT NULL REFERENCES "section"("section_id")
);

-- Tabela MANUTENCAO
DROP TABLE IF EXISTS "maintenance";
CREATE TABLE "maintenance" (
  "maintenance_id" SERIAL PRIMARY KEY,
  "date" DATE NOT NULL,
  "state" FLOAT NOT NULL,
  "area_id" INT NOT NULL REFERENCES "area"("area_id")
);

-- Tabela VEGETACAO
DROP TABLE IF EXISTS "vegetation";
CREATE TABLE "vegetation" (
  "vegetation_id" SERIAL PRIMARY KEY,
  "image_file_name" VARCHAR(200) NOT NULL,
  "prediction" VARCHAR(20) NOT NULL,
  "score" FLOAT NOT NULL,
  "area_id" INT NOT NULL REFERENCES "area"("area_id"),
  "image_id" INT REFERENCES "image_data"("image_id")
);

-- Tabela placa_km
DROP TABLE IF EXISTS "km_plate";
CREATE TABLE "km_plate" (
  "km_plate_id" SERIAL PRIMARY KEY,
  "km" VARCHAR(20) NOT NULL,
  "BR" VARCHAR(20),
  "plate_details_id" INT NOT NULL REFERENCES "plate_details"("plate_details_id")
);

-- Tabela guardrail_details
DROP TABLE IF EXISTS "guardrail_details";
CREATE TABLE "guardrail_details" (
  "guardrail_details_id" SERIAL primary key,
  "class_value" FLOAT, 
  "class_name" VARCHAR(30),
  "cam" INT NOT NULL,
  "prob" FLOAT,
  "x1" FLOAT,
  "y1" FLOAT,
  "x2" FLOAT, 
  "y2" FLOAT, 
  "order" INT,
  "unique_id" INT,
  "image_id" INT REFERENCES "image_data"("image_id")
);


-- Tabela all_guardrail_matched
DROP TABLE IF EXISTS "all_guardrail_matched";
--CREATE TABLE "all_guardrail_matched" (
--  "all_guardrail_matched_id" SERIAL PRIMARY KEY,
--  "image_id" INT REFERENCES "image_data"("image_id")
--);
