# App Teardowns

**What's actually inside the apps you use every day.**

You can use software. You can't usually *read* it. This repo takes apps apart — statically, from
the copies already installed on a machine — and writes up how they're really built: their process
boundaries, the capabilities they hold over your computer, the servers they're wired to, and the
configuration switches nobody documents.

Every claim in every teardown cites a **file and a line number**. Where the evidence runs out, the
writeup says so instead of guessing.

---

## Teardowns

| App | Platform | What's covered | Report |
|---|---|---|---|
| **Discord Desktop** `0.0.380` | macOS arm64 | Two-archive architecture, the 30-member `DiscordNative` bridge, 136 privileged IPC endpoints, permission and navigation fencing, the update pipeline, 18 external endpoints, 20+ undocumented settings | [Read →](apps/discord/) · [PDF](apps/discord/Discord-Desktop-Teardown.pdf) |

*More apps coming. Suggestions welcome in [issues](../../issues).*

---

## How a teardown is structured

Each app lives in `apps/<name>/` and answers the same sixteen questions in the same order, so you
can compare two apps side by side:

```
apps/discord/
├── README.md                      summary — read this first
├── findings.md                    every finding, classified, with remediation
├── Discord-Desktop-Teardown.pdf   the full report (35 pages, diagrams)
└── report.html                    source for the PDF
```

The long report always covers: architecture → file inventory → dependency graph → call graph →
data flows → event flows → security boundaries → network inventory → runtime limits →
configuration → dynamic-code blind spots → feature-to-file map → findings → open questions →
reproduction steps.

### Every finding carries a confidence label

| Label | Meaning |
|---|---|
| **Confirmed** | Read directly in the source; reproducible with a command in the appendix |
| **Strongly supported** | Multiple independent lines of evidence agree |
| **Tentative** | One line of evidence; plausible alternative readings exist |
| **Unknown** | Evidence unavailable — compiled code, remote code, or needs runtime observation |

A teardown that says "Unknown" ten times is more useful than one that says "Confirmed" fifty times
and is wrong twice.

---

## Rules this repo follows

These aren't decoration. They're why the writeups are worth reading.

1. **Never fabricate.** No invented file names, line numbers, functions, endpoints, or
   observations. If a line number can't be verified, it doesn't go in.
2. **Separate capability from behaviour.** A function that *can* read your clipboard is not proof
   that your clipboard *was* read. These are reported as different things.
3. **Separate static from runtime.** A URL in source is not a network request. Unless traffic was
   actually captured, the report says "not observed."
4. **No exploit code.** Findings describe design properties and weaknesses with enough precision to
   be verified and fixed. No proof-of-concept exploits, no weaponisation, no working attack chains.
5. **Report the good too.** Defences that are correctly built get written up alongside the gaps.
   Most teardowns only hunt for problems, which gives a distorted picture of how an app is actually
   engineered.
6. **Correct the record.** Where an earlier assumption or an automated tool got something wrong,
   the correction is stated explicitly rather than quietly fixed. Several of the most interesting
   entries in the Discord teardown are corrections.

---

## Tooling

[`tools/asarq.py`](tools/) — query an Electron `.asar` archive **in memory**: list, cat with line
numbers, grep, stats. No unpacking thousands of files to disk just to read six of them.

```bash
python3 tools/asarq.py stats core.asar
python3 tools/asarq.py list  core.asar | grep -v node_modules
python3 tools/asarq.py cat   core.asar app/mainScreen.js 335 560
python3 tools/asarq.py grep  core.asar "contextIsolation|sandbox|setPermission" app/
```

Most Electron apps on your machine — VS Code, Slack, Postman, WhatsApp, Notion — open with the
same four commands.

---

## Adding a teardown

Copy [`apps/_template/`](apps/_template/) to `apps/<your-app>/` and work through
`METHOD.md`, which is the checklist used for every report here. Then add a row to the
table above.

---

## Scope and ethics

Everything here is **static analysis of software already installed on a machine the analyst owns**,
for interoperability research, security education, and software preservation. Nothing is
decompiled from a service, no accounts are accessed, no authentication is bypassed, no traffic is
intercepted from anyone else, and no DRM is circumvented.

Reverse engineering for these purposes is lawful in many jurisdictions and is explicitly protected
in some — but **it is not protected everywhere, and it may still conflict with a product's terms of
service**. Read [DISCLAIMER.md](DISCLAIMER.md) before using anything here, and before adding a
teardown of your own.

**Found something that looks genuinely exploitable?** Don't open an issue — report it to the
vendor first. Discord's is at [hackerone.com/discord](https://hackerone.com/discord).

---

## License

Code in `tools/` — [MIT](LICENSE).
Writeups in `apps/` — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use them, quote
them, build on them, just credit the source.

Product names and trademarks belong to their owners. This repo is not affiliated with, endorsed
by, or connected to any of the companies whose software it examines.
