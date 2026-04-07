"""Schema validation for parsed real-estate query filters."""

from __future__ import annotations

import json
from pathlib import Path


class SchemaValidator:
    """Load schema from data/schema.json and validate parsed filters."""

    def __init__(self, schema_path: str | None = None, allowed_cities=None):
        default_schema = Path(__file__).resolve().parents[2] / "data" / "schema.json"
        self.schema_path = Path(schema_path) if schema_path else default_schema
        self.schema = self._load_schema(self.schema_path)

        cities = self.schema.get("allowed_cities") or self.schema.get("cities") or []
        if allowed_cities is not None:
            cities = list(allowed_cities)
        self.allowed_cities = {c.lower(): c for c in cities}

        self.ranges = self.schema.get("ranges", {})

    def _load_schema(self, schema_path: Path) -> dict:
        if not schema_path.exists():
            raise FileNotFoundError(f"schema file not found: {schema_path}")
        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_range(self, field: str, value):
        range_cfg = self.ranges.get(field)
        if not range_cfg or value is None:
            return

        min_v = range_cfg.get("min")
        max_v = range_cfg.get("max")

        if min_v is not None and value < min_v:
            raise ValueError(f"{field} out of range: {value} < {min_v}")
        if max_v is not None and value > max_v:
            raise ValueError(f"{field} out of range: {value} > {max_v}")

    def validate_filters(self, filters: dict):
        city = filters.get("city")
        if city and self.allowed_cities and city.lower() not in self.allowed_cities:
            raise ValueError(f"invalid city: {city}")

        city_exclude = filters.get("city_exclude")
        if city_exclude and self.allowed_cities and city_exclude.lower() not in self.allowed_cities:
            raise ValueError(f"invalid city: {city_exclude}")

        self._validate_range("price", filters.get("price_min"))
        self._validate_range("price", filters.get("price_max"))
        self._validate_range("beds", filters.get("beds_min"))
        self._validate_range("beds", filters.get("beds_max"))
        self._validate_range("baths", filters.get("baths_min"))
        self._validate_range("baths", filters.get("baths_max"))

        if (
            filters.get("price_min") is not None
            and filters.get("price_max") is not None
            and filters["price_min"] > filters["price_max"]
        ):
            raise ValueError("price_min cannot be greater than price_max")
        if (
            filters.get("beds_min") is not None
            and filters.get("beds_max") is not None
            and filters["beds_min"] > filters["beds_max"]
        ):
            raise ValueError("beds_min cannot be greater than beds_max")
        if (
            filters.get("baths_min") is not None
            and filters.get("baths_max") is not None
            and filters["baths_min"] > filters["baths_max"]
        ):
            raise ValueError("baths_min cannot be greater than baths_max")
