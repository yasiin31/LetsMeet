-- Tabelle für Cities --
CREATE TABLE CITY
(
    city_id  SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    zip_code VARCHAR(10)  NOT NULL
);

-- Tabelle für Hobbys --
CREATE TABLE HOBBY
(
    hobby_id SERIAL PRIMARY KEY,
    name     VARCHAR(50) NOT NULL UNIQUE
);

-- Tabelle für User --
CREATE TABLE "USER"
(
    user_id       SERIAL PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    phone_number  VARCHAR(20),
    birth_date    DATE         NOT NULL,
    gender        VARCHAR(30),
    interested_in VARCHAR(30),
    city_id       INT,

    CONSTRAINT fk_city
        FOREIGN KEY (city_id)
            REFERENCES CITY (city_id)
            ON DELETE SET NULL
);

-- n:m Beziehung zwischen User und Hobby --
CREATE TABLE USER_HOBBY
(
    user_id  INT REFERENCES "USER" (user_id) ON DELETE CASCADE,
    hobby_id INT REFERENCES HOBBY (hobby_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, hobby_id)
);

-- Tabelle für Likes --
CREATE TABLE LIKES
(
    like_id    SERIAL PRIMARY KEY,
    liker_id   INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    liked_id   INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Nachrichten --
CREATE TABLE MESSAGE
(
    message_id  SERIAL PRIMARY KEY,
    sender_id   INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    receiver_id INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    content     TEXT      NOT NULL,
    sent_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- n:m Beziehung zwischen User und User --
CREATE TABLE FRIENDSHIP
(
    user_one_id INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    user_two_id INT       NOT NULL REFERENCES "USER" (user_id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_one_id, user_two_id)
);