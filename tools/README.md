# Tools

## `asarq.py` — query an Electron `.asar` in memory

Electron apps ship their JavaScript inside a single `.asar` archive. Most guides tell you to unpack
it. For a 2,400-file archive where you need six files, that's the wrong move — it floods your disk,
breaks your line numbers against the original, and leaves artefacts lying around.

`asarq.py` parses the ASAR header and serves the files straight out of the archive. No unpacking,
no temp directory, line numbers that match what you cite in a report.

Pure standard library. Python 3.8+.

### Commands

```bash
# inventory — file count, total bytes, top-level directory breakdown
python3 asarq.py stats core.asar

# list paths, optionally filtered by substring
python3 asarq.py list core.asar
python3 asarq.py list core.asar discord_native
python3 asarq.py list core.asar | grep -v node_modules     # the useful one

# print a file with line numbers, optionally a range
python3 asarq.py cat core.asar app/mainScreen.js
python3 asarq.py cat core.asar app/mainScreen.js 335 560

# regex grep across .js/.json/.html/.ts, with path:line output
python3 asarq.py grep core.asar "contextIsolation|sandbox|nodeIntegration"
python3 asarq.py grep core.asar "ipcMain\.(on|handle)" app/          # scope to a subtree
python3 asarq.py grep core.asar "https?://" app/ node_modules        # scope + exclude
```

`grep` takes up to three positional arguments after the pattern: `<scope-substring>`
`<exclude-substring>`. Both match anywhere in the path.

### Finding the archive

```bash
ls /Applications/<App>.app/Contents/Resources/        # app.asar
ls ~/Library/Application\ Support/<app>/              # often the real payload
```

If the bundled `app.asar` is small, it's probably a launcher and the real shell is downloaded
elsewhere — that's exactly what Discord does. Chase it before you start reading.

### First four commands on any Electron app

```bash
python3 asarq.py stats core.asar
python3 asarq.py list  core.asar | grep -v node_modules
python3 asarq.py grep  core.asar "contextIsolation|sandbox|nodeIntegration|preload"
python3 asarq.py grep  core.asar "ipcMain\.(on|handle)"
```

That gives you the size of the real surface, the security posture of the window, and the full
privileged API in about thirty seconds.

### Counting IPC handlers

There's no subcommand for this — it's a few lines against the same index:

```python
import re
exec(open('asarq.py').read().split('def main()')[0])   # import Asar without running the CLI

a = Asar('core.asar')
pat = re.compile(r"(ipcMain\.(?:on|handle)|DiscordIPC\.main\.(?:on|handle))\s*\(\s*([^,]+?)\s*,")
for p in sorted(a.index):
    if not p.endswith('.js') or 'node_modules' in p:
        continue
    for i, line in enumerate(a.text(p).split('\n'), 1):
        m = pat.search(line)
        if m:
            print(f"{p}:{i}  {m.group(2)[:60]}")
```

Watch for the same channel registered twice in mutually exclusive branches — a raw count will
overstate the live surface.
