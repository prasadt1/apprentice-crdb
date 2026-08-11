from apprentice_crdb.grader import result_signature, signatures_match


def test_signature_ignores_row_order() -> None:
    cols = ["region", "revenue_cents"]
    a = result_signature(cols, [("AMER", 1), ("EMEA", 2)])
    b = result_signature(cols, [("EMEA", 2), ("AMER", 1)])
    assert signatures_match(a, b)


def test_signature_detects_value_change() -> None:
    cols = ["region", "revenue_cents"]
    a = result_signature(cols, [("AMER", 1)])
    b = result_signature(cols, [("AMER", 2)])
    assert not signatures_match(a, b)
