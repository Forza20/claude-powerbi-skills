# PII Pattern Reference (DA/EN)

Substring patterns (case-insensitive) used by `parse_pbip.py` to flag column names as potential PII candidates. Matches are heuristic — always review manually.

## Patterns

### Contact
- `email`, `e-mail`, `mail`
- `phone`, `telefon`, `mobil`, `tlf`

### National identifiers
- `cpr` (Danish personal ID)
- `ssn` (US social security)
- `passport`, `pas`
- `cvr` (Danish company ID), `vat`

### Names
- `name`, `navn`
- `fornavn`, `efternavn` (DA first/last name)
- `firstname`, `lastname`, `fullname`

### Addresses
- `address`, `adresse`
- `postnr`, `zip`, `postal`
- `city`, `by`

### Birth
- `dob`, `birth`, `birthday`
- `fødsel`, `fodsel`

### Online identifiers
- `ip`, `ipaddress`
- `deviceid`, `userid`

### Financial
- `iban`, `account`
- `kontonummer`, `kortnummer`, `cardnumber`
- `salary`, `løn`, `lon`
- `income`, `indkomst`

### Sensitive attributes (GDPR special categories)
- `gender`, `køn`, `kon`
- `ethnic`, `religion`
- `nationality`, `nationalitet`

## Notes on false positives

Common false positives to watch for:
- `category_name`, `table_name`, `column_name` — matches `name` but not PII
- `company_name` — edge case; often not PII but can be in B2C contexts
- `city` in geographic dimension tables (city = master data, not personal)
- `email_template`, `email_subject` — matches `email` but not personal data

When presenting PII findings, always caveat: "potential PII" or "PII candidate" — never assert a column IS PII without domain context.
