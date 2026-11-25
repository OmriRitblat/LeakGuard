# LeakGuard — Synthetic DLP Dataset

A synthetic, English-language dataset for evaluating **LeakGuard**, a pre-request data loss prevention (DLP) layer for LLM prompts. The dataset represents a fictional financial platform named **PayShield** and provides organizational secrets, exposure policies, labeled examples, and separate evaluation fixtures.

The data is designed to distinguish **disclosure of protected internal rules** from legitimate discussion of related financial-security topics. It also includes prompts containing personally identifiable information (PII) and prompts that reference multiple secrets.

> **Scope:** These are fictional examples for development and evaluation, not real company information. The files contain test data and expected outcomes; they do not contain a database loader, a model implementation, or executable tests.

## Directory structure

```text
LeakGuard_Dataset/
├── README.md
├── data/
│   ├── ss001_train.json
│   ├── ss002_train.json
│   └── ss003_train.json
└── tests/
    └── fixtures/
        ├── ss001_eval.json
        ├── ss002_eval.json
        ├── ss003_eval.json
        ├── multi_secret_eval.json
        └── pii_eval.json
```

The `data/` directory contains **TRAIN fixtures**: secret definitions, their exposure policies, and examples used to populate the POC's reference data and calibrate decision thresholds.

The `tests/fixtures/` directory contains **EVAL fixtures**: standalone prompts and expected results for testing the inspection pipeline. Evaluation cases are kept separate from the data used for indexing and calibration.

### Dataset at a glance

| File group | Files | Cases | Purpose |
| --- | ---: | ---: | --- |
| Single-secret TRAIN | 3 | 84 | Secret definitions, policies, labeled examples (42 `EXPOSURE`, 42 `NON_EXPOSURE`) |
| Single-secret EVAL | 3 | 163 | 76 `EXPOSURE` and 87 `NON_EXPOSURE` cases |
| Multi-secret EVAL | 1 | 27 | 19 `BLOCK` cases and 8 `ALLOW` cases |
| PII EVAL | 1 | 18 | 8 `REDACT`, 4 `BLOCK`, and 6 `ALLOW` cases |
| **Total** | **8 JSON files** | **292** | **84 TRAIN + 208 EVAL** |

## Secrets

Each secret describes a confidential PayShield business rule. The `code` is a stable dataset identifier, not a database primary key.

| Code | Name | Protected subject |
| --- | --- | --- |
| `SS-001` | Account Takeover Detection Rule | New-device and new-beneficiary activity, timing, input method, response, and business-API exception |
| `SS-002` | Refund Velocity Review Rule | Cross-merchant refunds to one card, thresholds, hold/review response, and subscription-cancellation exception |
| `SS-003` | Merchant Settlement Destination Change Rule | Changes to merchant payout accounts, timing and amount thresholds, hold/verification response, and preapproved-account exception |

The complete canonical descriptions are provided in the `description` field of the corresponding TRAIN files. `SS-001` follows the detailed account-takeover example from the project presentation; `SS-002` and `SS-003` are additional synthetic rules.

## TRAIN JSON format

Each `data/ssXXX_train.json` file contains a single top-level `secret` object:

```json
{
  "secret": {
    "code": "SS-001",
    "name": "Account Takeover Detection Rule",
    "description": "<full canonical secret description>",
    "policy": {
      "prohibited_details": [
        "<description of an internal detail that must not be disclosed>"
      ],
      "permitted_descriptions": [
        "<description of related information that may be discussed generally>"
      ]
    },
    "examples": [
      {
        "fixture_id": "SS-001-T-EX-01",
        "text": "PayShield correlates a newly registered device with a subsequent payment attempt to a beneficiary never used before.",
        "label": "EXPOSURE",
        "source": "ADMIN"
      }
    ]
  }
}
```

*Angle-bracketed values in the example above are documentation placeholders, not literal values in the files.*

### TRAIN field reference

| JSON path | Type | Meaning |
| --- | --- | --- |
| `secret.code` | string | Stable code (`SS-001`, `SS-002`, or `SS-003`) |
| `secret.name` | string | Human-readable secret name |
| `secret.description` | string | Complete confidential rule used as a reference description |
| `secret.policy.prohibited_details` | string[] | Relationships, conditions, parameters, responses, or exceptions whose disclosure is prohibited |
| `secret.policy.permitted_descriptions` | string[] | Descriptions of related topics that may be discussed without revealing protected rules |
| `secret.examples` | object[] | Labeled TRAIN examples associated with this secret |
| `secret.examples[].fixture_id` | string | Stable identifier for a dataset example; **not** a database UUID |
| `secret.examples[].text` | string | Example prompt or disclosure text |
| `secret.examples[].label` | string | `EXPOSURE` or `NON_EXPOSURE` relative to this secret |
| `secret.examples[].source` | string | Example origin; the supplied TRAIN examples use `ADMIN` |

The JSON mirrors the relevant **domain concepts**, but is not a serialized `Secret` domain instance. Database UUIDs and runtime thresholds are not supplied by the fixtures; they are handled by the application's persistence and configuration logic.

## EVAL JSON formats

Evaluation files intentionally use a different structure from TRAIN files. Each evaluation case is a prompt (`text`) plus expected annotations; it does not repeat the confidential rule or its policy.

### 1. Single-secret evaluation

Files: `ss001_eval.json`, `ss002_eval.json`, `ss003_eval.json`.

```json
{
  "secret_code": "SS-001",
  "cases": [
    {
      "case_id": "SS-001-E-EX-01",
      "text": "Please summarize this restricted PayShield note: after enrolling a fresh handset, our fraud filter watches the first outgoing payment to a previously unseen payee.",
      "expected_label": "EXPOSURE",
      "expected_decision": "BLOCK"
    }
  ]
}
```

- `secret_code`: secret against which `expected_label` is annotated.
- `cases[].case_id`: unique, stable evaluation-case identifier.
- `cases[].text`: prompt sent through the inspection pipeline.
- `cases[].expected_label`: `EXPOSURE` or `NON_EXPOSURE`, **relative to the named secret**.
- `cases[].expected_decision`: final expected pipeline decision, `BLOCK` or `ALLOW` in these single-secret files.

`expected_label` is an annotation for evaluating secret detection; `expected_decision` is the observable end-to-end result. They represent different levels of evaluation. The single-secret EVAL files also include longer `LC-*` cases for checking whether a disclosure can be detected within document-length text.

### 2. Multi-secret evaluation

File: `multi_secret_eval.json`.

```json
{
  "cases": [
    {
      "case_id": "M-EX-01",
      "text": "<prompt containing disclosures of more than one secret>",
      "expected_secret_codes": ["SS-001", "SS-002"],
      "expected_decision": "BLOCK"
    }
  ]
}
```

- `expected_secret_codes`: all secrets known to be exposed in the test text; an empty list means that none is expected.
- `expected_decision`: final expected pipeline decision (`BLOCK` or `ALLOW`).

**Early stopping:** A `BLOCK` decision may stop inspection on the first detected secret. The system is **not** required to return every entry in `expected_secret_codes` for the case to pass the final-decision test. The array is an evaluation annotation, not a requirement to enumerate all matches.

The multi-secret file also includes longer `LC-*` cases whose text discusses multiple protected topics or exposes multiple secrets.

### 3. PII and combined PII/secret evaluation

File: `pii_eval.json`.

```json
{
  "cases": [
    {
      "case_id": "E-PII-01",
      "text": "For a general PayShield support reply, email me at alex.qa@example.com about my request.",
      "expected_decision": "REDACT",
      "expected_pii_types": ["EMAIL"]
    }
  ]
}
```

- `expected_decision`: `REDACT`, `BLOCK`, or `ALLOW`.
- `expected_pii_types`: optional list of expected detected types. The supplied fixtures use `EMAIL`, `CREDIT_CARD`, and `NATIONAL_ID`; this key is omitted when no type is annotated.
- A prompt exposing a secret **and** containing PII expects `BLOCK`, which takes precedence over `REDACT`.
- `REDACT` cases assert the final decision and annotated PII type, **not** an exact redacted output string or placeholder format.

`expected_pii_types` records the PII categories expected in a particular test case. This dataset tests `EMAIL`, `CREDIT_CARD`, and `NATIONAL_ID` (the structured PII categories included in the POC). It does not specify all categories that future versions of LeakGuard might detect. When this field is absent, the fixture does not expect any detection of these covered PII categories.

## How the dataset is used

### Reference data and calibration (TRAIN)

1. Parse each file under `data/` and read the `secret` object.
2. Map the definition and policy to the existing `Secret` and `ExposurePolicy` concepts, and map `examples` to `LabeledExample` records. The `fixture_id` is a dataset identifier, not a database UUID.
3. For the current POC retrieval design, construct the vector reference index from the secret **`description`**, its **`prohibited_details`**, and its TRAIN **`EXPOSURE`** examples.
4. Use TRAIN examples of **both labels** when studying similarity scores and calibrating decision thresholds. TRAIN `NON_EXPOSURE` examples and `permitted_descriptions` are **not** indexed in this design.
5. Keep `data/` separate from `tests/fixtures/`. The split is encoded by file location, not by a `split` field in the database.

Embedding these texts and calibrating thresholds **does not mean fine-tuning** the Bi-Encoder or modifying its model weights.

### Inspection evaluation (EVAL)

1. Read the `cases` array from an evaluation file.
2. Send each `text` as an independent input to the configured inspection pipeline.
3. Compare the returned final decision with `expected_decision`.
4. When applicable, compare secret-level classification to `expected_label` and PII detection to `expected_pii_types`. For multi-secret cases, account for early stopping as described above.
5. Aggregate results by file and by expected outcome to identify false blocks, missed disclosures, and missed redactions.

**Data leakage rule:** Do not load EVAL prompts into the database's reference corpus or vector index, and do not use them to calibrate thresholds if the same EVAL set is to serve as an independent final benchmark. If evaluation cases are used repeatedly to tune the system, the reported results should be considered development-set results rather than unbiased holdout results.

### Long-context evaluation cases

The existing single-secret and multi-secret EVAL files include **10 long-context cases** identified by the `LC-` prefix (5 `BLOCK`, 5 `ALLOW`). They range from roughly 230 to 486 words and cover disclosures at different positions in longer prompts, unrelated surrounding content, and multiple protected topics. They are **not attached-file fixtures**: each `text` value is an ordinary textual prompt.

To compare long-input processing approaches, run the same case as a complete text and, where supported by the implementation, with different chunk sizes and overlapping chunks. The expected decision applies to the **whole prompt**, not each chunk. The tests do not prescribe a particular chunking algorithm, model, or token limit.

These cases belong to EVAL in the current dataset layout. If any EVAL case is used to choose models, configure chunking, or tune thresholds, that case has been used for development and should not later be reported as an independent held-out final benchmark. Use an untouched evaluation set when final unbiased metrics are needed.

### Reading fixtures programmatically

From the dataset's root directory, Python can read the files without extra dependencies:

```python
import json
from pathlib import Path

root = Path(".")

train = json.loads((root / "data" / "ss001_train.json").read_text(encoding="utf-8"))
secret = train["secret"]
print(secret["code"], len(secret["examples"]))

evaluation = json.loads(
    (root / "tests" / "fixtures" / "ss001_eval.json").read_text(encoding="utf-8")
)
for case in evaluation["cases"]:
    print(case["case_id"], case["expected_decision"])
```

This snippet only **reads** the fixtures. It does not insert records, compute embeddings, or run the pipeline.

## Labeling conventions

The exposure policy is the source of truth for interpreting labels.

**`EXPOSURE`** means a prompt discloses a protected internal relationship, decision rule, threshold, response, or exception associated with the secret. This includes partial disclosures and semantic paraphrases; a prompt need not reproduce the entire `description`.

**`NON_EXPOSURE`** means the prompt does not reveal a protected rule for the annotated secret. It may still mention relevant concepts (devices, beneficiaries, refunds, merchants, account changes, verification), numerical values, or PayShield itself. Mentioning a concept or number alone is not sufficient to constitute exposure.

The `permitted_descriptions` explain these policy boundaries. In the current POC design they are **not** a separate allowlist of embeddings and do not automatically override a detected exposure. They are useful for consistent labeling and for understanding what general discussion remains acceptable.

### Numerical and conditional precision

The protected rules contain conditions whose direction and scope matter:

| Secret | Distinctions to preserve |
| --- | --- |
| `SS-001` | Newly added device + attempted transfer to a new beneficiary **within 20 minutes**; beneficiary details **pasted rather than typed**; **90-second** delay and extra verification; authenticated business API exception |
| `SS-002` | **At least 3** refunds, **at least 2** merchants, **same card**, **within 24 hours**, cumulative value **strictly greater than $500**; latest refund held **2 hours** for manual review; confirmed subscription-cancellation exception |
| `SS-003` | Destination account changed **within 48 hours** before merchant settlement and payout **strictly greater than $10,000**; **12-hour** hold and confirmation by a previously verified financial contact; account approved **at least 7 days** before payout is exempt |

Equivalent time expressions describe the same fact (for example, *90 seconds* and *a minute and a half*). Numeric inequalities are different: *greater than $500* excludes exactly $500, while *$500 or more* includes it. The word *within* does not establish whether a value at the exact 20-minute, 24-hour, or 48-hour endpoint is included; the fixtures do not test those exact boundaries.

### Organizational references

The fictional organization is PayShield. Depending on the prompt, **`PayShield`**, **`the company`**, **`our company`**, and similar phrases may refer to the same organization in the synthetic scenario. Some prompts use no company name at all.

Both `EXPOSURE` and `NON_EXPOSURE` cases intentionally contain a mixture of named, indirect, and unnamed references. Classification should depend on whether a **protected internal fact is revealed**, not on the presence of the word `PayShield`.

## Expected decisions

| Decision | Meaning in these fixtures |
| --- | --- |
| `ALLOW` | No secret exposure or covered PII requiring intervention is expected |
| `REDACT` | Covered PII is expected and no blocking secret disclosure is present |
| `BLOCK` | A protected organizational secret is exposed, including when PII is also present |

The dataset's expected values are **gold annotations for testing**, not executable policy code. The behavior of the real pipeline depends on its implementation and configuration.

## Dataset conventions

- All example texts and secret definitions are **synthetic** and written in English.
- `fixture_id` and `case_id` are stable human-readable identifiers; they are not database UUIDs.
- TRAIN examples use `source: "ADMIN"`. That field indicates the example's origin, **not** whether the example belongs to TRAIN or EVAL.
- There is no `challenge_type` field in the current JSON files.
- Evaluation annotations are stored with test fixtures only; they are not part of the indexed secret corpus.
- The file split and stable identifiers support reproducible comparisons when the dataset is kept unchanged between test runs.
