from __future__ import annotations

import re
import uuid

from .models import ASRWord, ClaimDossier, ClaimEvent, ClaimFact, EvidenceLink, ReviewStatus


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _words_for_span(text: str, words: list[ASRWord], start: int, end: int) -> tuple[float | None, float | None, str, str | None]:
    cursor = 0
    selected: list[ASRWord] = []
    for word in words:
        token = word.text.strip()
        position = text.lower().find(token.lower(), cursor)
        if position < 0:
            continue
        token_end = position + len(token)
        if token_end > start and position < end:
            selected.append(word)
        cursor = token_end
    if not selected or any(word.start is None or word.end is None for word in selected):
        return None, None, "missing", "Aucune frontière audio fiable fournie par l’ASR."
    return selected[0].start, selected[-1].end, "high", None


def _evidence(text: str, words: list[ASRWord], match: re.Match[str]) -> EvidenceLink:
    start, end, quality, note = _words_for_span(text, words, match.start(), match.end())
    return EvidenceLink(text_start=match.start(), text_end=match.end(), audio_start=start, audio_end=end, quality=quality, note=note)


def _fact(text: str, words: list[ASRWord], field: str, label: str, match: re.Match[str], value: str, method: str = "context_rules") -> ClaimFact:
    return ClaimFact(id=f"fact_{uuid.uuid4().hex[:10]}", field=field, label=label, value=_norm(value), extraction_method=method, evidence_text=match.group(0).strip(), evidence=_evidence(text, words, match), verification_state=ReviewStatus.needs_attention if _evidence(text, words, match).quality == "missing" else ReviewStatus.unreviewed)


def extract_claim(text: str, words: list[ASRWord], language: str | None, privacy_policy: str = "INTERNAL_CLAIM_REVIEW") -> ClaimDossier:
    """Conservative rule-based claim extraction. Missing values stay explicit."""
    facts: list[ClaimFact] = []
    timeline: list[ClaimEvent] = []
    languages = {"fr", "en", "ar"}
    if language not in languages:
        return ClaimDossier(privacy_policy=privacy_policy, missing_information=["Langue non supportée ou non confirmée", "Type d’incident", "Date/heure", "Lieu"])

    patterns: list[tuple[str, str, str]] = [
        ("incident_type", "Type d’incident", r"\b(accident|collision|accrochage|sinistre|vol|accident de voiture|car accident|crash|collision|theft)\b"),
        ("incident_date", "Date de l’incident", r"\b(?:le\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|hier|aujourd'hui|yesterday|today)\b"),
        ("incident_time", "Heure de l’incident", r"\b(?:à|vers|at|around)\s+(\d{1,2}(?:h|:\d{2})\s*\d{0,2})"),
        ("location", "Lieu de l’incident", r"\b(?:à|au|dans|sur|at|on)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{2,50}?)(?=\s+(?:avec|près|sur|vers|le|la|un|une|et|immatriculée|immatriculee)\b|[,.!?]|$)"),
        ("damage", "Dommages déclarés", r"\b(?:dégâts|dommages|damage|damaged|choc sur|impact sur)\s*[:：]?(?:sont|concernent|pour)?\s*([^.!?]{3,120})"),
        ("repair_estimate", "Estimation des réparations", r"\b(?:estimation|estim(?:é|ée|és|ées)|coût|montant|estimate|cost|repairs?|réparations?(?:\s+(?:sont|are))?(?:\s+estim(?:é|ée|és|ées))?)\s*(?:est|sont|is)?\s*(?:à|de|of)?\s*([\d\s.,]+\s*(?:€|euros?|EUR|dollars?|USD|MAD|DH|dirhams?)?)"),
        ("vehicles_count", "Nombre de véhicules", r"\b(\d+)\s+(?:véhicules?|voitures?|cars?|vehicles?)\b"),
        ("injuries", "Blessures mentionnées", r"\b(?:blessé|blessure|blessures|injured|injury|injuries)\b[^.!?]{0,100}"),
        ("witnesses", "Témoins mentionnés", r"\b(?:témoin|témoins|witness|witnesses)\b[^.!?]{0,100}"),
        ("police_report", "Rapport de police", r"\b(?:police|gendarmerie|rapport de police|police report)\b[^.!?]{0,100}"),
    ]
    for field, label, pattern in patterns:
        match = re.search(pattern, text, flags=re.I | re.UNICODE)
        if not match:
            continue
        value = match.group(1) if match.lastindex else match.group(0)
        facts.append(_fact(text, words, field, label, match, value))

    for match in re.finditer(r"\b(?:ensuite|puis|après|later|then|after)\s+([^.!?]{3,120})", text, flags=re.I):
        audio_start, audio_end, quality, note = _words_for_span(text, words, match.start(), match.end())
        timeline.append(ClaimEvent(id=f"event_{uuid.uuid4().hex[:10]}", label="Étape rapportée", description=_norm(match.group(1)), relative_time=match.group(0).split()[0], evidence_text=match.group(0).strip(), evidence=EvidenceLink(text_start=match.start(), text_end=match.end(), audio_start=audio_start, audio_end=audio_end, quality=quality, note=note), uncertainty="relative"))
    if facts:
        first = facts[0]
        summary = "; ".join(f"{fact.label}: {fact.value}" for fact in facts[:4])
    else:
        summary = None
    required = {"incident_type": "Type d’incident", "incident_date": "Date/heure de l’incident", "location": "Lieu de l’incident"}
    missing = [label for field, label in required.items() if not any(fact.field == field for fact in facts)]
    contradictions: list[str] = []
    amounts = re.findall(r"\b\d[\d\s.,]*\s*(?:€|euros?|EUR)\b", text, flags=re.I)
    if len({re.sub(r"\D", "", amount) for amount in amounts}) > 1:
        contradictions.append("Plusieurs montants de réparation ont été mentionnés ; vérification humaine requise.")
    dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    if len(set(dates)) > 1:
        contradictions.append("Plusieurs dates absolues ont été mentionnées ; elles ne sont pas résolues automatiquement.")
    return ClaimDossier(incident_summary=summary, facts=facts, timeline=timeline, missing_information=missing, contradictions=contradictions, privacy_policy=privacy_policy)

