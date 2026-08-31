---
name: "security-resource-map"
source: "https://github.com/Hack-with-Github/Awesome-Hacking"
type: "resource-orientation"
description: "Maps the offensive security resource landscape: 43 domain-specific awesome-lists plus 35+ cross-cutting tools. Orientation layer — tells you which specialized list or tool to reach for next."
---

# Security Resource Map

An orientation layer: it does not hold the tools, it tells you which specialized awesome-list / tool to reach for given a domain or assessment phase.

## How to Use
1. Identify target domain or assessment phase.
2. Jump to matching row below.
3. Route to that awesome-list / tool for deep tooling.

## Domain Taxonomy — 43 Awesome-Lists (sample of key rows)
| Domain | Awesome-list |
|---|---|
| Android Security | android-security-awesome |
| AppSec | awesome-appsec |
| Bug Bounty | awesome-bug-bounty |
| CI/CD Attacks | awesome-cicd-attacks |
| CTF | awesome-ctf |
| Detection Engineering | awesome-detection-engineering |
| Embedded/IoT Security | awesome-embedded-and-iot-security |
| Fuzzing | Awesome-Fuzzing |
| ICS/SCADA | awesome-industrial-control-system-security |
| Malware Analysis | awesome-malware-analysis |
| OSINT | awesome-osint |
| Password Cracking | awesome-password-cracking |
| Pentest | awesome-pentest |
| Reversing | awesome-reversing |
| Threat Intelligence | awesome-threat-intelligence |
| Vehicle Security | awesome-vehicle-security |
| Web Hacking | awesome-web-hacking |
| Web3 Security | Awesome-web3-Security |
| YARA | awesome-yara |
| (…full list: Android/AppSec/Asset-Discovery/BugBounty/Cellular/CI-CD/CTF/CyberUni/CyberSkills/Cybersources/DetectionEng/DevSecOps/Drone/EmbeddedIoT/Fuzzing/Hacking/Honeypots/IR/ICS/InfoSec/IoT-HW/Mainframe/MalwareAnaly/Persistence/NodeJS/OSINT/OSX-iOS/PwCrack/Pcap/Pentest/PHP/PromptInjection/RTC/RedTeam/RL-cyber/Reversing/SecTalks/SecLists/Security/SocialEng/StaticAnalysis/h4cker/ThreatIntel/Vehicle/WebHack/Web3/YARA) |

## Cross-Cutting Tools — 35+
| Tool | What it solves |
|---|---|
| GTFOBins | Unix binaries abusable for privesc / sudo |
| CyberChef | Decode/encode/transform data without code |
| SecLists | Default wordlists for assessments |
| Vulhub | Docker-Compose pre-built vulnerable envs |
| Hacker101 | Free web-security class by HackerOne |
| OWASP CheatSheetSeries | AppSec cheat sheets |
| PayloadsAllTheThings | Web attack payloads (see offensive-payloads) |
| trickest/cve | Daily-updated CVE PoC index |
| DetectionLab | Vagrant/Packer lab with security tooling |
| Infosec_Reference | Infosec reference library |
| Bug Bounty Reference | Bug bounty write-ups by bug type |
| (…full list incl. APTnotes, awesome-forensics, linux-kernel-exploitation, Probable-Wordlists, RedTeam-Physical-Tools, reverseengineering-reading-list, RFSec-ToolKit, ThreatHunter-Playbook, awesome-tor, awesome-web-security, etc.) |

## Assessment-Phase → Resource Routing
| Phase | Primary resource(s) |
|---|---|
| Scope & asset discovery | Awesome-Asset-Discovery, OSINT |
| Recon / fingerprinting | SecLists, awesome-pentest |
| Vuln discovery (web) | PayloadsAllTheThings, awesome-web-hacking |
| Vuln discovery (mobile) | android-security-awesome, osx-and-ios-security-awesome |
| Vuln discovery (IoT/hardware) | awesome-embedded-and-iot-security |
| Fuzzing | Awesome-Fuzzing |
| Exploitation & payload | PayloadsAllTheThings, trickest/cve |
| Privilege escalation | GTFOBins, linux-kernel-exploitation |
| Password recovery | awesome-password-cracking, Probable-Wordlists |
| Lateral movement / red team | Red-Teaming-Toolkit, RedTeam-Physical-Tools |
| Persistence analysis | awesome-malware-persistence |
| Forensics & IR | awesome-forensics, awesome-incident-response |
| Threat intel & hunting | awesome-threat-intelligence, ThreatHunter-Playbook |
| Deception | awesome-honeypots |
| Reporting / learning | Hacker101, awesome-cyber-security-university |
| Data transform/decode | CyberChef |
| Lab environment | Vulhub, DetectionLab, awesome-cyber-skills |

## Routing Heuristics
- Mobile → android-security-awesome / osx-and-ios-security-awesome
- Cloud / CI-CD → awesome-devsecops + awesome-cicd-attacks
- Smart contracts → Awesome-web3-Security
- Need wordlists → SecLists (default) / Probable-Wordlists (human passwords)
- Decode unknown blob → CyberChef "Magic"
- Linux privesc → GTFOBins first, then kernel-exploitation
- AI/LLM target → awesome-prompt-injection + Awesome-AI-Security

## Field Notes
- Meta-list: each entry links outward to a deeper list. Treat as routing table, not catalog.
- CC0-1.0 licensed; community-contributed, may lag behind upstream.