from apprentice_crdb.embeddings import DIM, MockHasher


def test_mock_hasher_is_1024d_and_normalized() -> None:
    assert DIM == 1024
    vec = MockHasher().embed("fiscal year starts in february")
    assert len(vec) == 1024
    assert abs(sum(x * x for x in vec) - 1.0) < 1e-6
