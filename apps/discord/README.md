# Discord Desktop — Teardown

**Target** Discord.app · host `1.0.9208` · core module `0.0.380` · macOS arm64
**Method** static analysis only — no runtime instrumentation, no network capture
**Report** [Discord-Desktop-Teardown.pdf](Discord-Desktop-Teardown.pdf) — 35 pages
**Findings** [findings.md](findings.md)

---

## The one-line version

Discord desktop is a **hardened browser window pointed at discord.com**. It ships almost no product
logic of its own — what it ships is a carefully fenced set of operating-system capabilities that
the website is allowed to reach through one named bridge.

## Nine things worth knowing

**1 · The UI is remote.** The main window loads `https://discord.com/app` over the network
(`app/mainScreen.js:72,108,109`). Chat, voice UI, servers, settings — none of it is in either
shipped archive.

**2 · Two archives, two tiers.** The `app.asar` inside `/Applications/Discord.app` is only a
*launcher* — 39 source files: splash screen, updater, connectivity tests. The real shell is
`core.asar`, downloaded separately into `~/Library/Application Support/discord/0.0.380/`. Discord
therefore updates itself without ever asking for an admin password, and the code that actually runs
lives in a user-writable directory.

**3 · The bridge is one object with 30 keys.** `contextBridge.exposeInMainWorld('DiscordNative', …)`
at `app/mainScreenPreload.js:68`, assembled from 26 distinct capability modules — filesystem,
clipboard, screen capture, keychain, power, native-module installation, WebAuthn, and more.

**4 · 136 privileged IPC endpoints** are registered in the main process, drawn from a canonical
enum of **144** channel names in `@discordapp/discord-native-types/IPCEvents.js`.

**5 · Two real allow-lists exist** — `renderer/ipc.js:9-10` restricts the generic IPC facade to 25
sendable and 13 invokable channels and throws `'cannot send this event'` otherwise. A genuine,
well-built control. It's also *narrower than the attack surface*, because the typed capability
modules bypass that facade entirely.

**6 · Context isolation is on; the sandbox is off.** `contextIsolation:true`,
`nodeIntegration:false`, but `sandbox:false` (`app/mainScreen.js:352-356`). The preload therefore
holds full Node — `renderer/fileManager.js` does real `fs` I/O and `clipboard.read()` never crosses
IPC at all. This single flag defines the client's entire security posture.

**7 · Permissions are deny-by-default** with real origin checks (`mainScreen.js:388-428`), and
off-origin navigation is blocked (`:526-530`) — except during a Google OAuth flow, where the
restriction is deliberately and completely lifted.

**8 · Module updates carry no JavaScript-level signature check.** The legacy path trusts HTTP 200
and TLS (`common/moduleUpdater.js:572-605`), then extracts with `yauzl` and later `require()`s the
result as native code. On macOS the legacy path is the default.

**9 · Crash reports from modded clients are filtered out.** `common/crashReporterSetup.js:70-71`
ignores errors mentioning BetterDiscord and VencordPatcher and denies the `betterdiscord://`
scheme. Also: crash sampling is 1% on stable Windows but **100% on macOS and Linux**.

---

## Two corrections worth their own section

Both are cases where the obvious reading was wrong, and checking changed the answer.

### `riotGames` is not a partnership

A dedicated `riotGames` member on the bridge plus a bundled `riotgames.pem` looks like evidence of
a commercial deal. It isn't. `renderer/riotGames.js:8` does a plain GET against
`https://127.0.0.1:2999/liveclientdata/` — Riot's **publicly documented Live Client Data API**,
served by the League client on your own machine with a self-signed certificate. The bundled PEM
exists because that cert isn't in any public trust store, so it has to be pinned explicitly. That's
how Rich Presence knows what you're playing. No business relationship required, and none evidenced.

### Zip-slip is present in shape, absent in effect

`common/moduleUpdater.js:728` joins archive-controlled entry names onto a destination directory
with no sanitisation — the textbook zip-slip pattern, and an automated scanner will flag it. It's
safe anyway, because the bundled `yauzl` rejects `..` segments, absolute paths and backslashes in
`validateFileName` (`yauzl/index.js:608-619`) before emitting any entry.

The outcome is correct today and fragile tomorrow: the guarantee lives in a dependency, not in
Discord's code, so it could vanish in a library upgrade with no visible change. **Reported as a
mitigated finding specifically so the false positive is on record.**

---

## Verified counts

The initial automated pass reported 49 message names, 85 operations and 33 handlers. All three were
partial. Verified figures, each reproducible:

| Metric | Verified | How |
|---|---|---|
| Canonical IPC channel names | **144** | `grep -c 'IPCEvents\["' IPCEvents.js` |
| Main-process registrations (raw) | **140** | regex over every `ipcMain.on/handle` + `DiscordIPC.main.on/handle` site |
| — minus 4 generic wrappers | **136 concrete** | `DiscordIPC.js:19,24` and `app/ipcMain.js:11,14` are transports, not endpoints |
| — live on any one host | **131** | `notifications.js` registers 5 channels twice in mutually exclusive branches |
| Bridge members | **30** | 26 capability modules + 2 aliases + 2 inline values |
| Allow-listed send / invoke channels | **25 / 13** | `renderer/ipc.js:9-10` |

---

## What the report deliberately does not claim

- That the app **downloads all its code on every launch**. It doesn't — only `shadercache` and the
  code caches are cleared at window creation (`mainScreen.js:379-383`). Chromium's HTTP cache is
  left intact, so subresources come from disk on later launches. Only the document URL is
  cache-busted, via `?_=${Date.now()}`.
- That any capability seen in code is actually **exercised**. No runtime tracing was done.
- That a third-party host **receives user data** because its URL appears in source. The network
  section separates "URL present" from "request observed" — which, for every row, is *none*.

---

## Reproducing any of it

```bash
# from the repo root
H=~/Library/Application\ Support/discord/0.0.380/modules
C="$H/discord_desktop_core/core.asar"

python3 ../../tools/asarq.py stats "$C"
python3 ../../tools/asarq.py list  "$C" | grep -v node_modules
python3 ../../tools/asarq.py cat   "$C" app/mainScreen.js 335 560
python3 ../../tools/asarq.py grep  "$C" "contextIsolation|sandbox|setPermission" app/
python3 ../../tools/asarq.py cat   "$C" app/mainScreenPreload.js
```

Your version number will differ — check `ls ~/Library/Application\ Support/discord/`. Line numbers
in the report are valid for core `0.0.380`; the shipped code is Babel-compiled but **not** minified,
so they're stable within a build.

### Rebuilding the PDF

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=30000 \
  --print-to-pdf=Discord-Desktop-Teardown.pdf "file://$PWD/report.html"
```

Diagrams are Mermaid, rendered at print time — the headless browser needs network access for the
Mermaid library on first run.

---

## Open questions

The report ends with ten, in priority order. The top three:

1. **Does the native Rust updater verify signatures?** `common/updater.js` is a thin JSON-RPC shim;
   the logic is compiled. Needs Ghidra or Hopper on `discord_dispatch`. This is the single largest
   gap in the analysis.
2. **Is the OAuth navigation window reachable or extendable by an attacker?** Needs a runtime test.
3. **Which `DiscordNative` members does the web bundle actually call?** Determines the real attack
   surface. Answerable in two minutes from the devtools console.

---

## Scope

Static analysis of a locally installed application, for defensive security review and
interoperability research. No accounts accessed, no authentication bypassed, no traffic
intercepted, no binaries executed for analysis, no DRM circumvented, **no exploit code produced**.
Compiled native modules were inventoried but not decompiled — the principal boundary of this work.

Not affiliated with or endorsed by Discord Inc. If anything here looks genuinely exploitable,
report it to [hackerone.com/discord](https://hackerone.com/discord) rather than opening an issue.
