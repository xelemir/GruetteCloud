# Anleitung für Entwickler

## Docker Installieren
1. Gehe auf die Docker-Website: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Klicke auf "Get Docker". Dies sollte die Installation für macOS starten.
3. Öffne die heruntergeladene Datei und folge den Anweisungen auf dem Bildschirm, um Docker zu installieren.
4. Nach der Installation, starte Docker Desktop durch Suche in deinen Anwendungen und klicken auf das Docker Desktop Symbol.

## Docker Container mit Docker Compose starten
Nun, da du Docker und Docker Compose installiert hast, kannst du beginnen, deine Docker Container zu starten. 

1. Öffne ein Terminalfenster.
2. Navigiere zu dem Verzeichnis, das deine `docker-compose.yml` Datei enthält.
3. Sobald du dich im richtigen Verzeichnis befindest, starte deine Docker Container mit dem Befehl `docker-compose up`.

Jetzt laufen deine Docker Container und dein Host sollte unter `http://localhost` erreichbar sein.
