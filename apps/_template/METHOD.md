# Teardown method

The checklist every report in this repo follows. Work it in order — each step feeds the next.
Copy this directory to `apps/<your-app>/`, delete what doesn't apply, and keep the section
numbering so reports stay comparable.

**Before you start:** you must own or be authorised to examine the copy you're analysing. Read
[../../DISCLAIMER.md](../../DISCLAIMER.md).

---

## 0 · Set up

Find the real code. For Electron apps it is rarely where you first look:

```bash
ls -la /Applications/<App>.app/Contents/Resources/        # app.asar, maybe app/
ls -la ~/Library/Application\ Support/<app>/              # often the real payload
```

If `app.asar` is small (under ~2 MB of source), it's probably a launcher and the real shell lives
elsewhere. Chase it before writing anything.

```bash
python3 tools/asarq.py stats <archive>.asar
python3 tools/asarq.py list  <archive>.asar | grep -v node_modules
```

Record SHA-256 of every archive you analyse. Put it in the report header.

---

## 1 · Understand the codebase

Identify, with file paths:

- entry points (main process, renderer, preload, workers)
- how the UI is loaded — bundled, remote, or hybrid
- native bridge implementations
- IPC definitions and registrations
- native modules and OS integrations
- configuration files and environment variables
- update, cache, persistence and network layers

Output: a project architecture overview and a table of important files. **Don't invent files, and
don't assume a filename proves an implementation** — open it.

## 2 · Dependency graph

Follow real `require`/`import` call sites. For each important edge record source file:line, target,
relationship type, evidence, and why it matters.

Output: a Mermaid graph. Distinguish **static** from **dynamically loaded** dependencies — in
Electron the dangerous edges are usually the ones not written as imports (a preload attached by
filename, a module loaded by runtime name, a cross-archive require).

Name the central modules everything routes through.

## 3 · Call graph

Trace startup first, then representative features: loading the UI, bridge access, file I/O,
clipboard, secure storage, power events, caching, native-module install, network, window lifecycle.

For each: **trigger → entry point → intermediate calls → handler → underlying API → result/error**.
Include exact paths, line numbers, function names, message identifiers.

Output: Mermaid sequence diagrams for the most important flows. **Never claim a call relationship
from name similarity alone** — verify the call site or mark it inferred.

## 4 · Data flows

For each sensitive flow — user input, IPC payloads, credentials, clipboard, file data,
screen-capture data, anything leaving the machine — record:

1. where it originates
2. what transforms it
3. which modules receive it
4. whether it's stored, transmitted, or discarded
5. what validation or security checks apply
6. **what remains unknown**

Keep **capability** and **demonstrated behaviour** strictly apart. A function that can read your
clipboard is not proof your clipboard was read.

## 5 · Event flows

Startup, shutdown, window lifecycle, power/lock/sleep, IPC messages, renderer lifecycle, auth,
update, error. For each: **source → listener registration → callback → downstream effects → state
change**.

Separate what happens **automatically** from what needs a user action — that distinction is usually
the most interesting thing in the section.

Note missing listeners, dynamic registration, and cleanup gaps **where evidence supports them**.

## 6 · Security & permission boundaries

- which code runs in which process
- which origins can reach privileged functions
- how handlers authenticate, validate, authorise
- can untrusted input reach filesystem or OS APIs
- clipboard, screen capture, secure storage handling
- can env vars or URLs redirect what the app loads
- is native-module installation restricted and validated
- CSP, sandbox, context isolation, navigation settings

Classify every finding: **Design / Potential / Mitigated / Unknown / Positive**. Give evidence,
impact, prerequisites, remediation.

**Do not call something a vulnerability because a powerful API exists.** And write up the defences
that are correctly built — a findings list with no positives is a distorted picture.

## 7 · Network

Enumerate every hardcoded URL and configurable endpoint. For each: host, file:line, calling
function, evidence-backed purpose, data potentially transmitted, trigger conditions, **whether a
real request was observed**, and confidence.

"URL present in source" and "request observed" are different columns. If you captured no traffic,
every row in the second column says *no*.

## 8 · Runtime (optional, and only if authorised)

If you have a safe environment: which modules load, which handlers register, which operations run,
what traffic occurs, how config changes behaviour, what dynamic objects really expose.

Use test accounts and non-destructive actions. Document reproduction steps and keep runtime
observations visibly separate from static ones.

**If you didn't do runtime analysis, say so plainly and provide a test plan instead.** Never imply
you observed something you inferred.

## 9 · Configuration & hidden switches

Environment variables, feature flags, command-line switches, build constants, debug options,
alternate routes. For each confirmed switch: where defined, where read, default, which code paths
change, user/env/build-controlled, security implications, how to verify safely.

Look for undocumented options — but not every internal flag is a secret feature.

## 10 · Dynamic code & blind spots

Anything a static pass couldn't resolve: dynamically built objects, runtime `require`, generated
methods, missing source, compiled binaries.

Build a consolidated inventory and mark each entry: confirmed by source / found only by reference /
dynamically generated / **unresolved**. Never fill a gap with a guess.

## 11 · Feature-to-file map

| Feature | Entry point | Intermediate | Handler | Underlying API | Evidence |

Every major feature you can actually verify, linked end to end so a reader can follow it. If the
code is minified and line numbers are unstable, say so and give a search term instead.

## 12 · Report

Order: executive summary → architecture → structure → dependency graph → call graph → data flows →
event flows → security → network → runtime & limits → configuration → dynamic code → feature map →
findings & remediation → open questions → appendix (method + reproduction).

Each major finding gets: **What we found · Evidence · How the files connect · What it means in
simple English · Why it matters · Confidence · Next verification step.**

---

## Non-negotiables

- Inspect real files before concluding anything.
- Never fabricate file names, line numbers, functions, endpoints or observations.
- Keep facts, inferences and hypotheses visibly separate.
- Capability ≠ exercised behaviour.
- URL in source ≠ data sent to that host.
- Module name ≠ business relationship.
- Verify any tool-generated graph against the actual code before publishing it.
- Don't claim an app re-downloads everything on launch without checking its caching.
- State what's missing precisely rather than papering over it.
- **No exploit code. No weaponisation. No working attack chains.**
- If something looks genuinely exploitable, tell the vendor before you publish.

---

## Build the PDF

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=30000 \
  --print-to-pdf=<App>-Teardown.pdf "file://$PWD/report.html"
```
