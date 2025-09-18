"""Command line helper for the demo dashboard."""
from __future__ import annotations

from typing import Optional

import typer

from . import DATA_DIR
from . import data_loader
from . import forecasting
from . import metrics

app = typer.Typer(help="MSP business dashboard helper commands")


def _fmt_currency(value: float) -> str:
    return f"${value:,.2f}"


def _fmt_percentage(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _fmt_minutes(value: float) -> str:
    return f"{value:.1f} min"


def _fmt_hours(value: float) -> str:
    return f"{value:.1f} hrs"


def _resolve_range(start: Optional[str], end: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if start and not end:
        # default to end at most recent
        end = data_loader.load_financials()["month"].max().strftime("%Y-%m-%d")
    return start, end


@app.command()
def summary(
    client: str = typer.Option("All", help="Filter the summary for a specific client"),
    start: Optional[str] = typer.Option(None, help="Start month in YYYY-MM format"),
    end: Optional[str] = typer.Option(None, help="End month in YYYY-MM format"),
) -> None:
    """Print a quick business summary in the terminal."""

    start, end = _resolve_range(start, end)
    financials = data_loader.get_filtered_dataset("financials", client, start, end)
    tickets = data_loader.get_filtered_dataset("tickets", client, start, end)
    uptime = data_loader.get_filtered_dataset("uptime", client, start, end)

    kpis = metrics.calculate_kpis(financials, tickets, uptime)

    typer.secho("MSP Business Dashboard", bold=True)
    typer.echo(f"Data directory: {DATA_DIR}")
    if client and client != "All":
        typer.echo(f"Client filter: {client}")
    if start or end:
        typer.echo(f"Date range: {start or 'beginning'} -> {end or 'latest'}")
    typer.echo("")

    typer.secho("Key Metrics", bold=True)
    typer.echo(f"Recurring revenue: {_fmt_currency(kpis.recurring_revenue)}")
    typer.echo(f"Project revenue: {_fmt_currency(kpis.project_revenue)}")
    typer.echo(f"Gross margin: {_fmt_percentage(kpis.gross_margin)}")
    typer.echo(f"Ticket resolution rate: {_fmt_percentage(kpis.ticket_resolution_rate)}")
    typer.echo(f"Avg. first response: {_fmt_minutes(kpis.avg_first_response_minutes)}")
    typer.echo(f"Avg. resolution time: {_fmt_hours(kpis.avg_resolution_hours)}")
    typer.echo(f"SLA compliance: {_fmt_percentage(kpis.sla_compliance)}")
    typer.echo(f"Avg. uptime: {_fmt_percentage(kpis.avg_uptime / 100)}")
    typer.echo(f"CSAT score: {kpis.csat_score:.2f} / 5.0")
    typer.echo("")

    typer.secho("Top Clients by Health", bold=True)
    health = metrics.client_health_score(financials, tickets, uptime)
    if health.empty:
        typer.echo("No client data found.")
    else:
        for _, row in health.iterrows():
            typer.echo(f" - {row['client']}: {row['health_score']}/100")

    typer.echo("")
    typer.secho("Renewals", bold=True)
    renewals = metrics.renewal_pipeline(data_loader.load_contracts())
    if renewals.empty:
        typer.echo("No renewals in the next 120 days.")
    else:
        for _, row in renewals.iterrows():
            typer.echo(
                f" - {row['client']} renews {row['contract_end'].date()}"
                f" ({row['days_remaining']} days, value {_fmt_currency(row['contract_value'])})"
            )


@app.command()
def forecast(
    periods: int = typer.Option(3, help="Number of months to forecast"),
    client: str = typer.Option("All", help="Optional client filter"),
) -> None:
    """Display basic forecasts for revenue and ticket volume."""

    financials = data_loader.get_filtered_dataset("financials", client)
    tickets = data_loader.get_filtered_dataset("tickets", client)

    revenue_forecast = forecasting.forecast_recurring_revenue(financials, periods)
    ticket_forecast = forecasting.forecast_ticket_volume(tickets, periods)

    typer.secho("Revenue Forecast", bold=True)
    for _, row in revenue_forecast.iterrows():
        typer.echo(
            f" - {row['month'].strftime('%Y-%m')}: {_fmt_currency(row['recurring_revenue'])}"
        )

    typer.echo("")
    typer.secho("Ticket Volume Forecast", bold=True)
    for _, row in ticket_forecast.iterrows():
        typer.echo(
            f" - {row['month'].strftime('%Y-%m')}: {row['tickets_opened']:.0f} tickets"
        )


@app.command()
def contracts(
    within_days: int = typer.Option(180, help="Renewals within the next N days"),
) -> None:
    """List contracts expiring within the next N days."""

    renewals = metrics.renewal_pipeline(data_loader.load_contracts(), within_days)
    if renewals.empty:
        typer.echo("No contracts in the specified window.")
        return

    typer.secho("Upcoming Renewals", bold=True)
    for _, row in renewals.iterrows():
        typer.echo(
            f" - {row['client']} | {row['contract_end'].date()} | "
            f"{row['days_remaining']} days | {_fmt_currency(row['contract_value'])}"
        )


if __name__ == "__main__":
    app()
