from services.quality import validate_caption


def test_accepts_a_fresh_caption():
    assert validate_caption("आजको plan: भोलिदेखि पढ्ने 😄", ["हिजोको joke फरक थियो"]) is True


def test_rejects_near_duplicate_caption():
    previous = ["Exam को तयारी भोलिदेखि सुरु गर्छु"]
    try:
        validate_caption("Exam को तयारी भोलिदेखि सुरु गर्छु!", previous)
    except ValueError as exc:
        assert "similar" in str(exc).lower()
    else:
        raise AssertionError("Expected duplicate caption to be rejected")


def test_rejects_too_short_caption():
    try:
        validate_caption("haha", [])
    except ValueError as exc:
        assert "short" in str(exc).lower()
    else:
        raise AssertionError("Expected short caption to be rejected")
