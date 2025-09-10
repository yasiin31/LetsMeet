SELECT COUNT(*) AS anzahl_user FROM "USER";
SELECT COUNT(*) AS anzahl_cities FROM city;
SELECT COUNT(*) AS anzahl_hobbies FROM hobby;
SELECT COUNT(*) AS anzahl_user_hobby_verknuepfungen FROM user_hobby;
SELECT COUNT(*) AS anzahl_likes FROM likes;
SELECT COUNT(*) AS anzahl_messages FROM message;
SELECT COUNT(*) AS anzahl_friendships FROM friendship;

SELECT
    user_id,
    first_name,
    last_name,
    email,
    phone_number,
    birth_date,
    gender,
    interested_in
FROM
    "USER"
WHERE
    email = 'martin.forster@web.ork';

SELECT * FROM city WHERE name = 'Dorsten' AND zip_code = '46286';

SELECT name FROM hobby
WHERE name IN (
               'Fremdsprachenkenntnisse erweitern',
               'Im Wasser waten',
               'Schwierige Probleme klären',
               'Morgens Früh aufstehen'
    );

SELECT
    u.first_name,
    u.last_name,
    c.name AS city_name,
    c.zip_code
FROM
    "USER" u
        JOIN
    city c ON u.city_id = c.city_id
WHERE
    u.email = 'martin.forster@web.ork';

SELECT
    COUNT(h.hobby_id) AS anzahl_hobbies_fuer_martin
FROM
    "USER" u
        JOIN
    user_hobby uh ON u.user_id = uh.user_id
        JOIN
    hobby h ON uh.hobby_id = h.hobby_id
WHERE
    u.email = 'martin.forster@web.ork';

SELECT
    h.name AS hobby_name
FROM
    "USER" u
        JOIN
    user_hobby uh ON u.user_id = uh.user_id
        JOIN
    hobby h ON uh.hobby_id = h.hobby_id
WHERE
    u.email = 'martin.forster@web.ork'
ORDER BY
    h.name;