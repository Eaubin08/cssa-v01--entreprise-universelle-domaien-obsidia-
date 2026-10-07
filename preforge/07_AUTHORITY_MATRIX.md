# 07 — AUTHORITY MATRIX

Initial pre-forge authority profile.

| Capability | Initial status | Boundary |
|---|---|---|
| Read authorized source | ALLOW | source access policy |
| Parse / understand | ALLOW | non-authoritative |
| Classify | ALLOW | trace required |
| Link to case/match | ALLOW | uncertainty preserved |
| Detect deadline | ALLOW | provenance required |
| Remind | ALLOW | internal/no external commitment |
| Prepare draft | ALLOW | proposal only |
| Recommend action | ALLOW | proposal only |
| Send external message | HOLD | human validation |
| Modify official record | HOLD | human validation + adapter boundary |
| Submit declaration | HOLD/BLOCK | explicit permission required |
| Financial commitment | BLOCK by default | separate governed domain/policy |
| Sign/attest legally | BLOCK by default | human/legal authority |
| Override rule | BLOCK | no domain authority |
| Kernel mutation | BLOCK | out of scope |

KX108 remains the authority boundary for governed admission.
Binder/adapter boundaries remain separate from KX108 decision.
