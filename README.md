# Mesh Agent Installer Page

Kleine Web-App fuer MeshCentral: Eine Person gibt einen Code ein und bekommt danach genau den passenden Agent-Download plus eine kurze Anleitung.

Gedacht fuer eine Subdomain wie `install.example.com`, damit Familie oder Kunden ohne technisches Wissen den MeshCentral-Agent installieren koennen.

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
docker compose up -d
```

Die Seite laeuft danach auf `http://SERVER-IP:5055`.

Der Admin-Bereich ist auf `http://SERVER-IP:5055/admin`.

Das normale `docker-compose.yml` nutzt ein fertiges Image:

```text
ghcr.io/jobbedeluxe/meshagentinstallerpage:latest
```

Dieses Image wird automatisch per GitHub Actions gebaut und in GitHub Container Registry veroeffentlicht.

Wenn du lokal selbst bauen willst, nutze stattdessen:

```bash
docker compose -f docker-compose.build.yml up -d --build
```

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

Mit Nginx Proxy Manager, Traefik oder Caddy leitest du `install.example.com` auf den Container weiter:

- Ziel-Host: IP deines Docker-Hosts
- Ziel-Port: `5055`
- SSL aktivieren
- Optional: HTTP nach HTTPS weiterleiten

Danach ist die Nutzerseite unter `https://install.example.com` erreichbar und der Admin unter `https://install.example.com/admin`.

## Installation auf OpenMediaVault

In OMV musst du kein Dockerfile einfuegen. Ein Dockerfile beschreibt nur, wie ein Image gebaut wird. OMV soll aber am besten ein fertiges Image starten. Dafuer nutzt du eine Compose-Datei mit `image: ghcr.io/jobbedeluxe/meshagentinstallerpage:latest`.

Wenn OMV beim ersten Start `unauthorized` oder `pull access denied` meldet, ist das Container-Paket in GitHub noch nicht oeffentlich sichtbar. Dann in GitHub beim Package `meshagentinstallerpage` die Visibility auf `Public` stellen oder kurz warten, bis der erste GitHub-Actions-Build fertig ist.

### Voraussetzungen

- Docker ist auf OMV installiert.
- Das OMV-Compose-Plugin ist installiert.
- Optional, aber praktisch: Nginx Proxy Manager oder ein anderer Reverse Proxy fuer `install.example.com`.

Wenn du Docker ueber OMV-Extras nutzt, findest du die Compose-Verwaltung normalerweise unter `Services > Compose`. Die Compose-Dateien werden dort ueber den Tab `Files` verwaltet.

### 1. Datenordner anlegen

Lege auf OMV einen Ordner fuer die Codes an, z. B.:

```bash
/srv/appdata/meshagentinstallerpage/data
```

Du kannst auch einen Ordner auf deiner Datenplatte nehmen. Wichtig ist nur, dass der Pfad im Compose-File unten dazu passt.

### 2. Compose-Datei in OMV einfuegen

In OMV:

1. `Services > Compose > Files` oeffnen.
2. `Add` anklicken.
3. Name z. B. `mesh-agent-installer`.
4. Diese Compose-Datei einfuegen:

```yaml
services:
  mesh-installer:
    image: ghcr.io/jobbedeluxe/meshagentinstallerpage:latest
    container_name: mesh-installer
    restart: unless-stopped
    ports:
      - "5055:5055"
    environment:
      ADMIN_PASSWORD: "HIER-EIN-LANGES-PASSWORT"
      SECRET_KEY: "HIER-EIN-LANGER-ZUFAELLIGER-WERT"
      CODES_FILE: /data/codes.json
    volumes:
      - /srv/appdata/meshagentinstallerpage/data:/data
```

Passe diese Werte an:

- `ADMIN_PASSWORD`: Passwort fuer `/admin`
- `SECRET_KEY`: langer Zufallswert fuer Sessions
- `/srv/appdata/meshagentinstallerpage/data`: dein echter OMV-Pfad fuer persistente Codes

Einen Secret-Key kannst du z. B. auf deinem PC oder per SSH auf OMV erzeugen:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Container starten

In OMV bei der Compose-Datei:

- `Save`
- danach `Up`

Oder per SSH im passenden Compose-Ordner:

```bash
docker compose up -d
```

### 4. Testen

```bash
curl http://127.0.0.1:5055/healthz
```

Wenn alles passt, ist die Seite im LAN erreichbar unter:

```text
http://DEINE-OMV-IP:5055
```

Admin:

```text
http://DEINE-OMV-IP:5055/admin
```

### Alternative: Repo auf OMV klonen

Wenn du lieber mit SSH arbeitest, kannst du auch das Repository klonen:

```bash
ssh root@DEINE-OMV-IP
mkdir -p /srv/appdata
cd /srv/appdata
git clone https://github.com/JobbeDeluxe/meshagentinstallerpage.git
cd meshagentinstallerpage
cp .env.example .env
nano .env
docker compose up -d
```

Das ist nicht zwingend noetig, weil OMV das fertige Image direkt ziehen kann.

### Image manuell aktualisieren

Wenn eine neue Version verfuegbar ist:

```bash
docker compose pull
docker compose up -d
```

In OMV kannst du dafuer bei der Compose-Datei ebenfalls `Pull` und danach `Up` nutzen.

### 5. Subdomain in Nginx Proxy Manager

Wenn du Nginx Proxy Manager nutzt:

1. `Proxy Hosts` oeffnen.
2. `Add Proxy Host`.
3. Domain Names: `install.example.com`.
4. Scheme: `http`.
5. Forward Hostname / IP: IP deines OMV-Servers.
6. Forward Port: `5055`.
7. `Block Common Exploits` aktivieren.
8. Unter `SSL` ein Let's-Encrypt-Zertifikat anfordern.
9. `Force SSL` aktivieren.
10. Speichern.

Danach:

```text
https://install.example.com
```

### 6. Codes anlegen

Oeffne:

```text
https://install.example.com/admin
```

Dann mit deinem `ADMIN_PASSWORD` einloggen und neue Codes mit MeshCentral-Download-Link anlegen.

Die Codes bleiben erhalten, weil sie im gemounteten `data`-Ordner liegen.

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
