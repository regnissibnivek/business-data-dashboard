"""Lightweight forecasting helpers for the demo dashboard."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _linear_forecast(values: pd.Series, periods: int) -> pd.Series:
    if periods < 0:
        raise ValueError("periods must be non-negative")
    if values.empty or periods == 0:
        return pd.Series(dtype=float)

    if len(values) == 1:
        return pd.Series(float(values.iloc[0]), index=np.arange(1, periods + 1))

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
    if forecast.empty:
        return trend.iloc[:0].copy()
    last_month = trend["month"].max()
    future_months = pd.date_range(last_month + pd.offsets.MonthBegin(), periods=periods, freq="MS")
    return pd.DataFrame({"month": future_months, "recurring_revenue": forecast.values})


def forecast_ticket_volume(tickets: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    """Forecast ticket volume for the next *periods* months."""

    trend = (
        tickets.groupby("month", as_index=False)["tickets_opened"].sum()
        .sort_values("month")
    )
    forecast = _linear_forecast(trend["tickets_opened"], periods)
    if forecast.empty:
        return trend.iloc[:0].copy()
    last_month = trend["month"].max()
    future_months = pd.date_range(last_month + pd.offsets.MonthBegin(), periods=periods, freq="MS")
    return pd.DataFrame({"month": future_months, "tickets_opened": forecast.values})
