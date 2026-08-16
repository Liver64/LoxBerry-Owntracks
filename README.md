# OwnTracks for LoxBerry

[![LoxBerry Plugin](https://img.shields.io/badge/LoxBerry-Plugin-blue)](https://www.loxberry.de/)
[![Release v1.0.6](https://img.shields.io/badge/release-v1.0.6-blue)](https://github.com/Liver64/LoxBerry-Owntracks/releases/tag/v1.0.6)
[![GitHub issues](https://img.shields.io/github/issues/Liver64/LoxBerry-Owntracks)](https://github.com/Liver64/LoxBerry-Owntracks/issues)
[![License](https://img.shields.io/github/license/Liver64/LoxBerry-Owntracks)](https://github.com/Liver64/LoxBerry-Owntracks)

**OwnTracks for LoxBerry** verbindet die [OwnTracks](https://owntracks.org/)-App mit LoxBerry und ermöglicht die Nutzung von Positions- und Trackingdaten über MQTT.

Das Plugin übernimmt die Benutzerverwaltung, erzeugt benutzerspezifische OwnTracks-Konfigurationsdateien (`.otrc`) und integriert den offiziellen **OwnTracks Recorder (`ot-recorder`)** in LoxBerry.

---

## ✨ Funktionen

- 👤 Verwaltung mehrerer OwnTracks-Benutzer / DeviceIDs
- 📱 Erzeugung benutzerspezifischer `.otrc`-Konfigurationsdateien
- 📡 Nutzung der MQTT-Konfiguration von LoxBerry
- 🌍 Konfiguration von DynDNS/IP-Adresse und MQTT-Port
- 📍 Definition einer eigenen Lokation mit Breiten-/Längengrad und Radius
- 📶 Optionaler iBeacon-Support über UUID, Major und Minor
- ▶️ Aktivieren, Deaktivieren und Neustarten des Trackings
- 🗄️ Integration des offiziellen OwnTracks Recorders
- 🌐 Zugriff auf die Recorder-Weboberfläche
- 🔁 Unterstützung bei Migration und Plugin-Upgrades
- 🇩🇪 Deutsche und 🇬🇧 englische Benutzeroberfläche

---

## 🟢 Benutzerstatus

Der Status eines Benutzers wird direkt in der Benutzerliste über einen farbigen Punkt dargestellt.

| Status | Bedeutung |
|:---:|---|
| 🔴 | Keine App-Konfiguration vorhanden |
| 🟡 | App-Konfiguration vorhanden |
| 🟢 | Tracking-Daten vorhanden |

---

## 📋 Voraussetzungen

- LoxBerry
- eingerichteter MQTT-Broker bzw. MQTT-Dienst
- Internetzugang während der Installation
- OwnTracks-App auf dem Smartphone
- bei externer Nutzung eine geeignete Erreichbarkeit des MQTT-Brokers, z. B. über DynDNS, VPN oder Portweiterleitung

---

## 📦 Installation

1. Das aktuelle Release-ZIP unter **[Releases](https://github.com/Liver64/LoxBerry-Owntracks/releases)** herunterladen.
2. In der LoxBerry-Pluginverwaltung installieren.
3. Während der Installation wird der OwnTracks Recorder eingerichtet.
4. Anschließend das Plugin öffnen und konfigurieren.

> [!IMPORTANT]
> Das ZIP aus den GitHub-Releases ist das vollständige LoxBerry-Installationspaket.  
> Das Repository selbst sollte nicht als ZIP über **Code → Download ZIP** installiert werden.

---

## ⚙️ Erste Einrichtung

1. Prüfen, ob MQTT in LoxBerry korrekt eingerichtet ist.
2. Unter **IP-Konfiguration** die für die OwnTracks-App erreichbare Adresse und den MQTT-Port eintragen.
3. Lokation, Breiten-/Längengrad und Radius konfigurieren.
4. Einen oder mehrere Benutzer anlegen.
5. Optional UUID, Major und Minor für iBeacon hinterlegen.
6. Konfiguration speichern.
7. Die erzeugte `.otrc`-Datei auf das jeweilige Smartphone übertragen.
8. Die Datei mit OwnTracks öffnen/importieren.
9. Tracking im Plugin aktivieren.

Die erzeugten Benutzerkonfigurationen werden im Plugin-Datenverzeichnis abgelegt:

```text
data/plugins/owntracks4lox/user_config_files/
```

> [!WARNING]
> Die `.otrc`-Dateien können MQTT-Zugangsdaten enthalten.  
> Diese Dateien sollten daher nicht veröffentlicht oder ungeschützt weitergegeben werden.

---

## 🛰️ OwnTracks Recorder

Dieses Plugin verwendet den offiziellen **OwnTracks Recorder** als Backend zur Speicherung und Bereitstellung der Positionsdaten.

### Offizielles Projekt

**OwnTracks Recorder:**  
https://github.com/owntracks/recorder

Der Recorder ist ein eigenständiges Open-Source-Projekt des OwnTracks-Teams. Er empfängt OwnTracks-Daten, speichert sie lokal und stellt Schnittstellen zur weiteren Verarbeitung und Anzeige bereit.

> [!NOTE]
> **OwnTracks for LoxBerry** ist ein eigenständiges LoxBerry-Plugin und kein Bestandteil des offiziellen OwnTracks-Projekts.  
> Der `ot-recorder` wird vom OwnTracks-Team entwickelt und gepflegt.

---

## 🗂️ Recorder-Daten

Die aufgezeichneten Daten befinden sich standardmäßig unter:

```text
/var/spool/owntracks/recorder/store
```

Die Recorder-Konfiguration befindet sich typischerweise unter:

```text
/etc/default/ot-recorder
```

Bei einer Deinstallation des Plugins bleiben bereits aufgezeichnete Tracking-Daten erhalten, damit keine Historie unbeabsichtigt verloren geht.

---

## 🔧 Recorder prüfen

### Dienststatus

```bash
sudo systemctl status ot-recorder
```

### Letzte Logmeldungen

```bash
sudo journalctl -u ot-recorder -n 100 --no-pager
```

### Weboberfläche

Standardmäßig:

```text
http://<LOXBERRY-IP>:8083
```

---

## 🔄 Update / Upgrade

Bei einem Plugin-Upgrade werden vorhandene Benutzer- und Recorder-Konfigurationen erhalten und nach der Installation wiederhergestellt.

Persistente Benutzerdateien und erzeugte `.otrc`-Konfigurationen bleiben dabei erhalten.

---

## 🗑️ Deinstallation

Bei der Deinstallation werden die vom Plugin eingerichteten Komponenten des OwnTracks Recorders entfernt bzw. deaktiviert.

> [!CAUTION]
> Die bereits aufgezeichneten Positionsdaten im Recorder-Store werden bewusst **nicht automatisch gelöscht**.

Dadurch wird verhindert, dass eine Plugin-Deinstallation versehentlich die komplette Positionshistorie entfernt.

---

## 🐛 Fehler melden

Fehler, Probleme oder Verbesserungsvorschläge bitte über GitHub Issues melden:

**https://github.com/Liver64/LoxBerry-Owntracks/issues**

Wenn möglich, bitte folgende Informationen angeben:

- LoxBerry-Version
- Plugin-Version
- verwendete Architektur / Hardware
- relevante Logausgaben
- genaue Schritte zur Reproduktion

---

## 🔗 Links

| Projekt | Link |
|---|---|
| OwnTracks for LoxBerry | https://github.com/Liver64/LoxBerry-Owntracks |
| Releases | https://github.com/Liver64/LoxBerry-Owntracks/releases |
| Issues | https://github.com/Liver64/LoxBerry-Owntracks/issues |
| OwnTracks Recorder | https://github.com/owntracks/recorder |
| OwnTracks | https://owntracks.org/ |
| LoxBerry | https://www.loxberry.de/ |

---

## 👤 Autor

**Oliver Lewald**

---

## ℹ️ Hinweis

Dieses Repository stellt eine eigenständige Integration für LoxBerry bereit.

**OwnTracks**, **OwnTracks Recorder** und die zugehörigen Komponenten sind eigenständige Projekte des OwnTracks-Teams.
