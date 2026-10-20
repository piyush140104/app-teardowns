<div align="center">

# App Teardowns

### Understand any app on your machine — down to the line number.

**See a behaviour you can't explain. Find out exactly how it works, who it talks to, and what it's allowed to do to your computer.**

[![License: MIT](https://img.shields.io/badge/tools-MIT-f4c430?style=flat-square)](LICENSE)
[![Writeups: CC BY 4.0](https://img.shields.io/badge/writeups-CC_BY_4.0-2b5fd9?style=flat-square)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&logo=python&logoColor=white)](tools/)
[![No exploit code](https://img.shields.io/badge/no_exploit_code-enforced-117a4a?style=flat-square)](DISCLAIMER.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-6b3fa0?style=flat-square)](apps/_template/METHOD.md)

**[Teardowns](#teardowns) · [Quick start](#quick-start) · [How a teardown works](#how-a-teardown-works) · [What you can take apart](#what-you-can-take-apart) · [Highlights](#highlights) · [FAQ](#faq) · [Method](apps/_template/METHOD.md)**

<code>python3 tools/asarq.py grep core.asar "contextIsolation|sandbox|nodeIntegration"</code>

</div>

> [!IMPORTANT]
> Everything here is **static analysis of software already installed on a machine the analyst owns**,
> for interoperability research, security education and software preservation. No exploit code, no
> DRM circumvention, no credential access. Read [DISCLAIMER.md](DISCLAIMER.md) before using any of
> it — and before adding a teardown of your own.

---

You can *use* software. You usually can't *read* it. A desktop app is a sealed box: you see the
buttons, never the wiring — what it's permitted to do to your filesystem, which servers it was
built to reach, which switches its developers left in and never documented.

This repo opens the box. Each teardown reconstructs how an app is actually assembled and publishes
the evidence alongside the conclusion, so you can check the work instead of trusting it. Every
claim cites a **file and a line number**. Where the evidence runs out, the writeup says so.

## Teardowns

| App | Version | What's covered | Report |
| --- | --- | --- | --- |
| **Discord Desktop** | `0.0.380` · macOS arm64 | Two-archive architecture · the 30-member `DiscordNative` bridge · 136 privileged IPC endpoints · permission & navigation fencing · update pipeline · 18 external endpoints · 20+ undocumented settings | **[Read →](apps/discord/)** · [PDF (35 pp)](apps/discord/Discord-Desktop-Teardown.pdf) · [Findings](apps/discord/findings.md) |

More apps are in progress. Request one in [issues](../../issues), or
[write one](apps/_template/METHOD.md).

## Quick start

### Find the real code

For Electron apps it is rarely where you first look:

```bash
ls /Applications/<App>.app/Contents/Resources/        # app.asar — often just a launcher
ls ~/Library/Application\ Support/<app>/              # frequently the real payload
```

If the bundled archive holds only a megabyte or two of source, it's a downloader and the actual
program lives elsewhere. Chase it before you read a single line — Discord's entire product shell
is 9 MB in your home folder, not in `/Applications`.

### Open it without unpacking it

```bash
python3 tools/asarq.py stats core.asar
```

`asarq.py` reads straight out of the archive — no unpacking 2,400 files to disk, no temp
directories, line numbers that match what you cite in a report. Pure standard library.

### The four commands that open any Electron app

```bash
python3 tools/asarq.py stats core.asar                                      # how big is the real surface
python3 tools/asarq.py list  core.asar | grep -v node_modules               # what is hand-written
python3 tools/asarq.py grep  core.asar "contextIsolation|sandbox|preload"   # the security posture
python3 tools/asarq.py grep  core.asar "ipcMain\.(on|handle)"               # the privileged API
```

Thirty seconds, and you know the size of the attack surface, how the window is fenced, and every
operation the app will perform on request. Try it on VS Code, Slack, Postman, Notion or WhatsApp —
they all open the same way.

### Read a file with real line numbers

```bash
python3 tools/asarq.py cat core.asar app/mainScreen.js 335 560
```

Full tooling reference in [tools/README.md](tools/README.md).

## How a teardown works

```
  locate the real payload ─────► inventory ──────► dependency graph
                                                          │
                                                          ▼
   feature-to-file map ◄──── data & event flows ◄──── call graph
            │
            ▼
   security boundaries ──► network inventory ──► config & hidden switches
            │
            ▼
   blind spots (what could NOT be resolved) ──► findings ──► open questions
```

Twelve steps, same order every time, so two teardowns can be read side by side. The checklist is
[apps/_template/METHOD.md](apps/_template/METHOD.md) — not a summary of the method, the actual
checklist used to produce the reports here.

The step most writeups skip is the second-to-last. **Recording what you could not resolve** is what
separates a teardown from a guess: compiled binaries you didn't decompile, remote code you can't
see, objects built dynamically that static analysis can't enumerate.

### Every finding carries a confidence label

| Label | Meaning |
| --- | --- |
| **Confirmed** | Read directly in the source; reproducible with a command in the appendix |
| **Strongly supported** | Several independent lines of evidence agree |
| **Tentative** | One line of evidence; plausible alternative readings exist |
| **Unknown** | Evidence unavailable — compiled code, remote code, or needs runtime observation |

A teardown that says *Unknown* ten times is worth more than one that says *Confirmed* fifty times
and is wrong twice.

### And every finding is classified

| Class | Meaning |
| --- | --- |
| **Design** | Intended behaviour, correctly implemented. Carries risk by construction, not by mistake |
| **Potential** | A real weakness. Needs verification before it gets called a vulnerability |
| **Mitigated** | Looks alarming, isn't. Recorded so the false positive is on the record |
| **Unknown** | Can't be settled without evidence this analysis didn't have |
| **Positive** | A defence that is correctly built |

## What you can take apart

What a teardown gives you per target type, and what you need on your machine to produce it:

| Target | What a teardown recovers | Requirements |
| --- | --- | --- |
| **Electron / `.asar` apps** | Process tiers, preload bridge, full IPC surface, permission and navigation handling, every hardcoded endpoint | None — [`tools/asarq.py`](tools/) and Python 3.8+ |
| **Plain JavaScript / Node apps** | Module graph, imports, routes, native add-on boundaries | None |
| **Packaged app bundles** | File inventory, digests, plists, bundle anatomy, embedded resources | None |
| **Config & settings stores** | Undocumented switches, defaults, which code paths they change | None |
| **Source maps, when shipped** | Original file and symbol names behind a bundle | None |
| **.NET assemblies** | Metadata, CIL, declared native boundaries | None (static) |
| **Go / Rust binaries** | Embedded toolchain version, modules, dependency graph | None (static) |
| **Android APKs** | Manifest, classes, decompiled methods | A JDK and a headless decompiler |
| **Native binaries** | Pseudocode, assembly, strings, symbols, cross-references | Ghidra (free), Hopper or IDA |
| **Saved network captures** | Requests, responses, exposed payloads | A HAR or pcap you captured yourself |

The first five need nothing but this repo. That covers most desktop apps you actually use, because
most of them are Electron.

## Highlights

Three findings from the Discord teardown, picked because each one changed the answer.

### The app you installed isn't the app that runs

`/Applications/Discord.app` contains a **launcher** — 39 source files. The real 9 MB shell is
downloaded separately into `~/Library/Application Support/discord/`, which is why Discord updates
itself without ever asking for an admin password, and why the code that actually executes sits in a
user-writable directory.

[Read the architecture section →](apps/discord/README.md#nine-things-worth-knowing)

### A bridge that static analysis said was unreadable

Automated tooling reported the native bridge as `members: []`, `unknown_members: 1` — it found the
`contextBridge` call and gave up, because the object is assembled from `require()` expressions
rather than written as literal properties. Reading `mainScreenPreload.js:20-48` by hand resolved
**all 30 members, zero unresolved**: filesystem, clipboard, screen capture, OS keychain,
native-module installation, WebAuthn.

[Read the full enumeration →](apps/discord/README.md#verified-counts)

### A vulnerability that turned out not to be one

`moduleUpdater.js:728` joins archive-controlled filenames onto a destination path with no
sanitisation — textbook zip-slip, and any scanner will flag it. It's safe anyway, because the
bundled `yauzl` rejects `..` segments before emitting an entry.

It's reported as a **mitigated** finding precisely so the false positive is on the record — and
because the guarantee lives in a dependency rather than in Discord's code, which means it could
vanish in a library upgrade with nothing visibly changing.

[Read all findings →](apps/discord/findings.md)

## FAQ

<details>
<summary><strong>Is reverse engineering legal?</strong></summary>

In many jurisdictions, yes — and for interoperability it's explicitly protected in some
(DMCA §1201(f) in the US, Article 6 of the EU Software Directive). Courts have upheld it
repeatedly: *Sega v. Accolade*, *Sony v. Connectix*, *Google v. Oracle*.

That is not a universal permission. Protection varies by jurisdiction and purpose, a product's
terms of service may prohibit it regardless of what the law allows, and **understanding how
something works is legal while copying its code is not**. Full picture in
[DISCLAIMER.md](DISCLAIMER.md).

</details>

<details>
<summary><strong>Do these teardowns contain exploits?</strong></summary>

No. Findings describe design properties and weaknesses with enough precision to be verified and
fixed, and no further. No proof-of-concept code, no weaponisation, no working attack chains. It's
rule 4 of [the house rules](#house-rules) and it's enforced on contributions.

If something here looks genuinely exploitable, report it to the vendor rather than opening an
issue.

</details>

<details>
<summary><strong>Why static analysis only?</strong></summary>

Because it's reproducible and it's honest about its limits. Anyone can re-run the commands in an
appendix against their own copy and get the same output.

Runtime analysis is allowed in a teardown when it's done in an isolated environment with test
accounts — but it must be kept **visibly separate** from static findings. A report that blurs
"this code can do X" into "this app did X" isn't worth reading.

</details>

<details>
<summary><strong>Why does a finding say "Unknown" instead of giving an answer?</strong></summary>

Because the evidence wasn't there. Compiled binaries that weren't decompiled, code that runs on a
remote server, objects built at runtime that no static pass can enumerate.

Filling those gaps with a confident guess is the single most common failure in published
teardowns. Every report here ends with a list of open questions and the specific test that would
close each one.

</details>

<details>
<summary><strong>Can I use a teardown to build a compatible client or a similar feature?</strong></summary>

Understanding is yours to use; expression isn't. Copyright attaches to the code itself, so anything
you build should be written clean-room — from a behavioural description, never from copied source.
That distinction is what kept Compaq, Samba and WINE on the right side of the line.

</details>

<details>
<summary><strong>Which apps are you doing next?</strong></summary>

Open an [issue](../../issues) with the app and what you're curious about. Electron apps are fastest
because the tooling here covers them end to end; anything needing a decompiler takes longer.

</details>

<details>
<summary><strong>I'm a vendor and I think something here is wrong.</strong></summary>

Open an issue or get in touch. Corrections are made promptly and credited. Several entries in the
Discord teardown already exist *because* an earlier reading turned out to be wrong — getting
corrected is how this gets better.

</details>

## House rules

These aren't decoration. They're why the writeups are worth reading.

1. **Never fabricate.** No invented file names, line numbers, functions, endpoints or observations. If a line number can't be verified, it doesn't ship.
2. **Capability ≠ behaviour.** A function that *can* read your clipboard is not evidence that your clipboard *was* read.
3. **Static ≠ runtime.** A URL in source is not a network request. If no traffic was captured, the report says "not observed."
4. **No exploit code.** Precise enough to verify and fix. No further.
5. **Report the good too.** Defences that are correctly built get written up beside the gaps. A findings list with no positives is a distorted picture of how an app is engineered.
6. **Correct the record out loud.** Where an earlier assumption or an automated tool got something wrong, the correction is stated explicitly rather than quietly patched. Those are often the most interesting entries.

## Contributing

Copy [`apps/_template/`](apps/_template/) to `apps/<your-app>/`, work through
[`METHOD.md`](apps/_template/METHOD.md), add a row to [Teardowns](#teardowns), open a PR.

The template ships with the classification tables and per-finding structure already in place, so a
new teardown is fill-in-the-blanks rather than re-deciding the format. Reports are written in HTML
and rendered to PDF with headless Chrome:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=30000 \
  --print-to-pdf=<App>-Teardown.pdf "file://$PWD/report.html"
```

Diagrams are Mermaid, rendered at print time.

## Documentation

- **[Method](apps/_template/METHOD.md)** — the 12-step checklist, with the non-negotiables
- **[Tools](tools/README.md)** — `asarq.py` reference, plus how to census IPC handlers
- **[Disclaimer](DISCLAIMER.md)** — scope, legal picture, responsible disclosure
- **[Discord teardown](apps/discord/)** — the worked example

## Disclaimer

For lawful research, education, interoperability, software preservation, and analysis of software
you own or are authorised to examine. See [DISCLAIMER.md](DISCLAIMER.md) for the full position on
scope, jurisdiction and responsible disclosure.

## License

Tools in `tools/` — **[MIT](LICENSE)**.
Writeups in `apps/` — **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**: use them,
quote them, build on them, credit the source.

Product names and trademarks belong to their owners. This project is not affiliated with, endorsed
by, or connected to any company whose software it examines.
