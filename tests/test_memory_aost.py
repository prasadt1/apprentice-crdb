from apprentice_crdb.memory import aost_literal


def test_aost_literal_strips_quotes_and_logical_counter() -> None:
    assert aost_literal("1786458556.062624000,0") == "1786458556.062624000"
    assert aost_literal("'1786458556.062624000'") == "1786458556.062624000"
    assert aost_literal("  1786458556.062624000  ") == "1786458556.062624000"
