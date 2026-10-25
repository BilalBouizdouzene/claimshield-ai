from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path

from .models import CustomerCandidate, DetectedEntity, MatchStatus, PolicyCandidate


def _normalized(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "", ascii_value.upper())


def _masked_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return f"{digits[:2]}******{digits[-2:]}" if len(digits) >= 6 else "••••••"


def _masked_email(value: str | None) -> str | None:
    if not value or "@" not in value:
        return None
    local, domain = value.split("@", 1)
    return f"{local[:1]}•••@{domain}"


def match_claim(text: str, entities: list[DetectedEntity], db_path: Path) -> tuple[list[CustomerCandidate], list[PolicyCandidate]]:
    """Return explainable candidates only; never confirms identity automatically."""
    entity_values: dict[str, list[str]] = {}
    for entity in entities:
        entity_values.setdefault(entity.category, []).append(entity.text)
    phone_values = {_normalized(value) for value in entity_values.get("PHONE_NUMBER", [])}
    policy_values = {_normalized(value) for value in entity_values.get("POLICY_NUMBER", [])}
    plate_values = {_normalized(value) for value in entity_values.get("LICENSE_PLATE", [])}
    vin_values = {_normalized(value) for value in entity_values.get("VIN", [])}
    name_values = {_normalized(value) for value in entity_values.get("PERSON", [])}

    customers: list[CustomerCandidate] = []
    policies: list[PolicyCandidate] = []
    with sqlite3.connect(db_path) as connection:
        customer_rows = connection.execute(
            "SELECT customer_id, first_name, last_name, phone, email, customer_status FROM customers"
        ).fetchall()
        policy_rows = connection.execute(
            """SELECT p.policy_id, p.policy_number, p.insurance_product, p.policy_status,
                      p.effective_start, p.effective_end, p.customer_id,
                      c.first_name || ' ' || c.last_name, p.assigned_vehicle_id,
                      v.registration_number, v.manufacturer || ' ' || v.model,
                      v.vin
               FROM policies p JOIN customers c ON c.customer_id = p.customer_id
               LEFT JOIN vehicles v ON v.vehicle_id = p.assigned_vehicle_id"""
        ).fetchall()

    for row in customer_rows:
        customer_id, first_name, last_name, phone, email, status = row
        full_name = f"{first_name} {last_name}"
        reasons: list[str] = []
        identifiers: list[str] = []
        if _normalized(phone) in phone_values:
            reasons.append("Numéro de téléphone exact")
            identifiers.append("PHONE_NUMBER")
        if _normalized(full_name) in name_values or _normalized(last_name) in name_values:
            reasons.append("Nom prononcé correspondant")
            identifiers.append("PERSON")
        if not reasons:
            continue
        customers.append(CustomerCandidate(
            customer_id=customer_id,
            full_name=full_name,
            customer_status=status,
            match_status=MatchStatus.match_candidate,
            match_reasons=reasons,
            matched_identifiers=identifiers,
            phone_masked=_masked_phone(phone),
            email_masked=_masked_email(email),
        ))

    for row in policy_rows:
        policy_id, policy_number, product, status, start, end, customer_id, customer_name, vehicle_id, registration, vehicle_label, vin = row
        reasons: list[str] = []
        if _normalized(policy_number) in policy_values:
            reasons.append("Numéro de contrat exact")
        if _normalized(registration) in plate_values:
            reasons.append("Immatriculation exacte")
        if _normalized(vin) in vin_values:
            reasons.append("VIN exact")
        customer_match = next((candidate for candidate in customers if candidate.customer_id == customer_id), None)
        if customer_match:
            reasons.append("Client candidat associé")
        if not reasons:
            continue
        policies.append(PolicyCandidate(
            policy_id=policy_id,
            policy_number=policy_number,
            insurance_product=product,
            policy_status=status,
            effective_start=start,
            effective_end=end,
            customer_id=customer_id,
            customer_name=customer_name,
            vehicle_id=vehicle_id,
            vehicle_label=vehicle_label,
            registration_number=registration,
            match_status=MatchStatus.match_candidate,
            match_reasons=reasons,
        ))

    if len(customers) > 1:
        customers = [candidate.model_copy(update={"match_status": MatchStatus.multiple_candidates}) for candidate in customers]
    if len(policies) > 1:
        policies = [candidate.model_copy(update={"match_status": MatchStatus.multiple_candidates}) for candidate in policies]
    return customers, policies
