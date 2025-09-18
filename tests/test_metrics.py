from __future__ import annotations

import pytest

from src.dashboard import data_loader, forecasting, metrics


def test_kpi_summary_matches_manual():
    client = "Acme Manufacturing"
    start = "2024-01-01"
    end = "2024-03-01"

    financials = data_loader.get_filtered_dataset("financials", client, start, end)
    tickets = data_loader.get_filtered_dataset("tickets", client, start, end)
    uptime = data_loader.get_filtered_dataset("uptime", client, start, end)

    summary = metrics.calculate_kpis(financials, tickets, uptime)

    recurring_total = financials["recurring_revenue"].sum()
    project_total = financials["project_revenue"].sum()
    expenses_total = financials["expenses"].sum()
    revenue = recurring_total + project_total
    expected_gross_margin = (revenue - expenses_total) / revenue

    assert summary.recurring_revenue == pytest.approx(recurring_total)
    assert summary.project_revenue == pytest.approx(project_total)
    assert summary.gross_margin == pytest.approx(expected_gross_margin)

    tickets_opened = tickets["tickets_opened"].sum()
    tickets_resolved = tickets["tickets_resolved"].sum()
    expected_resolution_rate = tickets_resolved / tickets_opened
    expected_sla = 1 - tickets["sla_breaches"].sum() / tickets_opened

    assert summary.ticket_resolution_rate == pytest.approx(expected_resolution_rate)
    assert summary.sla_compliance == pytest.approx(expected_sla)

    assert summary.avg_uptime == pytest.approx(uptime["uptime_percentage"].mean())
    assert summary.avg_first_response_minutes == pytest.approx(
        tickets["first_response_minutes_avg"].mean()
    )


def test_client_health_scores_are_sorted_and_bounded():
    financials = data_loader.load_financials()
    tickets = data_loader.load_tickets()
    uptime = data_loader.load_uptime()

    health = metrics.client_health_score(financials, tickets, uptime)
    assert health["health_score"].between(0, 100).all()
    assert health["health_score"].is_monotonic_decreasing


def test_forecast_generates_future_months():
    financials = data_loader.load_financials()
    tickets = data_loader.load_tickets()

    revenue_forecast = forecasting.forecast_recurring_revenue(financials, periods=4)
    ticket_forecast = forecasting.forecast_ticket_volume(tickets, periods=4)

    assert len(revenue_forecast) == 4
    assert len(ticket_forecast) == 4
    assert revenue_forecast["month"].is_monotonic_increasing
    assert ticket_forecast["month"].is_monotonic_increasing
