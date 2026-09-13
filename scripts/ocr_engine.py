from __future__ import annotations

from pathlib import Path
from typing import Any

from paddleocr import PaddleOCR


class OCREngine:
    """Small wrapper around PaddleOCR."""

    def __init__(self) -> None:
        self.ocr = PaddleOCR(
            lang="pt",
            use_angle_cls=True,
        )

    def extract(self, image_path: str | Path) -> list[dict[str, Any]]:
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Compatible with the PaddleOCR API installed in this environment.
        results = self.ocr.ocr(str(image_path), cls=True)

        if results is None:
            return []

        output: list[dict[str, Any]] = []

        for page in results:
            if page is None:
                continue

            for line in page:
                if not line or len(line) < 2:
                    continue

                box = line[0]
                text_info = line[1]

                text = text_info[0]
                confidence = float(text_info[1])

                output.append(
                    {
                        "text": text,
                        "confidence": confidence,
                        "box": box,
                    }
                )

        return output