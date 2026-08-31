---
name: "offensive-payloads"
source: "https://github.com/swisskyrepo/PayloadsAllTheThings"
type: "tactical-payload-methodology"
description: "Per-vulnerability payload methodology for web attacks: description, exploit steps, payload variants, encoding transformations, WAF/filter bypasses, and references for 60+ vuln classes."
---

# Offensive Payloads Library

Per-vulnerability knowledge template: (1) description + exploit steps, (2) payload variants, (3) encoding transforms, (4) WAF/filter bypass chain, (5) references. Mirror the repo layout: README.md + Burp Intruder wordlists + images + auxiliary files.

## Vulnerability Taxonomy (60+ classes, grouped)

### Injection family
- SQLi (union/error/blind/time; per-DB), NoSQLi ($where/$ne), XSS (reflected/stored/DOM; CSP bypass), XXE (blind OOB/DTD/SSRF), SSTI (per-engine), Command Injection, LDAPi, GraphQLi, CRLF, CSS, CSV, LaTeX, XPATH, XSLT, SAML, SSI, Prompt Injection

### Authentication / Access Control
- Account Takeover, API Key Leaks, CORS misconfig, CSRF, IDOR, JWT (alg:none/key confusion), OAuth, Open Redirect, Mass Assignment, Type Juggling

### Server-Side
- SSRF (metadata/gopher/DNS rebinding), LFI/RFI (log poisoning/PHP filters), Directory Traversal, Insecure Deserialization (per-language gadgets), Request Smuggling (CL.TE/TE.CL), Race Condition, Reverse Proxy misconfig, ORM Leak, Client Side Path Traversal, Zip Slip, Dependency Confusion

### Client-Side
- DOM Clobbering, Prototype Pollution, XS-Leak, Clickjacking, Tabnabbing, DOM XSS

### Business Logic / Misc
- Business Logic Errors, Brute Force Rate Limit, DoS (ReDoS/hash collision/slowloris), Insecure Randomness, Insecure SCM (.git), Insecure Management Interface, Upload Insecure Files, Hidden Parameters, HTTP Parameter Pollution, External Variable Modification, Virtual Hosts, Web Cache Deception, Web Sockets, DNS Rebinding, Headless Browser, Encoding Transformations, CVE Exploits

## Payload Crafting Principles
1. Context first — the sink decides the payload (HTML/attr/JS/SQL/template/CLI arg).
2. Variants per engine/version (SSTI/SQLi/SAML/XSLT differ by runtime).
3. Error → Blind → OOB escalation (in-band first, blind fallback, OOB last via DNSLOG).
4. Encoding layering — apply 1..N passes only as the filter demands; over-encoding breaks sinks.
5. Bypass as a chain — canonical payload + encoding + case/whitespace/comment + protocol abuse, layer by layer.
6. Polyglots for unknown contexts.

## WAF / Filter Bypass per layer
- Keyword filters → case variation, inline comments (UN/**/ION), equivalent functions (SUBSTRING↔SUBSTR)
- Character blocklists → encoding (%27↔%u0027↔&#39;), Unicode normalization, overlong UTF-8
- Length limits → OOB fetching, multi-request splitting, short-domain DNS
- Regex WAF → greedy/backtracking ReDoS side-channel, semantic equivalents
- Parser differentials → CL.TE smuggling, JSON↔XML↔multipart confusion, double URL-decode

## Encoding Transformations
URL encode (`'`→%27), Double URL encode, Unicode %u, HTML entity (&#39;/&apos;), Base64, UTF-7 (+ADw-), Overlong UTF-8.

## Field Notes
- Wordlists loadable by Burp Intruder/ffuf/nuclei directly.
- Wayback-archive referenced links; MkDocs site (swisskyrepo.github.io/PayloadsAllTheThings).
- Siblings: InternalAllTheThings (AD), HardwareAllTheThings (IoT).