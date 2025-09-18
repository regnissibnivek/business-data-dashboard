"""Lightweight forecasting helpers for the demo dashboard."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _linear_forecast(values: pd.Series, periods: int) -> pd.Series:
    if values.empty:
        return pd.Series(dtype=float)

    y = values.values.astype(float)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y) + periods)
    forecast = intercept + slope * future_x
    return pd.Series(forecast, index=np.arange(1, periods + 1))


def forecast_recurring_revenue(financials: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    """Forecast recurring revenue for the next *periods* months."""

    trend = (
        financials.groupby("month", as_index=False)["recurring_revenue"].sum()
        .sort_values("month")
    )
    forecast = _linear_forecast(trend["recurring_revenue"], periods)
    last_month = trend["month"].max() if not trend.empty else pd.Timestamp.today()
    future_months = pd.date_range(last_month + pd.offsets.MonthBegin(), periods=periods, freq="MS")
    return pd.DataFrame({"month": future_months, "recurring_revenue": forecast.values})


def forecast_ticket_volume(tickets: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    """Forecast ticket volume for the next *periods* months."""

    trend = (
        tickets.groupby("month", as_index=False)["tickets_opened"].sum()
        .sort_values("month")
    )
    forecast = _linear_forecast(trend["tickets_opened"], periods)
    last_month = trend["month"].max() if not trend.empty else pd.Timestamp.today()
    future_months = pd.date_range(last_month + pd.offsets.MonthBegin(), periods=periods, freq="MS")
    return pd.DataFrame({"month": future_months, "tickets_opened": forecast.values})
