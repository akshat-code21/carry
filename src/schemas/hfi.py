"""Pydantic schemas for HFI (Hedge Fund Intelligence) API endpoints."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Investor ────────────────────────────────────────────────────────────────


class InvestorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    cik_number: str | None = Field(None, max_length=20)


class InvestorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    cik_number: str | None = Field(None, max_length=20)
    is_active: bool | None = None


class InvestorOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    cik_number: str | None
    is_active: bool
    last_synced_at: datetime | None
    sources_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvestorStats(BaseModel):
    content_items: int = 0
    reports: int = 0
    unread_alerts: int = 0


# ── Source ──────────────────────────────────────────────────────────────────


class SourceCreate(BaseModel):
    source_type: str = "website"
    url: str
    label: str | None = None
    config: dict | None = None


class SourceOut(BaseModel):
    id: uuid.UUID
    source_type: str
    url: str
    label: str | None
    is_active: bool
    last_checked_at: datetime | None
    last_successful_at: datetime | None
    consecutive_failures: int
    check_frequency_hours: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Content Item ────────────────────────────────────────────────────────────


class ContentItemOut(BaseModel):
    id: uuid.UUID
    content_type: str
    title: str | None
    url: str | None
    processing_status: str
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Portfolio Change ────────────────────────────────────────────────────────


class PortfolioChangeOut(BaseModel):
    id: uuid.UUID
    ticker_symbol: str | None
    company_name: str | None
    cusip: str | None
    change_type: str
    shares_previous: int
    shares_current: int
    value_usd: int | None
    percent_of_portfolio: float | None
    filing_period: str
    report_date: date | str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Report ──────────────────────────────────────────────────────────────────


class ReportOut(BaseModel):
    id: uuid.UUID
    investor_id: uuid.UUID | None
    report_type: str
    title: str
    summary: str | None
    content_markdown: str
    is_read: bool
    period_start: datetime | date | str | None = None
    period_end: datetime | date | str | None = None
    generated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: uuid.UUID
    investor_id: uuid.UUID | None
    report_type: str
    title: str
    summary: str | None
    is_read: bool
    generated_at: datetime

    model_config = {"from_attributes": True}


# ── Alert ───────────────────────────────────────────────────────────────────


class AlertOut(BaseModel):
    id: uuid.UUID
    investor_id: uuid.UUID | None
    alert_type: str
    title: str
    summary: str | None
    severity: str
    score: int
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertsResponse(BaseModel):
    alerts: list[AlertOut]
    total: int
    unread_count: int


# ── Consensus & Compare ────────────────────────────────────────────────────


class FundHoldingDetail(BaseModel):
    investor_id: str
    investor_name: str
    change_type: str
    shares_current: int
    shares_previous: int
    value_usd: int | None = None
    percent_of_portfolio: float | None = None


class ConsensusHolding(BaseModel):
    ticker_symbol: str | None = None
    company_name: str | None = None
    total_funds_holding: int
    funds_buying: int
    funds_selling: int
    total_value_usd: int | None = None
    funds: list[FundHoldingDetail] = []


class ConsensusResponse(BaseModel):
    filing_period: str
    available_periods: list[str] = []
    total_funds_analyzed: int
    holdings: list[ConsensusHolding]


class CompareCell(BaseModel):
    ticker_symbol: str | None
    company_name: str | None
    shares: int
    value_usd: int | None
    percent_of_portfolio: float | None
    change_type: str


class CompareInvestor(BaseModel):
    investor_id: uuid.UUID
    investor_name: str
    holdings: list[CompareCell]


class CompareResponse(BaseModel):
    period: str
    all_tickers: list[str]
    investors: list[CompareInvestor]


# ── Sync ────────────────────────────────────────────────────────────────────


class SyncResponse(BaseModel):
    investor_id: uuid.UUID
    status: str
    processed: int = 0
    failed: int = 0
    skipped: int = 0
