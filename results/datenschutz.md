# Datenschutzdokumentation

## 1. Rechtsgrundlage der Datenverarbeitung
Die Verarbeitung erfolgt nach Art. 6 DSGVO:
- **Einwilligung (Art. 6 Abs. 1 lit. a)** – für freiwillige Angaben wie Hobbys, Geschlecht, Interessensangaben.
- **Vertragserfüllung (Art. 6 Abs. 1 lit. b)** – für Kontaktdaten (Name, E-Mail, Telefon), die zur Nutzung der Plattform erforderlich sind.
- **Berechtigtes Interesse (Art. 6 Abs. 1 lit. f)** – für technische Daten und Auswertungen zur Verbesserung der Plattform.

**Besondere Kategorien (Art. 9 DSGVO):**
- Geschlecht / sexuelle Orientierung („Interessiert an Geschlecht“) → nur mit ausdrücklicher Einwilligung zulässig.
- Freitextnachrichten (können sensible Inhalte enthalten) → besonders zu schützen.

---

## 2. Klassifikation der Datenarten

| Datenquelle | Datenart | Personenbezug | Kategorie | Schutzbedarf |
|-------------|----------|---------------|-----------|--------------|
| **Excel (let_s-meet-db-dump.xlsx)** | Name, Adresse, Telefon, E-Mail | Ja | Stammdaten | 🟢 normal |
| | Hobbys mit Priorisierung | Ja | Profildaten | 🟢 normal |
| | Geburtsdatum | Ja | Identifikationsdaten | 🟡 erhöht |
| | Geschlecht | Ja | Sensible Daten | 🔴 hoch |
| | „Interessiert an Geschlecht“ | Ja | Sexuelle Orientierung (Art. 9) | 🔴 hoch |
| **MongoDB (users)** | Name, Telefon, E-Mail | Ja | Stammdaten | 🟢 normal |
| | Freunde, Likes | Ja | Soziale Beziehungen | 🟡 erhöht |
| | Nachrichten (Freitext) | Ja | Kommunikationsdaten, potenziell besonders sensibel | 🔴 hoch |
| | Zeitstempel (createdAt, updatedAt) | Ja | Nutzungsdaten | 🟡 erhöht |
| **XML (Hobbys)** | Name, E-Mail | Ja | Stammdaten | 🟢 normal |
| | Hobbys | Ja | Profildaten | 🟢 normal |

Legende: 🟢 = normal, 🟡 = erhöht, 🔴 = hoch (Art. 9 DSGVO)

---

## 3. Schutzbedarf
- **Normal (🟢):** Stammdaten und Hobbys.
- **Erhöht (🟡):** Geburtsdaten, Zeitstempel, Kommunikationsverläufe.
- **Hoch (🔴):** Geschlecht, sexuelle Orientierung, Freitextnachrichten (potenziell Art. 9-Daten).

---

## 4. Technische und organisatorische Maßnahmen (TOMs)

### Technische Maßnahmen
- **Verschlüsselung:** Transport (TLS), Speicherung (AES-256).
- **Pseudonymisierung:** Analyse von Hobbys ohne direkte Zuordnung zu Personen.
- **Zugriffskontrolle:** Rollen- und Rechtemanagement, 2FA für Admins.
- **Protokollierung:** Logging aller Zugriffe, Monitoring von Anomalien.
- **Backups:** Regelmäßige verschlüsselte Backups mit Notfallwiederherstellung.

### Organisatorische Maßnahmen
- **Mitarbeiterschulung:** Sensibilisierung für Umgang mit sensiblen Daten.
- **Lösch- und Aufbewahrungskonzepte:** Datenminimierung nach Art. 5 DSGVO.
- **Datenschutz-Folgenabschätzung:** Pflicht wegen Art. 9-Daten.
- **Auftragsverarbeitung:** Verträge mit externen Dienstleistern prüfen und dokumentieren.

---

## 5. Zusammenfassung
- Das System verarbeitet **normale personenbezogene Daten**, aber auch **besondere Kategorien nach Art. 9 DSGVO**, Daraus ergibt sich ein **hoher Schutzbedarf**.
- Ohne Einwilligung dürfen Angaben zu Geschlecht, sexueller Orientierung und Inhalte von Nachrichten **nicht verarbeitet** werden.
- Maßnahmen gemäß Art. 32 DSGVO sind verpflichtend und müssen regelmäßig überprüft werden.  
