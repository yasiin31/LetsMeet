-- Tabelle für Cities --
CREATE TABLE CITY (
    city_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    zip_code VARCHAR(10) NOT NULL
);

-- Tabelle für Hobbys --
CREATE TABLE HOBBY (
    hobby_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);