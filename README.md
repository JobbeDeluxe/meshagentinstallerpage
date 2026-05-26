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

## Installation auf OpenMediaVault

Der einfachste Weg auf OMV ist per SSH mit Docker Compose. Die OMV-Compose-Oberflaeche kann Container verwalten, aber fuer diese App ist ein Git-Checkout auf dem Server praktischer, weil der Container lokal aus `Dockerfile`, `app.py` und den Templates gebaut wird.

### Voraussetzungen

- Docker ist auf OMV installiert.
- Docker Compose funktioniert mit `docker compose version`.
- SSH ist in OMV aktiviert.
- Optional, aber praktisch: Nginx Proxy Manager oder ein anderer Reverse Proxy fuer `install.unlimited8.de`.

Wenn du Docker ueber OMV-Extras nutzt, findest du die Compose-Verwaltung normalerweise unter `Services > Compose`. Die Compose-Dateien werden dort ueber den Tab `Files` verwaltet.

### 1. Per SSH auf OMV verbinden

```bash
ssh root@DEINE-OMV-IP
```

Falls du dich nicht als `root` einloggst, setze vor Docker-Befehle ggf. `sudo`.

### 2. Zielordner anlegen

Nimm am besten einen Ordner auf deiner Datenplatte, nicht auf dem kleinen OMV-Systemlaufwerk. Beispiel:

```bash
mkdir -p /srv/appdata
cd /srv/appdata
```

Wenn du bereits einen Appdata-Ordner hast, nimm diesen stattdessen.

### 3. Repo klonen

```bash
git clone https://github.com/JobbeDeluxe/meshagentinstallerpage.git
cd meshagentinstallerpage
```

Falls `git` fehlt:

```bash
apt update
apt install -y git
```

### 4. `.env` anlegen

```bash
cp .env.example .env
nano .env
```

Inhalt anpassen:

```env
ADMIN_PASSWORD=hier-ein-langes-admin-passwort
SECRET_KEY=hier-einen-langen-zufaelligen-wert-eintragen
```

Einen Secret-Key kannst du auf OMV so erzeugen:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Container starten

```bash
docker compose up -d --build
```

Danach testen:

```bash
docker compose ps
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

### 6. Subdomain in Nginx Proxy Manager

Wenn du Nginx Proxy Manager nutzt:

1. `Proxy Hosts` oeffnen.
2. `Add Proxy Host`.
3. Domain Names: `install.unlimited8.de`.
4. Scheme: `http`.
5. Forward Hostname / IP: IP deines OMV-Servers.
6. Forward Port: `5055`.
7. `Block Common Exploits` aktivieren.
8. Unter `SSL` ein Let's-Encrypt-Zertifikat anfordern.
9. `Force SSL` aktivieren.
10. Speichern.

Danach:

```text
https://install.unlimited8.de
```

### 7. Codes anlegen

Oeffne:

```text
https://install.unlimited8.de/admin
```

Dann mit deinem `ADMIN_PASSWORD` einloggen und neue Codes mit MeshCentral-Download-Link anlegen.

### Updates

Wenn spaeter eine neue Version im GitHub-Repo liegt:

```bash
cd /srv/appdata/meshagentinstallerpage
git pull
docker compose up -d --build
```

Die Codes bleiben erhalten, weil sie im lokalen Ordner `data/` liegen.

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
