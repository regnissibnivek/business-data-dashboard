"""Utilities for loading demo data used by the dashboard."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import pandas as pd

from . import DATA_DIR


def _coerce_month(value: str | pd.Timestamp | None) -> pd.Timestamp | None:
    if value is None or value == "":
        return None
    if isinstance(value, pd.Timestamp):
        return value.normalize()
    return pd.to_datetime(value).normalize()


def _filter_date_range(
    df: pd.DataFrame,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    start_ts = _coerce_month(start)
    end_ts = _coerce_month(end)
    if start_ts is None and end_ts is None:
        return df
    mask = pd.Series([True] * len(df))
    if start_ts is not None:
        mask &= df["month"] >= start_ts
    if end_ts is not None:
        mask &= df["month"] <= end_ts
    return df.loc[mask]


def _filter_clients(df: pd.DataFrame, client: str | Iterable[str] | None) -> pd.DataFrame:
    if client is None or client == "All":
        return df
    if isinstance(client, str):
        clients = {client}
    else:
        clients = set(client)
    return df[df["client"].isin(clients)]


@lru_cache(maxsize=None)
def load_financials() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "financials.csv", parse_dates=["month"])
    df.sort_values(["month", "client"], inplace=True)
    return df


@lru_cache(maxsize=None)
def load_tickets() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "tickets_summary.csv", parse_dates=["month"])
    df.sort_values(["month", "client"], inplace=True)
    return df


@lru_cache(maxsize=None)
def load_uptime() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "uptime.csv", parse_dates=["month"])
    df.sort_values(["month", "client"], inplace=True)
    return df


@lru_cache(maxsize=None)
def load_contracts() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "contracts.csv", parse_dates=["contract_end"])
    df.sort_values("contract_end", inplace=True)
    return df


@lru_cache(maxsize=None)
def load_clients() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "clients.csv")


def get_filtered_dataset(
    dataset: str,
    client: str | Iterable[str] | None = None,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return a filtered dataset by name.

    Parameters
    ----------
    dataset:
        One of ``"financials"``, ``"tickets"``, ``"uptime"`` or ``"contracts"``.
    client:
        Optional client name or list of client names. ``"All"`` returns all clients.
    start, end:
        Optional month boundaries. Values are coerced using :func:`pandas.to_datetime`.
    """

    loaders = {
        "financials": load_financials,
        "tickets": load_tickets,
        "uptime": load_uptime,
        "contracts": load_contracts,
        "clients": load_clients,
    }
    try:
        loader = loaders[dataset]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Unknown dataset '{dataset}'") from exc

    df = loader()
    if "month" in df.columns:
        df = _filter_date_range(df, start=start, end=end)
    if "client" in df.columns:
        df = _filter_clients(df, client)
    return df.copy()
