from app.utils import compute_age_group

def test_compute_age_group_child():
    assert compute_age_group(5) == "child"

def test_compute_age_group_adult():
    assert compute_age_group(30) == "adult"

def test_compute_age_group_senior():
    assert compute_age_group(80) == "senior"

def test_compute_age_group_none():
    assert compute_age_group(None) == "unknown"

def test_compute_age_group_invalid():
    assert compute_age_group("abc") == "unknown"
