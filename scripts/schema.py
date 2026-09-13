from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Party(BaseModel):
    role: str
    name: str | None = None
    document_id: str | None = None
    address: str | None = None


class Reference(BaseModel):
    document_type: str
    number: str
    year: str


class Document(BaseModel):
    document_type: str
    number: str | None = None
    series: str | None = None
    year: str | None = None
    issued_date: str | None = None
    issued_time: str | None = None
    municipality: str | None = None
    agency: str | None = None

    parties: list[Party] = Field(default_factory=list)

    property_name: str | None = None
    car: str | None = None
    area_ha: float | None = None

    coordinates: list[str] = Field(default_factory=list)

    legal_basis: list[str] = Field(default_factory=list)
    fine_brl: float | None = None

    references: list[Reference] = Field(default_factory=list)

    officer_registration: str | None = None

    signatures: dict[str, Any] = Field(default_factory=dict)

    fields: dict[str, Any] = Field(default_factory=dict)

    confidence: dict[str, float] = Field(default_factory=dict)