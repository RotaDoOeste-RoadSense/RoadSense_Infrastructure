DROP TABLE IF EXISTS "horizontal_markings";
CREATE TABLE "horizontal_markings" (
  "horizontal_markings_id" SERIAL PRIMARY KEY,
  "class_id" SMALLINT,
  "class_name" CHAR(20),
  "mask_polygon" TEXT,
  "quality_score" REAL,
  "image_id" INT REFERENCES "image_data"("image_id")
);