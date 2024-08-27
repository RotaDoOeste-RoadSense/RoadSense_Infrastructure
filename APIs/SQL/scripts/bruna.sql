-- Tabela TRIPS
DROP TABLE IF EXISTS `TRIPS`;
CREATE TABLE `TRIPS` (
  `trip_id` int NOT NULL AUTO_INCREMENT,
  `root_folder` varchar(2000) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`trip_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela IMAGE_DATA
DROP TABLE IF EXISTS `IMAGE_DATA`;
CREATE TABLE `IMAGE_DATA` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome_imagem` varchar(200) NOT NULL,
  `latitude` decimal(18,15) NOT NULL,
  `longitude` decimal(18,15) NOT NULL,
  `timestamp` int NOT NULL,
  `order` bigint DEFAULT NULL,
  `trip_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trip_id` (`trip_id`),
  CONSTRAINT `IMAGE_DATA_ibfk_1` FOREIGN KEY (`trip_id`) REFERENCES `TRIPS` (`trip_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6847 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela all_plates_matched
DROP TABLE IF EXISTS `all_plates_matched`;
CREATE TABLE `all_plates_matched` (
  `id` int NOT NULL AUTO_INCREMENT,
  `image_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `all_plates_matched_ibfk_1` FOREIGN KEY (`image_id`) REFERENCES `IMAGE_DATA` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela plate_details
DROP TABLE IF EXISTS `plate_details`;
CREATE TABLE `plate_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_value` float DEFAULT NULL,
  `class_name` varchar(30) DEFAULT NULL,
  `prob` float DEFAULT NULL,
  `x1` float DEFAULT NULL,
  `y1` float DEFAULT NULL,
  `x2` float DEFAULT NULL,
  `y2` float DEFAULT NULL,
  `image_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `plate_details_ibfk_1` FOREIGN KEY (`image_id`) REFERENCES `all_plates_matched` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela all_gps_coordinates
DROP TABLE IF EXISTS `all_gps_coordinates`;
CREATE TABLE `all_gps_coordinates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plate_details_id` int DEFAULT NULL,
  `lat` decimal(20,15) DEFAULT NULL,
  `lon` decimal(20,15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `plate_details_id` (`plate_details_id`),
  CONSTRAINT `all_gps_coordinates_ibfk_1` FOREIGN KEY (`plate_details_id`) REFERENCES `plate_details` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela TRECHO
DROP TABLE IF EXISTS `TRECHO`;
CREATE TABLE `TRECHO` (
  `ID_TRECHO` int NOT NULL AUTO_INCREMENT,
  `coordenadas_latitude_inicio` varchar(20) NOT NULL,
  `coordenadas_longitude_inicio` varchar(20) NOT NULL,
  `coordenadas_latitude_fim` varchar(20) NOT NULL,
  `coordenadas_longitude_fim` varchar(20) NOT NULL,
  `codigo_rodovia` char(14) NOT NULL,
  `quilometragem_trecho` varchar(20) NOT NULL,
  PRIMARY KEY (`ID_TRECHO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela AREA
DROP TABLE IF EXISTS `AREA`;
CREATE TABLE `AREA` (
  `ID_AREA` int NOT NULL AUTO_INCREMENT,
  `caracteristicas_area` varchar(100) NOT NULL,
  `id_imagem_inicio` int NOT NULL,
  `id_imagem_fim` int NOT NULL,
  `ID_TRECHO` int NOT NULL,
  PRIMARY KEY (`ID_AREA`),
  KEY `ID_TRECHO` (`ID_TRECHO`),
  CONSTRAINT `AREA_ibfk_1` FOREIGN KEY (`ID_TRECHO`) REFERENCES `TRECHO` (`ID_TRECHO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela ESTRUTURA
DROP TABLE IF EXISTS `ESTRUTURA`;
CREATE TABLE `ESTRUTURA` (
  `ID_ESTRUTURA` int NOT NULL AUTO_INCREMENT,
  `descricao_tipo_estrutura` varchar(100) NOT NULL,
  `ID_TRECHO` int NOT NULL,
  PRIMARY KEY (`ID_ESTRUTURA`),
  KEY `ID_TRECHO` (`ID_TRECHO`),
  CONSTRAINT `ESTRUTURA_ibfk_1` FOREIGN KEY (`ID_TRECHO`) REFERENCES `TRECHO` (`ID_TRECHO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela MANUTENCAO
DROP TABLE IF EXISTS `MANUTENCAO`;
CREATE TABLE `MANUTENCAO` (
  `ID_MANUTENCAO` int NOT NULL AUTO_INCREMENT,
  `data` date NOT NULL,
  `situacao` float NOT NULL,
  `ID_AREA` int NOT NULL,
  PRIMARY KEY (`ID_MANUTENCAO`),
  KEY `ID_AREA` (`ID_AREA`),
  CONSTRAINT `MANUTENCAO_ibfk_1` FOREIGN KEY (`ID_AREA`) REFERENCES `AREA` (`ID_AREA`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela VEGETACAO
DROP TABLE IF EXISTS `VEGETACAO`;
CREATE TABLE `VEGETACAO` (
  `ID_VEGETACAO` int NOT NULL AUTO_INCREMENT,
  `nome_arquivo_imagem` varchar(200) NOT NULL,
  `classificacao` varchar(20) NOT NULL,
  `score` float NOT NULL,
  `ID_AREA` int NOT NULL,
  `ID_IMAGE_DATA` int NOT NULL,
  PRIMARY KEY (`ID_VEGETACAO`),
  KEY `ID_AREA` (`ID_AREA`),
  CONSTRAINT `VEGETACAO_ibfk_1` FOREIGN KEY (`ID_AREA`) REFERENCES `AREA` (`ID_AREA`),
  KEY `ID_IMAGE_DATA` (`ID_IMAGE_DATA`),
  CONSTRAINT `VEGETACAO_ibfk_2` FOREIGN KEY (`ID_IMAGE_DATA`) REFERENCES `IMAGE_DATA` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela placa_km
DROP TABLE IF EXISTS `placa_km`;
CREATE TABLE `placa_km` (
	`id_placa_km` int NOT NULL AUTO_INCREMENT,
	`km` varchar(20) NOT NULL,
	`BR` varchar(20),
	`id` int NOT NULL,
	PRIMARY KEY (`id_placa_km`),
	KEY `plate_details_id` (`id`),
	CONSTRAINT `placa_km_fk` FOREIGN KEY (`id`) REFERENCES `plate_details` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- all_guardrail_matched
DROP TABLE IF EXISTS `all_guardrail_matched`;
CREATE TABLE `all_guardrail_matched` (
`id` int NOT NULL AUTO_INCREMENT,
`image_id` int DEFAULT NULL,
PRIMARY KEY (`id`),
CONSTRAINT `image_ibfk1` FOREIGN KEY (`image_id`) REFERENCES `IMAGE_DATA` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- guardrail_details
DROP TABLE IF EXISTS `guardrail_details`;
CREATE TABLE `guardrail_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_value` float DEFAULT NULL, 
  `class_name` varchar(30) DEFAULT NULL,
  `cam` int NOT NULL,
  `prob` float DEFAULT NULL,
  `x1` float DEFAULT NULL,
  `y1` float DEFAULT NULL,
  `x2` float DEFAULT NULL, 
  `y2` float DEFAULT NULL, 
  `image_id` int DEFAULT NULL,
  PRIMARY KEY (`id`,`cam`),
  CONSTRAINT `guardrail_details_ibfk1` FOREIGN KEY (`image_id`) REFERENCES `all_guardrail_matched` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
