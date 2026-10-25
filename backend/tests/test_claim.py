from backend.app.models import ASRWord
from backend.app.services_claim import extract_claim


def test_claim_facts_keep_evidence_and_missing_fields_explicit():
    text = "J'ai eu un accident hier à 18h à Paris. Les dégâts sont sur la portière."
    words = [ASRWord(id=str(index), text=token, start=index * 0.2, end=index * 0.2 + 0.15) for index, token in enumerate(text.split())]
    claim = extract_claim(text, words, "fr")
    assert any(fact.field == "incident_type" for fact in claim.facts)
    assert any(fact.field == "location" for fact in claim.facts)
    assert all(fact.evidence.audio_start is not None for fact in claim.facts)
    assert "Lieu de l’incident" not in claim.missing_information


def test_unsupported_language_is_not_presented_as_safe():
    claim = extract_claim("This is a test", [], "de")
    assert claim.facts == []
    assert "Langue non supportée ou non confirmée" in claim.missing_information


def test_automotive_demo_extracts_precise_date_location_and_estimate():
    text = "Le 12/05/2026 vers 18h, j'ai eu un accident à Casablanca avec ma Clio. Les réparations sont estimées à 8000 MAD."
    words = [ASRWord(id=str(index), text=token, start=index * 0.2, end=index * 0.2 + 0.15) for index, token in enumerate(text.split())]
    claim = extract_claim(text, words, "fr")
    values = {fact.field: fact.value for fact in claim.facts}
    assert values["incident_date"] == "12/05/2026"
    assert values["location"] == "Casablanca"
    assert values["repair_estimate"] == "8000 MAD"

