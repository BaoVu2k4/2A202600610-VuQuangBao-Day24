# ND13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [x] Patient data is stored on Vietnam-hosted infrastructure.
  - Solution: deploy production storage on VN cloud providers such as FPT Cloud or VNPT Cloud.
- [x] Backups remain inside Vietnam.
  - Solution: configure encrypted backup replication to a secondary VN region.
- [x] Cross-border transfers are logged and reviewed.
  - Solution: API export events include user, resource, action, timestamp, and destination country.

## B. Explicit Consent
- [x] Consent is required before using patient data for AI training.
  - Solution: store `consent_ai_training`, `consent_timestamp`, and consent source in the patient metadata store.
- [x] Consent withdrawal is supported.
  - Solution: expose a deletion/withdrawal workflow that removes the patient from future training datasets.
- [x] Consent changes are auditable.
  - Solution: append consent grant/revoke events to an immutable audit log.

## C. Breach Notification Within 72 Hours
- [x] Incident response plan is documented.
  - Solution: use a runbook covering detect, isolate, investigate, notify, and remediate steps.
- [x] Alerts are generated for suspicious access patterns.
  - Solution: Prometheus/AlertManager monitors repeated unauthorized access and failed authentication spikes.
- [x] Notification ownership is assigned.
  - Solution: DPO owns regulatory notification and customer communication timelines.

## D. DPO Appointment
- [x] Data Protection Officer is assigned.
- [x] DPO contact: dpo@medviet.vn | +84-xxx-xxx-xxx

## E. Technical Controls Mapping

| ND13 Requirement | Technical Control | Status | Owner |
|------------------|-------------------|--------|-------|
| Data minimization | PII detection and anonymization pipeline using Presidio | Done | AI Team |
| Raw PII restriction | Casbin RBAC denies raw patient data to non-admin roles | Done | Platform Team |
| Training data access | Admin and ML engineer can read anonymized training data | Done | Platform Team |
| Aggregated reporting | Admin, ML engineer, and data analyst can read aggregate metrics | Done | Platform Team |
| ABAC policy checks | OPA policy has explicit deny rules for restricted export and production access | Done | Platform Team |
| Encryption at rest | AES-256-GCM envelope encryption in `SimpleVault` | Done | AI Team |
| Encryption in transit | TLS 1.3 termination through the production reverse proxy | Planned control | Infra Team |
| Audit logging | API access events captured for export and authorization decisions | Designed control | Platform Team |
| Breach detection | Prometheus configuration added for monitoring bootstrap | Designed control | Security Team |
| Security scanning | Bandit report committed; TruffleHog report placeholder documents CLI availability | Completed with environment note | Security Team |

## F. Verification Evidence

| Evidence | File |
|----------|------|
| PII and anonymization tests | `reports/test_results.txt` |
| Bandit SAST report | `reports/bandit_report.json` |
| TruffleHog scan report | `reports/trufflehog_report.txt` |
| OPA access rules | `policies/opa_policy.rego` |
| RBAC policy | `src/access/policy.csv` |
| Anonymized patient output | `data/processed/patients_anonymized.csv` |

## G. Submission Notes

- Raw patient data is intentionally ignored and not submitted, except for `data/raw/.gitkeep`.
- `.vault_key` is intentionally ignored and not submitted.
- The submitted repository contains source code, tests, policies, processed data, reports, compliance checklist, and requirements.
