# CheckMK_Plugins

Sammlung eigener Checkmk-Erweiterungen. Aus jedem Plugin-Ordner wird ein
Erweiterungspaket (`.mkp`) gebaut – lokal per Skript oder automatisch per
GitHub Actions.

## Pakete

| Paket | Beschreibung | Checkmk |
|---|---|---|
| [ssh_keys](ssh_keys/) | Prüft `authorized_keys` gegen eine Liste erlaubter SSH-Keys | 2.3.0p52 – 2.4.0 |

## Aufbau

```
.
├── .github/workflows/build.yml   CI: Lint, Build, Release
├── tools/build_mkp.py            MKP-Builder (nur Python-Stdlib)
└── <paket>/
    ├── package.json              Metadaten (Name, Version, Checkmk-Versionen)
    ├── README.md
    ├── agent_based/              → ~/local/lib/check_mk/base/plugins/agent_based/
    ├── agents/                   → ~/local/share/check_mk/agents/
    ├── checks/                   → ~/local/share/check_mk/checks/
    └── web/                      → ~/local/share/check_mk/web/
```

Jeder Ordner auf oberster Ebene mit einer `package.json` ist ein Paket. Die
Unterordner entsprechen den Paket-„Parts“ von Checkmk (`agent_based`, `agents`,
`checks`, `web`, `lib`, `checkman`, `cmk_addons_plugins`, …) und landen 1:1
im MKP. Die Dateiliste (`files`) wird beim Build automatisch erzeugt.

`package.json`:

```json
{
  "title": "SSH-Key Check",
  "name": "ssh_keys",
  "description": "…",
  "version": "1.0.0",
  "version.packaged": "2.3.0p52",
  "version.min_required": "2.3.0p52",
  "version.usable_until": "2.4.0",
  "author": "…",
  "download_url": "https://github.com/DarkSilent/CheckMK_Plugins"
}
```

`name` muss dem Ordnernamen entsprechen.

## Lokal bauen

```bash
python3 tools/build_mkp.py            # alle Pakete nach dist/
python3 tools/build_mkp.py ssh_keys   # nur ein Paket
python3 tools/build_mkp.py --list     # Pakete und Versionen anzeigen
```

Für reproduzierbare Builds kann `SOURCE_DATE_EPOCH` gesetzt werden (die CI
nutzt den Zeitstempel des letzten Commits).

## CI / Releases

- **Push auf `main`, Pull Requests, manuell:** Lint (`py_compile`,
  `shellcheck`) und Build aller Pakete. Die `.mkp`-Dateien hängen als
  Artifact `mkp-packages` am Workflow-Lauf.
- **Release:** Version in `<paket>/package.json` erhöhen, committen und einen
  Tag `<paket>-v<version>` pushen:

  ```bash
  git tag ssh_keys-v1.0.0
  git push origin ssh_keys-v1.0.0
  ```

  Der Workflow prüft, dass Tag und `package.json` übereinstimmen, baut nur
  dieses Paket und legt ein GitHub-Release mit der `.mkp` an.

## Installation in Checkmk

GUI: *Setup → Maintenance → Extension packages → Upload package*, danach
aktivieren. Oder auf der Kommandozeile als Site-User:

```bash
mkp add ssh_keys-1.0.0.mkp
mkp enable ssh_keys 1.0.0
```
