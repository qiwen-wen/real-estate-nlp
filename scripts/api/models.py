"""Pydantic request/response models for the Real Estate NLP API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Health ─────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    version: str


# ── Search ─────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    rank: int
    score: float
    remarks: str


class SearchResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    sql_ready: bool
    filters: Dict[str, Any] = {}
    sql: Optional[str] = None
    params: Optional[List[Any]] = None
    schema_errors: List[str] = []
    message: str
    results: List[SearchResultItem] = []
    count: int = 0
    cached: bool = False


# ── Parse query ────────────────────────────────────────────────────────────
class ParseQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class ParseQueryResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    sql_ready: bool
    filters: Dict[str, Any] = {}
    sql: Optional[str] = None
    params: Optional[List[Any]] = None
    schema_errors: List[str] = []
    message: str
    cached: bool = False


# ── Intent only ────────────────────────────────────────────────────────────
class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class IntentResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    cached: bool = False


# ── Entity extraction ──────────────────────────────────────────────────────
class ExtractEntitiesRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


class EntitiesPayload(BaseModel):
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    price: Optional[int] = None
    sqft: Optional[int] = None
    amenities: List[str] = []


class ExtractEntitiesResponse(BaseModel):
    text: str
    entities: EntitiesPayload
    cached: bool = False


# ── Signal extraction ──────────────────────────────────────────────────────
class ExtractSignalsRequest(BaseModel):
    listing: Dict[str, Any] = Field(
        ...,
        description=(
            "Listing record matching rets_property columns. Required-ish keys: "
            "L_ListingID, L_Remarks. Optional: L_Keyword2 (beds), LM_Dec_3 (baths), "
            "L_SystemPrice, LM_Int2_3 (sqft)."
        ),
    )


class ExtractSignalsResponse(BaseModel):
    listing_id: Optional[Any] = None
    entities: EntitiesPayload
    amenities: List[str] = []
    condition_keywords: List[str] = []
    financing_terms: List[str] = []
    location_features: List[str] = []


# ── Summarize ──────────────────────────────────────────────────────────────
class SummarizeRequest(BaseModel):
    remarks: str = Field(..., min_length=1, max_length=20000)
    entities: Optional[EntitiesPayload] = None
    num_sentences: int = Field(default=2, ge=1, le=10)


class SummarizeResponse(BaseModel):
    summary: str
    num_sentences: int
    cached: bool = False


# ── Compliance ─────────────────────────────────────────────────────────────
class ComplianceRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


class ComplianceViolation(BaseModel):
    category: str
    severity: str
    matched_text: str
    start: int
    end: int
    message: str
    suggestion: str


class ComplianceResponse(BaseModel):
    compliant: bool
    requires_review: bool
    error_count: int
    warning_count: int
    info_count: int
    violations: List[ComplianceViolation] = []
    cached: bool = False
