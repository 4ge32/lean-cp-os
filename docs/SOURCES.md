# Source and rights record

No specification PDF, extracted full text or ATK2 code is distributed here. Metadata and the project's own requirement statements are in `trace/`. Original checks below were made on 2026-10-12. On 2026-10-13 the exact pinned OSEK PDF was obtained from [a fixed GitHub mirror revision](https://github.com/syfchao/osek_v2-2-3/blob/e70f1eba79d8864f01e45095a3b97d97d63569ba/doc/os223.pdf); its SHA256 matches the existing academic-mirror hash. Basic-task APIs §13.2.3.1–6, queue ordering §§4.3/4.5, ISR scheduling §4.6.1 and the call-context table §12.2.2 were reviewed for the expanded implementation.

| Source | Fixed version / anchor | Role and verification |
|---|---|---|
| OSEK/VDX Operating System | 2.2.3, 2005-02-17; §§4.2.2, 4.5, 4.6.1, 13.2.3.1/.2/.5/.6 | Primary M0 behavior source. Official-release PDF read via academic mirror; bytes hashed. Section references used because this document does not assign AUTOSAR-style IDs to these services. |
| ATK2 external specification, ATK2-0010 | 1.2.2, 2017-03-24; §§2.5, 3.9.4/.5/.8/.9 | Reference interpretation/design. Official PDF read and hashed. Verified COS IDs remain ATK2 document identifiers. |
| AUTOSAR CP OS (historical evidence) | R24-11; §7.1.2, p36, SWS_Os_00001 | Superseded proposal; retained for LCPO-012 provenance. Official indexed section checked. Complete PDF and hash still unavailable due server timeout/502. Full compliance mapping has not been done. |

Source URLs and exact hashes are in [sources.json](../trace/sources.json). The OSEK historical publisher endpoint is `http://portal.osek-vdx.org/files/pdf/specs/os223.pdf`; the retrieved publisher-authored document is hosted at [IRISA](https://www.irisa.fr/alf/downloads/puaut/TPNXT/images/os223.pdf). Its cover identifies it as the official release; mirror bytes are not asserted identical to a separately obtained publisher copy.

The [ATK2 project page](https://www.toppers.jp/atk2.html) states its external specification is based on **AUTOSAR Release 4.0 Revision 3**. That historical basis is not the selected R25-11 target. ATK2's added clarifications and implementation choices are reference-design decisions, not automatically normative AUTOSAR requirements. This project independently chooses the three-task model, derived task states, scalar ABI and host nonlocal dispatcher.

## Current specification policy

The user-approved current deliverable is the **OSEK OS 2.2.3 single-core Basic Task subset**, followed by actual task execution under QEMU. The larger AUTOSAR target below is retained for future mapping; it does not replace the pinned OSEK clauses used to implement and explain this stage.

The compatibility target is **AUTOSAR Classic Platform OS R25-11**, following the user's preference for the newest officially released specification. On 2026-10-12 the [official CP page](https://www.autosar.org/standards/classic-platform) lists R25-11 as Current Release, and the [official announcement](https://www.autosar.org/news-events/detail/release-r25-11-is-now-available) records its availability on 2025-12-01. This supersedes the earlier R24-11 proposal.

OS PDF retrieval still times out. R25-11 document bytes, rights notice, sections and requirement IDs remain **unverified**. Existing `SWS_Os_00001` / §7.1.2 evidence belongs only to R24-11; LCPO-012 retains that provenance and must not be relabelled as R25-11 evidence. M0's checked OSEK-based behavior and proofs do not establish R25-11 compatibility.

OSEK 2.2.3 remains the foundational behavior reference and ATK2 remains the historical design reference. Implement the small subset first, but review its requirements against R25-11 when the document becomes available. For future formal releases, review deltas, rights and hashes, update requirement mappings, and rerun affected proofs/tests in a new commit. Each commit pins a concrete version; no floating `latest` or automatic compliance upgrade. Pending releases are not adopted as released standards.

## Rights decisions

- OSEK 2.2.3 cover reserves reproduction subject to written permission. Neither original text nor an extracted/translated copy is committed.
- ATK2-0010 p.i provides its own document conditions, requiring copyright/conditions/disclaimer preservation and modification marking. It explicitly does not license AUTOSAR IP. No copy is redistributed.
- [TOPPERS license](https://www.toppers.jp/license.html) and [AUTOSAR usage notice](https://www.toppers.jp/autosar.html) were checked. An implementation's exact headers must be reviewed before reuse; this project does not copy ATK2 implementation code.
- [AUTOSAR official CP guidance](https://www.autosar.org/standards/classic-platform) refers commercial exploitation to partnership. The exact R24-11 and R25-11 OS disclaimers are not yet fully retrieved, so its detailed reuse conditions are unresolved; no spec material is bundled. This record is an engineering provenance policy, not a legal opinion or a commercial-use clearance.
- **Project source license is undecided.** No MIT/Apache/GPL permission is implicitly selected by a public repository request. Only original project files and generated evidence are intended for publication.
- Lean is an external tool dependency obtained from the official pinned release. The full tool distribution is not vendored. Binary evidence includes runtime components; see the distribution's [LICENSE](https://github.com/leanprover/lean4/blob/v4.19.0/LICENSE) and third-party notices before redistribution. Runtime license notices must accompany packaged binary evidence.

## Reference implementation inspected

ATK2-SC1 **1.4.2** (official 2017-03-24 archive) is pinned separately from document version 1.2.2. Archive and `kernel/task_manage.c` hashes are recorded. The activation limit and termination dispatch paths plus the actual file license header were inspected. Its successful termination uses a distinct discard-and-dispatch path, with normal return reserved for errors; M0 uses this as design context without copying implementation text. ATK2 resource/interrupt checks are intentionally deferred here.
