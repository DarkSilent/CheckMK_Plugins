# ssh_keys – SSH-Key Check

Überwacht, welche SSH-Keys in den `authorized_keys` eines Linux-Hosts
hinterlegt sind, und vergleicht sie mit einer Liste erlaubter Keys.

- **Checkmk:** 2.3.0p52 bis 2.4.0
- **Service:** `SSH-Keys <Benutzer>` (einer pro Benutzer)

## Funktionsweise

Das Agent-Plugin `sshkeys` gibt die Sektion `<<<ssh_keys>>>` aus: eine Zeile
für `root` sowie für jeden Benutzer mit UID ≥ 1000 und existierendem
Home-Verzeichnis, jeweils mit den Keys aus `~/.ssh/authorized_keys`
(mehrere Keys durch `;` getrennt).

Der Check bewertet pro Benutzer:

| Zustand | Bedingung |
|---|---|
| OK | keine Keys hinterlegt |
| OK | alle Keys sind in der Regel erlaubt (Ausgabe der Labels) |
| WARN | Keys vorhanden, aber keine Regel konfiguriert |
| CRIT | mindestens ein Key ist nicht erlaubt |

Verglichen wird der Teil `ssh-<typ> <base64>` eines Keys; Optionen und
Kommentar werden ignoriert.

## Dateien

| Datei | Zweck |
|---|---|
| `agent_based/ssh_keys.py` | Check-Plugin (Discovery + Check) |
| `agents/custom/sshkeys/lib/plugins/sshkeys` | Agent-Plugin (Bash) |
| `checks/ssh_keys.py` | Legacy-Registrierung `special_agent_info` |
| `web/plugins/wato/sshkeys_parameters.py` | Regelsatz „SSH-Keys“ |

## Einrichtung

1. Paket installieren und aktivieren (siehe [Haupt-README](../README.md)).
2. Agent-Plugin verteilen: Das Plugin liegt als Custom-Datei unter
   `agents/custom/sshkeys/`. Mit der Agent Bakery über
   *Deploy custom files with agent* → `sshkeys` ausrollen, oder die Datei
   manuell nach `/usr/lib/check_mk_agent/plugins/sshkeys` kopieren
   (ausführbar, läuft als root).
3. Erlaubte Keys festlegen: *Setup → Services → Service monitoring rules →
   SSH-Keys*. Pro Eintrag Key (`ssh-ed25519 AAAA…`) und Label angeben,
   optional auf einzelne Benutzer (Item) einschränken.
4. Service-Erkennung auf den Hosts ausführen.
