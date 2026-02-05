CREATE DATABASE Airbnb_DW;
GO
USE Airbnb_DW;
GO

CREATE TABLE Dim_Location (
    location_id BIGINT PRIMARY KEY,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT
);

CREATE TABLE Dim_Host (
    host_id BIGINT PRIMARY KEY,
    host_is_superhost BIT
);

CREATE TABLE Dim_Room_Type (
    room_type_id BIGINT PRIMARY KEY,
    room_type VARCHAR(50),
    room_shared BIT,
    room_private BIT
);

CREATE TABLE Dim_Amenities (
    amenity_id BIGINT PRIMARY KEY,
    wifi BIT,
    kitchen BIT,
    air_conditioning BIT,
    parking BIT,
    tv BIT,
    heating BIT
);

CREATE TABLE Dim_Day (
    day_id BIGINT PRIMARY KEY,
    day_type VARCHAR(50),
    is_weekend BIT,
    biz BIT,
    multi BIT
);

CREATE TABLE Fact_Listings (
    listing_id BIGINT PRIMARY KEY,
    location_id BIGINT NOT NULL,
    host_id BIGINT NOT NULL,
    room_type_id BIGINT NOT NULL,
    amenity_id BIGINT NOT NULL,
    day_id BIGINT NOT NULL,

    realSum FLOAT,
    person_capacity INT,
    bedrooms INT,
    beds INT,
    cleanliness_rating FLOAT,
    guest_satisfaction_overall FLOAT,
    dist FLOAT,
    metro_dist FLOAT,
    attr_index FLOAT,
    attr_index_norm FLOAT,
    rest_index FLOAT,
    rest_index_norm FLOAT,

    CONSTRAINT FK_Location FOREIGN KEY (location_id) REFERENCES Dim_Location(location_id),
    CONSTRAINT FK_Host FOREIGN KEY (host_id) REFERENCES Dim_Host(host_id),
    CONSTRAINT FK_Room FOREIGN KEY (room_type_id) REFERENCES Dim_Room_Type(room_type_id),
    CONSTRAINT FK_Amen FOREIGN KEY (amenity_id) REFERENCES Dim_Amenities(amenity_id),
    CONSTRAINT FK_Day FOREIGN KEY (day_id) REFERENCES Dim_Day(day_id)
);

CREATE TABLE Raw_Data (
    listing_id BIGINT,
    realSum FLOAT,
    room_type VARCHAR(50),
    room_shared BIT,
    room_private BIT,
    person_capacity INT,
    host_is_superhost BIT,
    multi BIT,
    biz BIT,
    cleanliness_rating FLOAT,
    guest_satisfaction_overall FLOAT,
    bedrooms INT,
    dist FLOAT,
    metro_dist FLOAT,
    attr_index FLOAT,
    attr_index_norm FLOAT,
    rest_index FLOAT,
    rest_index_norm FLOAT,
    longitude FLOAT,
    latitude FLOAT,
    city VARCHAR(100),
    country VARCHAR(100),
    day_type VARCHAR(50),
    is_weekend BIT,
    beds INT,
    wifi BIT,
    kitchen BIT,
    air_conditioning BIT,
    parking BIT,
    tv BIT,
    heating BIT,
    location_id BIGINT,
    host_id BIGINT,
    room_type_id BIGINT,
    amenity_id BIGINT,
    day_id BIGINT
);

ALTER TABLE Raw_Data
ALTER COLUMN longitude FLOAT;

ALTER TABLE Raw_Data
ALTER COLUMN latitude FLOAT;

-- NOTE: Replace the path below with your local absolute path to schema/final_raw_with_ids.csv
-- Example: 'C:\Users\YourName\airbnb-analytics\schema\final_raw_with_ids.csv'
BULK INSERT Raw_Data
FROM 'YOUR_LOCAL_PATH\schema\final_raw_with_ids.csv'
WITH (
    FORMAT='CSV',
    FIRSTROW=2,
    FIELDTERMINATOR=',',
    ROWTERMINATOR='\r\n'
);


USE Airbnb_DW;
DROP TABLE Raw_Data;


INSERT INTO Dim_Location
SELECT DISTINCT location_id, city, country, latitude, longitude
FROM Raw_Data;

INSERT INTO Dim_Host
SELECT DISTINCT host_id, host_is_superhost
FROM Raw_Data;

INSERT INTO Dim_Room_Type
SELECT DISTINCT room_type_id, room_type, room_shared, room_private
FROM Raw_Data;

INSERT INTO Dim_Amenities
SELECT DISTINCT amenity_id, wifi, kitchen, air_conditioning, parking, tv, heating
FROM Raw_Data;

INSERT INTO Dim_Day
SELECT DISTINCT day_id, day_type, is_weekend, biz, multi
FROM Raw_Data;
