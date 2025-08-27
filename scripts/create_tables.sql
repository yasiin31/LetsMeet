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

-- Tabelle für User --
CREATE TABLE "USER" (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    birth_date DATE NOT NULL,
    gender VARCHAR(30),
    interested_in VARCHAR(30),
    city_id INT,

    CONSTRAINT fk_city
                    FOREIGN KEY(city_id)
                    REFERENCES CITY(city_id)
                    ON DELETE SET NULL
);