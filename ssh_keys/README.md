# ssh_keys – SSH-Key Check

Überwacht, welche SSH-Keys in den `authorized_keys` eines Linux-Hosts
hinterlegt sind, und vergleicht sie mit einer Liste erlaubter Keys.

- **Checkmk:** ab 2.3.0p52, für 2.4 (APIs `cmk.agent_based.v2` und
  `cmk.rulesets.v1`)
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
| CRIT | mindestens ein Key ist nicht erlaubt (Details nennen die Keys) |
| UNKNOWN | Benutzer fehlt in der Agent-Ausgabe |

Verglichen wird exakt der Teil `<typ> <base64>` eines Keys; Optionen
(`command="…"`, `no-pty`, …) und Kommentar werden ignoriert. Erkannt werden
alle Key-Typen (`ssh-*`, `ecdsa-sha2-*`, `sk-*`). Leer- und
Kommentarzeilen in `authorized_keys` werden übersprungen, sonstige Zeilen
ohne erkennbaren Key gelten als nicht erlaubt.

## Dateien

| Datei | Zweck |
|---|---|
| `cmk_addons_plugins/ssh_keys/agent_based/ssh_keys.py` | Check-Plugin (Section, Discovery, Check) |
| `cmk_addons_plugins/ssh_keys/rulesets/ssh_keys.py` | Regelsatz „SSH-Keys“ |
| `agents/custom/sshkeys/lib/plugins/sshkeys` | Agent-Plugin (Bash) |

Die Plugins landen auf der Site unter
`~/local/lib/python3/cmk_addons/plugins/ssh_keys/`.

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

## Upgrade von 1.x

- Section, Check, Regelsatz und Service-Namen sind unverändert: keine neue
  Service-Erkennung nötig, bestehende Regeln bleiben erhalten.
- Gespeicherte Regeln (bisher `(Key, Label)`-Tupel) werden automatisch
  migriert, sobald sie in der GUI gespeichert werden oder
  `cmk-update-config` läuft. Bis dahin versteht der Check beide Formate.
- Wird 2.0.0 per MKP über 1.0.0 installiert, entfernt Checkmk die alten
  Dateien selbst. Wurden sie dagegen von Hand nach `local/` kopiert, müssen
  sie gelöscht werden, sonst ist der Regelsatz doppelt registriert:

  ```bash
  rm ~/local/lib/check_mk/base/plugins/agent_based/ssh_keys.py \
     ~/local/share/check_mk/checks/ssh_keys.py \
     ~/local/share/check_mk/web/plugins/wato/sshkeys_parameters.py
  ```

- **Verhaltensänderung:** ECDSA-/FIDO-Keys (`ecdsa-sha2-*`, `sk-*`) sowie
  Kommentar- und Leerzeilen galten in 1.x fälschlich immer als erlaubt, und
  verglichen wurde nur per Teilstring. Nicht freigegebene Keys dieser Typen
  werden jetzt CRIT.
