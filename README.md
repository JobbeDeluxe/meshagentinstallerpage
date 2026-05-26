# Mesh Agent Installer Page

Kleine Web-App fuer MeshCentral: Eine Person gibt einen Code ein und bekommt danach genau den passenden Agent-Download plus eine kurze Anleitung.

Gedacht fuer eine Subdomain wie `install.unlimited8.de`, damit Familie oder Kunden ohne technisches Wissen den MeshCentral-Agent installieren koennen.

## Funktionen

- Einfache Startseite mit Code-Eingabe
- Download-Link erscheint erst nach gueltigem Code
- Admin-Bereich unter `/admin`
- Codes per Weboberflaeche anlegen und loeschen
- Codes werden als JSON in einem Docker-Volume gespeichert
- Kein Datenbankserver noetig

## Schnellstart mit Docker Compose

1. `.env.example` nach `.env` kopieren.
2. `ADMIN_PASSWORD` in `.env` setzen.
3. `SECRET_KEY` in `.env` durch einen langen Zufallswert ersetzen.
4. Container starten:

```bash
docker compose up -d --build
```

Die Seite laeuft danach auf `http://SERVER-IP:5055`.

Der Admin-Bereich ist auf `http://SERVER-IP:5055/admin`.

## Beispiel `.env`

```env
ADMIN_PASSWORD=ein-langes-passwort
SECRET_KEY=hier-einen-langen-zufaelligen-wert-eintragen
```

Einen Secret-Key kannst du z. B. so erzeugen:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Subdomain verbinden

Mit Nginx Proxy Manager, Traefik oder Caddy leitest du `install.unlimited8.de` auf den Container weiter:

- Ziel-Host: IP deines Docker-Hosts
- Ziel-Port: `5055`
- SSL aktivieren
- Optional: HTTP nach HTTPS weiterleiten

Danach ist die Nutzerseite unter `https://install.unlimited8.de` erreichbar und der Admin unter `https://install.unlimited8.de/admin`.

## MeshCentral Download-Link finden

1. MeshCentral oeffnen.
2. Geraetegruppe auswaehlen.
3. `Add Agent` bzw. `Agent hinzufuegen` oeffnen.
4. Windows-Agent auswaehlen.
5. Direkten Download-Link kopieren.
6. Im Admin-Bereich einen neuen Code mit Name und Download-Link speichern.

## Codes per Kommandozeile anlegen

Optional geht das auch ohne Browser:

```bash
python gen_code.py "Mamas Laptop" "https://mesh.example.de/meshagents?id=..."
```

Im Container nutzt die App standardmaessig `/data/codes.json`. Lokal nutzt sie `codes.json`, falls `CODES_FILE` nicht gesetzt ist.

## Daten sichern

Die produktiven Codes liegen im Ordner `data/` auf dem Host. Diesen Ordner kannst du sichern oder auf einen neuen Server kopieren.
