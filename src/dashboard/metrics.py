"""Business metrics calculations for the demo dashboard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class KPISummary:
    recurring_revenue: float
    project_revenue: float
    gross_margin: float
    ticket_resolution_rate: float
    avg_first_response_minutes: float
    avg_resolution_hours: float
    sla_compliance: float
    avg_uptime: float
    csat_score: float

    def as_dict(self) -> Dict[str, float]:
        return self.__dict__.copy()


def calculate_kpis(
    financials: pd.DataFrame, tickets: pd.DataFrame, uptime: pd.DataFrame
) -> KPISummary:
    """Return a KPI summary for the selected slice of data."""

    recurring_total = financials["recurring_revenue"].sum()
    project_total = financials["project_revenue"].sum()
    expenses_total = financials["expenses"].sum()
    revenue = recurring_total + project_total
    gross_margin = (revenue - expenses_total) / revenue if revenue else 0

    tickets_opened = tickets["tickets_opened"].sum()
    tickets_resolved = tickets["tickets_resolved"].sum()
    resolution_rate = (
        tickets_resolved / tickets_opened if tickets_opened else 0
    )
    first_response = tickets["first_response_minutes_avg"].mean() if not tickets.empty else 0
    resolution_hours = tickets["resolution_hours_avg"].mean() if not tickets.empty else 0
    sla_breaches = tickets["sla_breaches"].sum()
    sla_compliance = (
        1 - (sla_breaches / tickets_opened) if tickets_opened else 1
    )
    csat = tickets["csat_score"].mean() if not tickets.empty else 0

    avg_uptime = uptime["uptime_percentage"].mean() if not uptime.empty else 0

    return KPISummary(
        recurring_revenue=float(recurring_total),
        project_revenue=float(project_total),
        gross_margin=float(gross_margin),
        ticket_resolution_rate=float(resolution_rate),
        avg_first_response_minutes=float(first_response),
        avg_resolution_hours=float(resolution_hours),
        sla_compliance=float(sla_compliance),
        avg_uptime=float(avg_uptime),
        csat_score=float(csat),
    )


def monthly_recurring_revenue(financials: pd.DataFrame) -> pd.DataFrame:
    """Return monthly recurring revenue totals."""

    return (
        financials.groupby("month", as_index=False)["recurring_revenue"].sum()
        .sort_values("month")
    )


def ticket_backlog(tickets: pd.DataFrame) -> pd.DataFrame:
    """Calculate ticket backlog by month."""

    df = (
        tickets.groupby("month", as_index=False)[["tickets_opened", "tickets_resolved"]].sum()
        .sort_values("month")
    )
    df["backlog"] = (df["tickets_opened"] - df["tickets_resolved"]).cumsum()
    return df


def uptime_trend(uptime: pd.DataFrame) -> pd.DataFrame:
    """Return average uptime per month."""

    return (
        uptime.groupby("month", as_index=False)["uptime_percentage"].mean()
        .sort_values("month")
    )


def client_health_score(
    financials: pd.DataFrame, tickets: pd.DataFrame, uptime: pd.DataFrame
) -> pd.DataFrame:
    """Return a health score for each client (0-100)."""

    revenue = (
        financials.groupby("client")["recurring_revenue"].mean()
        / financials["recurring_revenue"].mean()
    )
    revenue = revenue.clip(lower=0)

    ticket_quality = 1 - (
        tickets.groupby("client")["sla_breaches"].sum()
        / tickets.groupby("client")["tickets_opened"].sum()
    )
    ticket_quality = ticket_quality.fillna(1).clip(0, 1)

    uptime_score = (
        uptime.groupby("client")["uptime_percentage"].mean() / 100
    ).clip(0, 1)

    combined = (
        0.4 * revenue.reindex(uptime_score.index, fill_value=revenue.mean())
        + 0.35 * ticket_quality.reindex(uptime_score.index, fill_value=0.9)
        + 0.25 * uptime_score
    )
    df = combined.reset_index(name="health_score")
    df["health_score"] = (df["health_score"].clip(0, 1) * 100).round(1)
    return df.sort_values("health_score", ascending=False)


def renewal_pipeline(contracts: pd.DataFrame, within_days: int = 120) -> pd.DataFrame:
    """Return contracts renewing within the specified window."""

    today = pd.Timestamp.today().normalize()
    end = today + pd.Timedelta(days=within_days)
    mask = (contracts["contract_end"] >= today) & (contracts["contract_end"] <= end)
    result = contracts.loc[mask].copy()
    result["days_remaining"] = (
        result["contract_end"] - today
    ).dt.days
    return result.sort_values("contract_end")
