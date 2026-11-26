
"""Validation tests for the synthetic POC dataset."""

VALID_LABELS = {"EXPOSURE", "NON_EXPOSURE"}
VALID_SOURCES = {"ADMIN", "GENERATED", "VERIFIED"}


def test_train_dataset_structure(train_data):
    seen_codes = set()
    seen_example_ids = set()

    for filename, data in train_data.items():
        assert isinstance(data.get("secret"), dict), filename
        secret = data["secret"]

        for field in ("code", "name", "description"):
            assert isinstance(secret.get(field), str), (filename, field)
            assert secret[field].strip(), (filename, field)

        assert secret["code"] not in seen_codes
        seen_codes.add(secret["code"])

        policy = secret.get("policy")
        assert isinstance(policy, dict), filename

        for field in ("prohibited_details", "permitted_descriptions"):
            values = policy.get(field)
            assert isinstance(values, list) and values, (filename, field)
            assert all(isinstance(v, str) and v.strip() for v in values)

        examples = secret.get("examples")
        assert isinstance(examples, list) and examples, filename

        for example in examples:
            assert isinstance(example, dict), filename

            example_id = example.get("fixture_id")
            assert isinstance(example_id, str) and example_id.strip()
            assert example_id not in seen_example_ids
            seen_example_ids.add(example_id)

            assert isinstance(example.get("text"), str)
            assert example["text"].strip()

            assert example.get("label") in VALID_LABELS
            assert example.get("source") in VALID_SOURCES


VALID_DECISIONS = {"ALLOW", "REDACT", "BLOCK"}
VALID_PII_TYPES = {"EMAIL", "NATIONAL_ID", "CREDIT_CARD"}


def test_eval_dataset_structure(eval_data):
    seen_case_ids = set()

    for filename, data in eval_data.items():
        cases = data.get("cases")
        assert isinstance(cases, list) and cases, filename

        for case in cases:
            assert isinstance(case, dict), filename

            case_id = case.get("case_id")
            assert isinstance(case_id, str) and case_id.strip()
            assert case_id not in seen_case_ids, case_id
            seen_case_ids.add(case_id)

            assert isinstance(case.get("text"), str)
            assert case["text"].strip(), case_id

            assert case.get("expected_decision") in VALID_DECISIONS


def test_single_secret_eval_structure(eval_data, train_data):
    train_codes = {
        data["secret"]["code"]
        for data in train_data.values()
    }

    for filename, data in eval_data.items():
        if not filename.startswith("ss"):
            continue

        secret_code = data.get("secret_code")
        assert secret_code in train_codes, filename

        for case in data["cases"]:
            assert case.get("expected_label") in VALID_LABELS


def test_multi_secret_eval_structure(eval_data, train_data):
    data = eval_data["multi_secret_eval"]

    train_codes = {
        item["secret"]["code"]
        for item in train_data.values()
    }

    for case in data["cases"]:
        expected_codes = case.get("expected_secret_codes")

        assert isinstance(expected_codes, list)
        assert len(expected_codes) == len(set(expected_codes))
        assert all(code in train_codes for code in expected_codes)

        if case["expected_decision"] == "BLOCK":
            assert expected_codes


def test_pii_eval_structure(eval_data):
    data = eval_data["pii_eval"]

    for case in data["cases"]:
        expected_types = case.get("expected_pii_types")

        if case["expected_decision"] in {"REDACT", "BLOCK"}:
            assert isinstance(expected_types, list)
            assert expected_types

        if expected_types is not None:
            assert isinstance(expected_types, list)
            assert len(expected_types) == len(set(expected_types))
            assert all(
                pii_type in VALID_PII_TYPES
                for pii_type in expected_types
            )
