# <App Name> — Teardown

**Target** <App>.app · version `x.y.z` · <platform/arch>
**Method** static analysis only — no runtime instrumentation, no network capture
**Report** [<App>-Teardown.pdf](<App>-Teardown.pdf)
**Findings** [findings.md](findings.md)

---

## The one-line version

<What this app actually is, architecturally, in one sentence.>

## N things worth knowing

**1 · <Headline>.** <Claim with `file.js:line`.>

**2 · <Headline>.** <Claim with `file.js:line`.>

---

## Corrections

<Where the obvious reading turned out to be wrong, and what checking changed. These are usually
the most valuable part of a teardown — keep the section even if it has one entry.>

---

## Verified counts

| Metric | Verified | How |
|---|---|---|
|  |  |  |

---

## What this report deliberately does not claim

-
-

---

## Reproducing any of it

```bash
python3 ../../tools/asarq.py stats "<archive>"
python3 ../../tools/asarq.py cat   "<archive>" <file> <from> <to>
```

---

## Open questions

1.
2.

---

## Scope

Static analysis of a locally installed application, for defensive security review and
interoperability research. No accounts accessed, no authentication bypassed, no traffic
intercepted, no DRM circumvented, no exploit code produced.

Not affiliated with or endorsed by <Vendor>. If anything here looks genuinely exploitable, report
it to the vendor rather than opening an issue.
