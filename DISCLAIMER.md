# Disclaimer & responsible use

## What this repo is

Static analysis of software already installed on a machine the analyst owns, written up for
**interoperability research, security education, and software preservation**.

## What it is not

- Not a collection of exploits. No proof-of-concept code, no weaponisation, no working attack chains.
- Not a piracy, cracking, licence-bypass or DRM-circumvention resource.
- Not affiliated with, endorsed by, or connected to any company whose software it examines.
- Not legal advice.

## Rules for anything published here

1. **Analyse only software you own or are authorised to examine.** Having a copy installed is not
   automatically authorisation — check the terms you agreed to.
2. **Static analysis of local files only**, unless runtime testing is performed in an isolated
   environment with test accounts you control.
3. **No accounts accessed, no authentication bypassed, no traffic intercepted** from anyone other
   than yourself, and no requests sent to private or production infrastructure beyond what the
   application makes on its own.
4. **No DRM circumvention, no licence-check defeat, no anti-cheat evasion.**
5. **No exploit code.** Findings describe design properties and weaknesses with enough precision
   to be verified and fixed — and no further.
6. **Vendor first.** If a finding looks genuinely exploitable, report it to the vendor and give
   them time before publishing. Most large vendors run a bug bounty; Discord's is at
   [hackerone.com/discord](https://hackerone.com/discord).

## The legal picture, honestly

Reverse engineering is lawful in many jurisdictions and explicitly protected for interoperability
in some — DMCA §1201(f) in the United States, Article 6 of the EU Software Directive. Courts have
repeatedly upheld it: *Sega v. Accolade*, *Sony v. Connectix*, *Google v. Oracle*.

**None of that makes it universally permitted.** Three things remain true:

- Protection varies by jurisdiction and by purpose.
- A product's terms of service may prohibit it regardless of what the law allows. Breaching terms
  is a contractual matter, not a criminal one, but it is still a real consequence.
- **Understanding how something works is legal; copying its code is not.** Copyright attaches to
  expression. Anything built from a teardown here should be written clean-room, from a behavioural
  description, never from copied source.

## Accuracy

Every claim cites a file and a line number against a specific version, and carries a confidence
label. Software changes — a line number valid for one build may be meaningless in the next. Verify
against your own copy before relying on anything. Where evidence was unavailable, the reports say
"unknown" rather than guessing, and that is a deliberate feature of the format.

## Takedowns and corrections

If you represent a vendor and believe something here is inaccurate, oversteps, or should not be
public, open an issue or get in touch. Corrections are welcome and will be made promptly.

## Your responsibility

Using anything in this repository means you accept responsibility for complying with the laws of
your jurisdiction and the terms of any software you examine. The author accepts no liability for
how these materials are used.
