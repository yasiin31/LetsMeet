# Datenmigration & Datenbank-Design für Let's Meet GmbH

Dieses Repository dient der Analyse, dem Entwurf und der Migration der Bestandsdaten für die Dating-App der Let's Meet GmbH.

## 1. Hintergrund & Ausgangslage

Unsere Kundin, die Let’s Meet GmbH, hat uns mit der Weiterentwicklung ihrer Dating-App beauftragt. Nach einer problematischen Trennung vom vorherigen IT-Dienstleister besteht kein Zugriff mehr auf die produktiven Datenbanken. Die gesamte Datenbasis liegt uns in heterogener Form vor und muss in ein neues, robustes System überführt werden.

Die Kernaufgabe unseres Teams ist die Konzeption und Umsetzung der Datenmigration. Die eigentliche App-Entwicklung wird von einem separaten Team betreut.

## 2. Projektziele & Aufgaben unseres Teams

Die Kundin legt größten Wert auf eine saubere Konzeption und nachvollziehbare Dokumentation, um zukünftige Probleme zu vermeiden.

Unsere Hauptaufgaben sind:

1. **Datenanalyse:** Eingehende Analyse der bereitgestellten Datenquellen zur Identifizierung von Entitäten, Attributen und Beziehungen.
2. **Konzeptueller Entwurf:** Erstellung eines ausgefeilten konzeptuellen Datenmodells (z.B. als ER-Diagramm), das als Diskussionsgrundlage mit der Kundin dient.
3. **Logischer Entwurf:** Überführung des konzeptuellen Modells in ein logisches Datenmodell (relationales Schema).
4. **Datenbankimplementierung:** Erstellung des physischen Datenbankschemas in PostgreSQL mittels DDL-Skripten.
5. **Datenmigration:** Entwicklung von Skripten zum Import, zur Bereinigung und zur Transformation der Daten aus allen Quellen in die neue PostgreSQL-Datenbank.
6. **Dokumentation:** Lückenlose Dokumentation aller Entwurfsphasen und Zwischenschritte in Markdown-Dateien.

## 3. Datenquellen

Die zu migrierenden Daten stammen aus drei unterschiedlichen Quellen:

* **Excel-Datei (`.xlsx`):** Haupt-Dump der ehemaligen relationalen Datenbank. Enthält die Kern-Entitäten wie Nutzerprofile, Stammdaten etc.
* **MongoDB-Backup:** NoSQL-Datenbank-Export, der **Likes** und **Nachrichten** aus einer anderen App enthält.
* **XML-Datei (`.xml`):** Enthält strukturierte Daten zu den **Hobbys** der Nutzer.

## 4. Technologie-Stack & Zielsystem

* **Zieldatenbank:** PostgreSQL
* **Laufzeitumgebung:** Docker
* **Versionierung:** Git

Der PostgreSQL-Server wird über die `docker-compose.yml`-Datei in diesem Repository konfiguriert und bereitgestellt.

## 5. Entity Relationship Model

![ERM Picture](./images/letsmeetErm.png)

## 6. Entity Relationship Diagram

```mermaid
erDiagram
    USER {
        int user_id PK
        string first_name
        string last_name
        string email UK "Eindeutige E-Mail"
        string phone_number
        date birth_date
        string gender
        string interested_in
        int city_id FK
    }

    CITY {
        int city_id PK
        string name
        string zip_code
    }

    HOBBY {
        int hobby_id PK
        string name UK "Eindeutiges Hobby"
    }

    USER_HOBBY {
        int user_id PK, FK
        int hobby_id PK, FK
    }

    FRIENDSHIP {
        int user_one_id PK, FK
        int user_two_id PK, FK
        datetime created_at
    }

    "LIKE" {
        int like_id PK
        int liker_id FK "Wer hat geliked?"
        int liked_id FK "Wer wurde geliked?"
        datetime created_at
    }

    MESSAGE {
        int message_id PK
        int sender_id FK
        int receiver_id FK
        text content
        datetime sent_at
    }

    USER ||--|{ CITY : "lebt in"
    USER ||--o{ USER_HOBBY : "hat"
    HOBBY ||--o{ USER_HOBBY : "wird ausgeübt von"
  
    USER }o--o{ FRIENDSHIP : "ist befreundet mit"
  
    USER }o--o{ "LIKE" : "gibt"
    USER }o--o{ "LIKE" : "erhält"

    USER }o--o{ MESSAGE : "sendet"
    USER }o--o{ MESSAGE : "empfängt"
```
