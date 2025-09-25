def test_repo_snapshot():
    from core.repo_index import repo_snapshot

    result = repo_snapshot(max_chars=1000)
    assert isinstance(result, str)
    assert len(result) <= 1000
