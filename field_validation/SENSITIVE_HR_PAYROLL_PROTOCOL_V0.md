# F3E — SENSITIVE HR / PAYROLL EVIDENCE PROTOCOL V0

Status: MANUAL PRIVACY GATE / RAW PAYSLIPS FORBIDDEN IN PUBLIC REPO

A payslip could help answer a few narrow organizational questions, but it is far more sensitive than necessary for most of F3E.

## What a payslip could legitimately validate

Potentially useful facts:

- employing legal entity;
- employment/contract category if shown;
- pay period/frequency;
- presence of expense/allowance lines;
- broad employer-cost structure if voluntarily shared and needed.

## Better than a raw payslip

Prefer a manually abstracted record:

```text
role_id
employing_entity
contract_type
weekly_hours_or_range
gross_pay_band_optional
expense_categories
mileage_reimbursement_present
meal_or_travel_allowance_present
pay_period
source_validated_by_staff_member = true
```

Exact salary is not required for the Administration proof.

## Never commit raw payroll documents to this public repository

If a real document is voluntarily supplied for validation, process it outside the repo and redact at minimum:

- full name;
- home address;
- date/place of birth;
- social-security number;
- employee/payroll identifier;
- IBAN/bank details;
- tax-withholding details;
- health/leave information;
- garnishments or other private deductions;
- signature;
- QR/bar codes or document identifiers.

The raw file must not be committed.

## Runtime boundary

Payroll and personal financial records remain:

`FINANCIAL_DATA -> MANUAL_PRIVACY_REVIEW -> PRE_RUNTIME_BLOCK`

F3E contains a synthetic payroll event proving this boundary.
