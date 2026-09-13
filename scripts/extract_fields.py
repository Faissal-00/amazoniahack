from __future__ import annotations

import re
from typing import Any


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def all_text(ocr_results: list[dict[str, Any]]) -> str:
    return "\n".join(
        normalize_text(item["text"])
        for item in ocr_results
        if item.get("text")
    )


def find_text(
    ocr_results: list[dict[str, Any]],
    pattern: str,
    flags: int = re.IGNORECASE,
) -> str | None:
    text = all_text(ocr_results)

    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def extract_document_type(
    ocr_results: list[dict[str, Any]],
) -> tuple[str, float]:

    text = all_text(ocr_results).upper()

    if "AUTO DE INFRACAO" in text:
        return "infraction_notice", 0.99

    if "AUTO DE EMBARGO" in text or "TERMO DE EMBARGO" in text:
        return "embargo_notice", 0.96

    if "AUTO DE CONSTATA" in text:
        return "finding_notice", 0.96

    if "RELATORIO DE FISCALIZACAO" in text:
        return "inspection_report", 0.96

    return "unknown", 0.25


def extract_number(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    value = find_text(
        ocr_results,
        r"N[ÚUÜU]MERO\s*:\s*(\d+)",
    )

    if value:
        return value, 0.99

    return None, 0.0


def extract_series(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    value = find_text(
        ocr_results,
        r"S[ÉE]RIE\s*:\s*([A-Z0-9]+)",
    )

    if value:
        return value, 0.97

    return None, 0.0


def extract_year(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    value = find_text(
        ocr_results,
        r"\b(20\d{2})\b",
    )

    if value:
        return value, 0.96

    return None, 0.0


def extract_date(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    dates = re.findall(
        r"\b\d{2}/\d{2}/\d{4}\b",
        text,
    )

    if dates:
        return dates[-1], 0.96

    return None, 0.0


def extract_time(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    # 15:42
    match = re.search(
        r"\b([01]\d|2[0-3]):([0-5]\d)\b",
        text,
    )

    if match:
        return f"{match.group(1)}:{match.group(2)}", 0.98

    return None, 0.0


def extract_municipality(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    match = re.search(
        r"\b(PARAGOMINAS|ALTAMIRA|TAILANDIA|ULIAN[ÓO]POLIS)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).upper(), 0.98

    return None, 0.0


def extract_agency(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    if "SEMMA" in text.upper():
        return "SEMMA", 0.98

    return None, 0.0


def extract_party(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    match = re.search(
        r"1\.?NOME DO AUTUADO:\s*([^\n]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return normalize_text(match.group(1)), 0.85

    return None, 0.0


def extract_document_id(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    match = re.search(
        r"(?:RG/CPF/CNPJ|CPF|CNPJ)\s*:\s*([0-9.\-/]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1), 0.94

    # fallback for the known CPF pattern
    match = re.search(
        r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        text,
    )

    if match:
        return match.group(0), 0.94

    return None, 0.0


def extract_address(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    match = re.search(
        r"6\.ENDERECO:\s*([^\n]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return normalize_text(match.group(1)), 0.80

    return None, 0.0


def extract_property_and_area(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float, float | None, float]:

    text = all_text(ocr_results)

    # Example:
    # "Desmatar 18,9862 hectares ..."
    area_match = re.search(
        r"Desmatar\s+([0-9]+,[0-9]+)\s+hectares",
        text,
        re.IGNORECASE,
    )

    area = None
    area_conf = 0.0

    if area_match:
        try:
            area = float(area_match.group(1).replace(",", "."))
            area_conf = 0.86
        except ValueError:
            pass

    # Example:
    # "imóvel rural denominado Fazenda Santa Terezinha"
    property_match = re.search(
        r"denominado\s+([^,\n]+)",
        text,
        re.IGNORECASE,
    )

    property_name = None
    property_conf = 0.0

    if property_match:
        property_name = normalize_text(property_match.group(1))
        property_conf = 0.84

    return property_name, property_conf, area, area_conf


def extract_coordinates(
    ocr_results: list[dict[str, Any]],
) -> tuple[list[str], float]:

    text = all_text(ocr_results)

    # Preserve the coordinates as printed as much as possible.
    # Do not normalize them.
    candidates = re.findall(
        r"[NS]\s*\d+°?\d*['’]?\d+(?:[.,]\d+)?[\"”]?\s*"
        r"[EW]\s*\d+°?\d*['’]?\d+(?:[.,]\d+)?[\"”]?",
        text,
        re.IGNORECASE,
    )

    if candidates:
        return [normalize_text(value) for value in candidates], 0.65

    return [], 0.0


def extract_fine(
    ocr_results: list[dict[str, Any]],
) -> tuple[float | None, float]:

    text = all_text(ocr_results)

    # OCR is currently misreading the handwritten amount.
    # We deliberately do NOT repair it automatically.
    #
    # Recognize only an unambiguous Brazilian currency pattern.
    match = re.search(
        r"R\$\s*([\d.]+,\d{2})",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None, 0.0

    raw = match.group(1)

    try:
        value = float(
            raw.replace(".", "").replace(",", ".")
        )
        return value, 0.98
    except ValueError:
        return None, 0.0


def extract_officer_registration(
    ocr_results: list[dict[str, Any]],
) -> tuple[str | None, float]:

    text = all_text(ocr_results)

    match = re.search(
        r"MATR[ÍI]CULA(?:\s+DO\s+AUTUANTE)?\s*[:\-]?\s*([\d.]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1), 0.98

    return None, 0.0


def extract_legal_basis(
    ocr_results: list[dict[str, Any]],
) -> list[str]:

    text = all_text(ocr_results)

    patterns = [
        r"Decreto Federal n\s*[º°]?\s*[\d.]+/\d{4}",
        r"Lei Federal n\s*[º°]?\s*[\d.]+/\d{4}",
    ]

    found: list[str] = []

    for pattern in patterns:
        found.extend(
            re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )
        )

    return list(dict.fromkeys(found))


def extract_fields(
    ocr_results: list[dict[str, Any]],
) -> dict[str, Any]:

    document_type, document_type_conf = extract_document_type(ocr_results)
    number, number_conf = extract_number(ocr_results)
    series, series_conf = extract_series(ocr_results)
    year, year_conf = extract_year(ocr_results)
    issued_date, date_conf = extract_date(ocr_results)
    issued_time, time_conf = extract_time(ocr_results)
    municipality, municipality_conf = extract_municipality(ocr_results)
    agency, agency_conf = extract_agency(ocr_results)

    party_name, party_conf = extract_party(ocr_results)
    document_id, document_id_conf = extract_document_id(ocr_results)
    address, address_conf = extract_address(ocr_results)

    property_name, property_conf, area_ha, area_conf = (
        extract_property_and_area(ocr_results)
    )

    coordinates, coordinates_conf = extract_coordinates(ocr_results)

    fine_brl, fine_conf = extract_fine(ocr_results)

    officer_registration, officer_conf = (
        extract_officer_registration(ocr_results)
    )

    legal_basis = extract_legal_basis(ocr_results)

    parties = []

    if party_name:
        parties.append(
            {
                "role": "cited_party",
                "name": party_name,
                "document_id": document_id,
                "address": address,
            }
        )

    return {
        "document_type": document_type,
        "number": number,
        "series": series,
        "year": year,
        "issued_date": issued_date,
        "issued_time": issued_time,
        "municipality": municipality,
        "agency": agency,

        "parties": parties,

        "property_name": property_name,
        "car": None,
        "area_ha": area_ha,

        "coordinates": coordinates,

        "legal_basis": legal_basis,

        "fine_brl": fine_brl,

        "references": [],

        "officer_registration": officer_registration,

        "signatures": {},

        "fields": {},

        "confidence": {
            "document_type": document_type_conf,
            "number": number_conf,
            "series": series_conf,
            "year": year_conf,
            "issued_date": date_conf,
            "issued_time": time_conf,
            "municipality": municipality_conf,
            "agency": agency_conf,
            "party_name": party_conf,
            "party_document_id": document_id_conf,
            "party_address": address_conf,
            "property_name": property_conf,
            "area_ha": area_conf,
            "coordinates": coordinates_conf,
            "fine_brl": fine_conf,
            "officer_registration": officer_conf,
        },
    }