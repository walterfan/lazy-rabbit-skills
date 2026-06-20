# Security, Privacy & Accessibility Deep-Dive Checklist

Use this reference when filling in Sections 4, 5, and 6 of the design spec. It preserves the compliance rigor of the official template v2.2.2 while the main template keeps the structure lean.

---

## Table of Contents

1. [Security: Assets](#1-security-assets)
2. [Security: Controls](#2-security-controls)
3. [Security: STRIDE Threat Modeling](#3-stride-threat-modeling)
4. [Privacy: Data Classification](#4-privacy-data-classification)
5. [Privacy: Data Subjects](#5-privacy-data-subjects)
6. [Privacy: Purpose of Processing](#6-privacy-purpose-of-processing)
7. [Privacy: Data Lifecycle](#7-privacy-data-lifecycle)
8. [Accessibility: UE Design Checklist](#8-accessibility-ue-design-checklist)
9. [Accessibility: Programming Checklist](#9-accessibility-programming-checklist)

---

## 1. Security: Assets

List every asset stored, transferred, or processed by this feature:

- Restricted Data (L5): Customer communication content (recordings, chat, images, meeting titles)
- Confidential Data (L4): Other L4-L5 per Data Handling Standard
- L3: Unique identifiers (User ID, Account ID, PMI), direct identifiers (name, email), precise location, online tracking IDs (IP)
- L2: Data that combined with other info can identify an individual (gender, ethnicity), metadata identifiers (meeting ID, polling ID)

For each asset, document: name, classification level, where stored, who can access.

---

## 2. Security: Controls

Evaluate each control category:

| Control | Questions to Answer |
|---------|-------------------|
| **Authentication** | How are users/services authenticated? |
| **Authorization** | How is access scoped? Role-based? |
| **Customer Data Access** | Does any employee/staff member gain new persistent access? Provisioned via your SSO / access-request system? |
| **Encryption at rest** | AES-256 GCM minimum per Cryptographic Algorithm Standard? |
| **Encryption in transit** | TLS 1.2+ per Cryptographic Algorithm Standard? |
| **Auditing & Logging** | What events are logged? Follow Secure Logging Principles. |
| **Monitoring** | Alerts for anomalous access patterns? |
| **Input validation** | All external input validated and sanitized? |
| **Output validation** | Outputs scrubbed of sensitive data before display? |
| **Network-level** | Firewall rules, VPC isolation, trust boundaries? |

---

## 3. STRIDE Threat Modeling

For each threat type, ask the corresponding question:

| Type | Property Violated | Ask |
|------|------------------|-----|
| **S**poofing | Authentication | Can an attacker pretend to be another user/service? |
| **T**ampering | Integrity | Can data be modified on disk, network, or in memory? |
| **R**epudiation | Non-repudiation | Can someone deny performing an action? Are actions logged? |
| **I**nformation Disclosure | Confidentiality | Can unauthorized parties access sensitive data? |
| **D**enial of Service | Availability | Can resources be exhausted to degrade service? |
| **E**levation of Privilege | Authorization | Can someone perform actions beyond their permissions? |

For each identified threat, document:
- Threat ID (TM-01, TM-02, ...)
- STRIDE category
- Detailed description with risk statement
- Mitigation(s)
- Status: Mitigated / Partially mitigated / Not mitigated

---

## 4. Privacy: Data Classification

Per the organization's Data Handling Standard:

| Level | Examples |
|-------|---------|
| L5 | Customer communication content: recordings, chat messages, chat images, meeting titles |
| L4 | Other restricted data per Data Handling Standard |
| L3 | Unique identifiers (User ID, Account ID, PMI, DOB), direct identifiers (name, email), precise location (street address), online tracking IDs (IP) |
| L2 | Combinable identifiers (gender, ethnicity), metadata identifiers (meeting ID, polling ID) |

---

## 5. Privacy: Data Subjects

Check all that apply:

- [ ] Account Admin
- [ ] Host / Creator / Channel Owner (Content Owner)
- [ ] Internal Participant (same account)
- [ ] External Participant (different account, logged in)
- [ ] Non-logged-in user
- [ ] Third-party vendor (integrations, purchased datasets)

Key rule: Data of external participants / non-logged-in users cannot be shared with another account unless those users have consented.

---

## 6. Privacy: Purpose of Processing

Check all that apply:

- [ ] Provide Products & Services (product cannot operate without this data)
- [ ] Product Research & Development
- [ ] Marketing & Promotions
- [ ] Authentication, Integrity, Security & Safety
- [ ] AI/ML Training

Each purpose carries specific privacy guidance (aggregation rules, opt-in requirements by jurisdiction, etc.). See Purpose Limitation Privacy Playbook.

---

## 7. Privacy: Data Lifecycle

| Question | Standard Reference |
|----------|-------------------|
| Integrated with DSAR (Data Subject Access Request)? | Data Subject Access & Deletion Requests Playbook |
| Integrated with DSDR (Data Subject Deletion Request)? | Same as above |
| Retention and deletion timelines defined? | Data Retention Privacy Playbook |
| Available to regional (non-US) clusters or cross-cluster? | Data Residency Playbook |

---

## 8. Accessibility: UE Design Checklist

- [ ] U1. Text/background contrast >= 4.5:1
- [ ] U2. Color not sole information carrier
- [ ] U3. Meaningful page/dialog titles
- [ ] U4. Descriptive headings, labels, controls
- [ ] U5. Descriptive link text
- [ ] U6. Consistent identification of same-function components
- [ ] U7. Labels/instructions for user input
- [ ] U8. Auto-detected input errors described in text
- [ ] U9. Time limits adjustable/removable (except real-time)
- [ ] U10. Moving/blinking/scrolling content can be paused
- [ ] U11. Non-animated alternative for animated info
- [ ] U12. No flashing > 3Hz (web) / 2Hz (desktop/mobile)
- [ ] U13. CAPTCHA accessible to visually impaired

---

## 9. Accessibility: Programming Checklist

- [ ] P1. All controls keyboard/virtual-keyboard accessible
- [ ] P2. No keyboard trap
- [ ] P3. Visible focus outline on keyboard/screen-reader navigation
- [ ] P4. Logical focus order
- [ ] P5. Consistent screen-reader audio feedback for same-function components
- [ ] P6. Descriptive screen-reader text on all controls
- [ ] P7. Input labels announced on focus
- [ ] P8. User input announced on keystroke/choice
- [ ] P9. Operations announced with meaningful text (e.g., "recording stopped")
- [ ] P10. Auto-detected errors announced by screen reader
- [ ] P11. Programmatic UI changes announced by screen reader
