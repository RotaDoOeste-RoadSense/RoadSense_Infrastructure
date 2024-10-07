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
  "status" SMALLINT,
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
  "image_id" INT REFERENCES "image_data"("image_id"),
  "pred_true" FLOAT
);

CREATE TABLE public.guardrails_cro (
    id serial4 NOT NULL,
    km varchar NULL,
    km_final varchar NULL,
    sentido varchar NULL,
    tipo varchar NULL,
    altura float8 NULL,
    comprimento float8 NULL,
    lado varchar NULL,
    geom public.geometry(linestring, 4326) NULL,
    CONSTRAINT guardrails_cro_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_guardrails_cro_geom ON public.guardrails_cro USING gist (geom);

-- -- Tabela km_cro
DROP TABLE IF EXISTS "km_cro";
CREATE TABLE "km_cro" (
  "km_cro_id" SERIAL PRIMARY KEY,
  "geom" geometry(Point, 4326) -- Usando o EPSG 4326, que é o sistema de coordenadas geográficas padrão (WGS 84)
);

-- Tabela drainage_details
DROP TABLE IF EXISTS "drainage_details";
CREATE TABLE "drainage_details" (
  "drainage_details_id" SERIAL primary key,
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

-- Tabela structure_cro
DROP TABLE IF EXISTS "structures_cro";
CREATE TABLE "structures_cro" (
  "structure_cro_id" SERIAL primary key,
  "name" VARCHAR(120),
  "geom_structure" geometry(Point, 4326)
);

-- Tabela dev_leadership
DROP TABLE IF EXISTS "dev_leadership";
CREATE TABLE "dev_dealership" (
  "id" SERIAL PRIMARY KEY,
  "name" VARCHAR,
  "date_end" DATE,
  "date_start" DATE
);

-- Tabela dev_import
DROP TABLE IF EXISTS "dev_import";
CREATE TABLE "dev_import" (
  "id" SERIAL PRIMARY KEY,
  "name_file" VARCHAR,
  "refer_year" INT,
  "refer_month" INT,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "file" BYTEA NULL,
  "column_names" VARCHAR,
  "column_select" VARCHAR,
  "process" INT DEFAULT 0,
  "date_process" TIMESTAMP,
  type INT,
  "coordinates" VARCHAR,
  "sheets_name" VARCHAR,
  "dealership_id" INT REFERENCES "dev_dealership"("id")
);

-- Tabela dev_guardrail
DROP TABLE IF EXISTS "dev_guardrail";
CREATE TABLE "dev_guardrail" (
  "id" SERIAL PRIMARY KEY,
  "geom" GEOMETRY,
  "attributes" JSON,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "dev_import_id" INT REFERENCES "dev_import"("id") ON DELETE CASCADE
);

-- Tabela dev_plates
DROP TABLE IF EXISTS "dev_plate";
CREATE TABLE "dev_plate" (
    "id" SERIAL PRIMARY KEY,
    "geom" GEOMETRY NULL,
    "attributes" JSON NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "dev_import_id" INT NULL REFERENCES "dev_import"("id") ON DELETE CASCADE
);


-- View area_vegetacao
CREATE OR REPLACE VIEW area_vegetacao AS
SELECT 
    a.area_id,
    a.area_characteristics,
    m.state,
    CASE
        WHEN UPPER(a.area_characteristics) LIKE '%LATERAL_DIREITA%' THEN
            ST_MAKELINE(ST_SETSRID(ST_MAKEPOINT(id.longitude + 0.00005, id.latitude), 4326) ORDER BY id."order")
        WHEN UPPER(a.area_characteristics) LIKE '%LATERAL_ESQUERDA%' THEN
            ST_MAKELINE(ST_SETSRID(ST_MAKEPOINT(id.longitude - 0.00005, id.latitude), 4326) ORDER BY id."order")
        ELSE 
            ST_MAKELINE(ST_SETSRID(ST_MAKEPOINT(id.longitude, id.latitude), 4326) ORDER BY id."order")
    END AS geom
FROM 
    area a
JOIN 
    maintenance m ON m.area_id = a.area_id
JOIN 
    vegetation v ON v.area_id = a.area_id
JOIN 
    image_data id ON id.image_id = v.image_id
GROUP BY 
    a.area_id, a.area_characteristics, m.state;

-- View plate_point
DROP VIEW IF EXISTS plate_point;
CREATE OR REPLACE VIEW plate_point AS
SELECT 
    pd.plate_details_id,
    id.image_id,
    id.image_name,
    id.trip_id,
    pd.class_value,
    pd.class_name,
    pd.prob,
    pd.x1,
    pd.y1,
    pd.x2,
    pd.y2,
    pd.status,
    pd.all_plates_matched_id,
    ST_SetSRID(ST_MakePoint(id.longitude, id.latitude), 4326) AS geom
FROM 
    plate_details pd
JOIN 
    all_plates_matched apm ON apm.all_plates_matched_id = pd.all_plates_matched_id
JOIN 
    image_data id ON id.image_id = apm.image_id;

-- View image_data_with_geom
CREATE OR REPLACE VIEW image_data_with_geom AS
SELECT 
    image_id,
    image_name,
    "timestamp",
    "order",
    trip_id,
    ST_SetSRID(ST_MakePoint(longitude + 0.00003, latitude), 4326) AS geom
FROM 
    image_data;

-- View pred_guardrails_with_geom
CREATE OR REPLACE VIEW public.pred_guardrails_with_geom AS
SELECT 
    row_number() OVER () AS rnum,
    gd.class_name,
    gd.cam,
    gd.pred_true,
    gd."order",
    gd.unique_id,
    img.trip_id,
    ST_SetSRID(img.geom, 4326) AS geom
FROM 
    guardrail_details gd
JOIN 
    image_data_with_geom img ON gd.image_id = img.image_id;

-- View  dev_plate_miss
DROP VIEW IF EXISTS dev_plate_miss;
CREATE OR REPLACE VIEW dev_plate_miss AS
SELECT 
    dp.id,
    dp.attributes,
    dp.created_at,
    st_buffer(dp.geom, 0.0001, 'quad_segs=8') AS st_buffer
FROM 
    dev_plate dp
WHERE 
    NOT EXISTS (
        SELECT 1
        FROM plate_point pp
        WHERE ST_DWithin(dp.geom, pp.geom, 0.0001)
    );

-- View guardrails_cro_evelop
CREATE OR REPLACE VIEW guardrails_cro_evelop AS
SELECT 
    ROW_NUMBER() OVER () AS rnum,
    id,
    ST_SetSRID(st_buffer(geom, 0.00015, 'endcap=flat join=round'), 4326) AS geom,
    sentido,
    tipo,
    lado
FROM 
    guardrails_cro dg;

-- View guardrails_evelop_analysis 
CREATE OR REPLACE VIEW guardrails_evelop_analysis AS
SELECT 
    ROW_NUMBER() OVER () AS rnum,
    id,
    ST_SetSRID(st_buffer(geom, 0.00015, 'endcap=flat join=round'), 4326) AS geom,
    sentido,
    tipo,
    lado
FROM 
    guardrails_cro dg
WHERE 
    sentido = 'NORTE' 
    AND tipo LIKE '%concr%' 
    AND lado = 'DIREITO';

-- View image_data_point
CREATE OR REPLACE VIEW image_data_point AS
SELECT 
    image_id,
    image_name,
    latitude,
    longitude,
    "timestamp",
    "order",
    trip_id,
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) AS geom
FROM 
    image_data id;

-- View plate_multiple_point
CREATE OR REPLACE VIEW plate_multiple_point AS
SELECT 
    id.image_id,
    id.image_name,
    id.latitude,
    id.longitude,
    id."timestamp",
    id."order",
    id.trip_id,
    COUNT(pd.plate_details_id) AS plates,
    JSONB_AGG(
        JSON_BUILD_OBJECT(
            'plate_details_id', pd.plate_details_id,
            'class_value', pd.class_value,
            'class_name', pd.class_name,
            'prob', pd.prob,
            'x1', pd.x1,
            'y1', pd.y1,
            'x2', pd.x2,
            'y2', pd.y2,
            'status', pd.status
        )
    ) AS plate_detail,
    ST_SetSRID(ST_MakePoint(id.longitude, id.latitude), 4326) AS geom
FROM 
    image_data id
JOIN 
    all_plates_matched apm ON apm.image_id = id.image_id
JOIN 
    plate_details pd ON pd.all_plates_matched_id = apm.all_plates_matched_id
GROUP BY 
    id.image_id, 
    id.image_name, 
    id.latitude, 
    id.longitude, 
    id."timestamp", 
    id."order", 
    id.trip_id;

-- View section_view
CREATE OR REPLACE VIEW section_view AS
SELECT 
    section_id,
    start_latitude_coordinates,
    start_longitude_coordinates,
    end_latitude_coordinates,
    end_longitude_coordinates,
    highway_code,
    section_mileage,
    ST_MakePoint(start_longitude_coordinates, start_latitude_coordinates) AS start_point,
    ST_MakePoint(end_longitude_coordinates, end_latitude_coordinates) AS end_point,
    ST_MakeLine(
        ST_MakePoint(start_longitude_coordinates, start_latitude_coordinates), 
        ST_MakePoint(end_longitude_coordinates, end_latitude_coordinates)
    ) AS line
FROM 
    section;

-- View sub_guardrails_with_geom
CREATE OR REPLACE VIEW sub_guardrails_with_geom AS
SELECT 
    pg.rnum,
    pg.class_name,
    pg.cam,
    pg.pred_true,
    pg."order",
    pg.unique_id,
    ST_SetSRID(pg.geom, 4326) AS geom
FROM 
    pred_guardrails_with_geom pg
JOIN 
    guardrails_evelop_analysis ga ON pg.unique_id = ga.id
WHERE 
    pg.class_name LIKE '%met%';

-- View trip linestring
CREATE OR REPLACE VIEW public.trip_linestring AS
SELECT 
    t.trip_id,
    t.way,
    t.starting_city,
    t.ending_city,
    ST_MakeLine(
        ST_SetSRID(ST_MakePoint(id.longitude, id.latitude), 4326) 
        ORDER BY id."order"
    ) AS geom
FROM 
    trips t
JOIN 
    image_data id ON id.trip_id = t.trip_id 
    AND id.longitude <> 0 
    AND id.latitude <> 0
GROUP BY 
    t.trip_id, 
    t.way, 
    t.starting_city, 
    t.ending_city;

-- View trip_linestring
CREATE OR REPLACE VIEW public.trip_linestring AS
SELECT 
    t.trip_id,
    t.way,
    t.starting_city,
    t.ending_city,
    ST_MakeLine(
        ST_SetSRID(ST_MakePoint(id.longitude, id.latitude), 4326) 
        ORDER BY id."order"
    ) AS geom
FROM 
    trips t
JOIN 
    image_data id ON id.trip_id = t.trip_id 
    AND id.longitude <> 0 
    AND id.latitude <> 0
GROUP BY 
    t.trip_id, 
    t.way, 
    t.starting_city, 
    t.ending_city;
