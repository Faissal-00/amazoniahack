from __future__ import annotations

import argparse
import json
from pathlib import Path

from ocr_engine import OCREngine
from extract_fields import extract_fields
from schema import Document


def save_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def model_to_dict(model: Document) -> dict:
    # Supports both Pydantic v1 and v2.
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AmazôniaHack Challenge 2 document extraction"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the document image",
    )

    parser.add_argument(
        "--output",
        default="output",
        help="Output directory",
    )

    args = parser.parse_args()

    image_path = Path(args.input)
    output_dir = Path(args.output)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Input image does not exist: {image_path}"
        )

    print(f"\n[OCR] Processing: {image_path}")

    # ---------------------------------------------------------
    # 1. OCR
    # ---------------------------------------------------------

    engine = OCREngine()
    ocr_results = engine.extract(image_path)

    if not ocr_results:
        raise RuntimeError("OCR returned no text.")

    print(f"[OK] OCR detected {len(ocr_results)} text regions")

    # ---------------------------------------------------------
    # 2. Save raw OCR
    # ---------------------------------------------------------

    ocr_output_path = (
        output_dir
        / "ocr"
        / f"{image_path.stem}.json"
    )

    save_json(
        {
            "source_image": str(image_path),
            "detections": ocr_results,
        },
        ocr_output_path,
    )

    print(f"[OK] Raw OCR saved: {ocr_output_path}")

    # ---------------------------------------------------------
    # 3. Structured extraction
    # ---------------------------------------------------------

    extracted = extract_fields(ocr_results)

    # ---------------------------------------------------------
    # 4. Validate against our schema
    # ---------------------------------------------------------

    document = Document(**extracted)

    structured_data = model_to_dict(document)

    # ---------------------------------------------------------
    # 5. Save final Challenge 2 JSON
    # ---------------------------------------------------------

    structured_output_path = (
        output_dir
        / "structured"
        / f"{image_path.stem}.json"
    )

    save_json(
        structured_data,
        structured_output_path,
    )

    print(
        f"[OK] Structured JSON saved: "
        f"{structured_output_path}"
    )

    # ---------------------------------------------------------
    # 6. Show a readable summary
    # ---------------------------------------------------------

    print("\n========== EXTRACTED DOCUMENT ==========")

    fields_to_show = [
        "document_type",
        "number",
        "series",
        "year",
        "issued_date",
        "issued_time",
        "municipality",
        "agency",
        "property_name",
        "car",
        "area_ha",
        "fine_brl",
        "officer_registration",
    ]

    for field in fields_to_show:
        print(f"{field}: {structured_data.get(field)}")

    print("\n========== CONFIDENCE ==========")

    for field, confidence in structured_data["confidence"].items():
        print(f"{field}: {confidence:.2f}")

    print("\n========================================")


if __name__ == "__main__":
    main()