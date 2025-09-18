"""Generate sample data sets for the MSP business dashboard."""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CLIENTS = [
    {
        "client": "Acme Manufacturing",
        "industry": "Manufacturing",
        "employees": 120,
        "region": "Midwest",
        "account_manager": "Alex Rivera",
        "tier": "Enterprise",
    },
    {
        "client": "Brightside Retail",
        "industry": "Retail",
        "employees": 75,
        "region": "Southeast",
        "account_manager": "Casey Patel",
        "tier": "Growth",
    },
    {
        "client": "Northwind Legal",
        "industry": "Legal",
        "employees": 45,
        "region": "Northeast",
        "account_manager": "Jordan Smith",
        "tier": "Professional",
    },
    {
        "client": "Skyline Nonprofit",
        "industry": "Nonprofit",
        "employees": 60,
        "region": "West",
        "account_manager": "Morgan Lee",
        "tier": "Growth",
    },
]

MONTHS = pd.date_range("2023-01-01", "2024-06-01", freq="MS")
RNG = random.Random(42)


def iterate_months() -> Iterable[pd.Timestamp]:
    for month in MONTHS:
        yield month


def generate_financials() -> pd.DataFrame:
    rows = []
    for client in CLIENTS:
        base_mrr = RNG.randint(4500, 7800)
        for month in iterate_months():
            growth = 1 + RNG.uniform(-0.04, 0.06)
            recurring = round(base_mrr * growth, 2)
            project = round(RNG.uniform(500, 2500), 2)
            expenses = round(recurring * RNG.uniform(0.35, 0.6), 2)
            rows.append(
                {
                    "month": month,
                    "client": client["client"],
                    "recurring_revenue": recurring,
                    "project_revenue": project,
                    "expenses": expenses,
                }
            )
            base_mrr = recurring * RNG.uniform(0.98, 1.04)
    return pd.DataFrame(rows)


def generate_ticket_summary() -> pd.DataFrame:
    rows = []
    for client in CLIENTS:
        base_opened = RNG.randint(15, 40)
        for month in iterate_months():
            delta = RNG.randint(-4, 6)
            opened = max(8, base_opened + delta)
            resolved = max(6, opened - RNG.randint(-2, 4))
            first_response = RNG.uniform(18, 90)
            resolution = RNG.uniform(6, 32)
            breaches = max(0, int(opened * RNG.uniform(0.02, 0.08)))
            csat = round(RNG.uniform(4.1, 4.9), 2)
            rows.append(
                {
                    "month": month,
                    "client": client["client"],
                    "tickets_opened": opened,
                    "tickets_resolved": resolved,
                    "first_response_minutes_avg": round(first_response, 2),
                    "resolution_hours_avg": round(resolution, 2),
                    "sla_breaches": breaches,
                    "csat_score": csat,
                }
            )
            base_opened = opened
    return pd.DataFrame(rows)


def generate_uptime() -> pd.DataFrame:
    rows = []
    for client in CLIENTS:
        for month in iterate_months():
            base = RNG.uniform(99.0, 99.9)
            major_incidents = RNG.choice([0, 0, 1])
            downtime = round((100 - base) * 43.2, 2)  # approximate minutes per month
            rows.append(
                {
                    "month": month,
                    "client": client["client"],
                    "uptime_percentage": round(base, 3),
                    "downtime_minutes": downtime,
                    "major_incidents": major_incidents,
                }
            )
    return pd.DataFrame(rows)


def generate_contracts() -> pd.DataFrame:
    today = date(2024, 5, 1)
    rows = []
    for idx, client in enumerate(CLIENTS):
        renewal = today + timedelta(days=90 * (idx + 1))
        value = RNG.randint(65000, 140000)
        rows.append(
            {
                "client": client["client"],
                "contract_end": renewal,
                "contract_value": value,
                "auto_renew": RNG.choice([True, False]),
                "notice_required_days": RNG.choice([30, 45, 60]),
            }
        )
    return pd.DataFrame(rows)


def generate_clients() -> pd.DataFrame:
    return pd.DataFrame(CLIENTS)


def write_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(DATA_DIR / name, index=False)


def main() -> None:
    write_csv(generate_financials(), "financials.csv")
    write_csv(generate_ticket_summary(), "tickets_summary.csv")
    write_csv(generate_uptime(), "uptime.csv")
    write_csv(generate_contracts(), "contracts.csv")
    write_csv(generate_clients(), "clients.csv")
    print(f"Sample data written to {DATA_DIR}")


if __name__ == "__main__":
    main()
