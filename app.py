"""Dash application exposing the MSP business dashboard demo."""
from __future__ import annotations

from typing import List

import dash
from dash import Dash, Input, Output, dcc, html
from dash.dash_table import DataTable
import pandas as pd
import plotly.express as px

from src.dashboard import data_loader, forecasting, metrics

financials_df = data_loader.load_financials()
contracts_df = data_loader.load_contracts()
clients_df = data_loader.load_clients()

min_month = financials_df["month"].min().date()
max_month = financials_df["month"].max().date()

app: Dash = dash.Dash(__name__, title="MSP Business Dashboard")
server = app.server


def _kpi_card(title: str, value: str, description: str) -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.P(title, className="kpi-title"),
            html.H3(value, className="kpi-value"),
            html.Span(description, className="kpi-description"),
        ],
    )


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _format_percentage(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _format_minutes(value: float) -> str:
    return f"{value:.0f} min"


def _format_hours(value: float) -> str:
    return f"{value:.1f} hrs"


app.layout = html.Div(
    className="layout",
    children=[
        html.Header(
            className="page-header",
            children=[
                html.H1("MSP Business Data Dashboard"),
                html.P(
                    "Track client health, revenue trends, service performance, and renewals at a glance."
                ),
            ],
        ),
        html.Div(
            className="filters",
            children=[
                html.Div(
                    children=[
                        html.Label("Client"),
                        dcc.Dropdown(
                            id="client-filter",
                            options=[{"label": "All Clients", "value": "All"}]
                            + [
                                {"label": client, "value": client}
                                for client in clients_df["client"].tolist()
                            ],
                            value="All",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Date range"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=min_month,
                            max_date_allowed=max_month,
                            start_date=min_month,
                            end_date=max_month,
                        ),
                    ]
                ),
            ],
        ),
        html.Div(id="kpi-row", className="kpi-row"),
        html.Div(
            className="chart-grid",
            children=[
                dcc.Graph(id="revenue-chart"),
                dcc.Graph(id="ticket-chart"),
                dcc.Graph(id="uptime-chart"),
                dcc.Graph(id="forecast-chart"),
            ],
        ),
        html.Div(
            className="tables",
            children=[
                html.Div(
                    className="table-wrapper",
                    children=[
                        html.H3("Client Health"),
                        DataTable(
                            id="health-table",
                            columns=[
                                {"name": "Client", "id": "client"},
                                {"name": "Health Score", "id": "health_score"},
                            ],
                            style_cell={"padding": "0.5rem"},
                            style_header={"backgroundColor": "#f4f6f8", "fontWeight": "bold"},
                        ),
                    ],
                ),
                html.Div(
                    className="table-wrapper",
                    children=[
                        html.H3("Upcoming Renewals"),
                        DataTable(
                            id="renewal-table",
                            columns=[
                                {"name": "Client", "id": "client"},
                                {"name": "End Date", "id": "contract_end"},
                                {"name": "Value", "id": "contract_value"},
                                {"name": "Days Remaining", "id": "days_remaining"},
                            ],
                            style_cell={"padding": "0.5rem"},
                            style_header={"backgroundColor": "#f4f6f8", "fontWeight": "bold"},
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-row", "children"),
    Output("revenue-chart", "figure"),
    Output("ticket-chart", "figure"),
    Output("uptime-chart", "figure"),
    Output("forecast-chart", "figure"),
    Output("health-table", "data"),
    Output("renewal-table", "data"),
    Input("client-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def refresh_dashboard(client: str, start_date: str, end_date: str):
    financials = data_loader.get_filtered_dataset("financials", client, start_date, end_date)
    tickets = data_loader.get_filtered_dataset("tickets", client, start_date, end_date)
    uptime = data_loader.get_filtered_dataset("uptime", client, start_date, end_date)

    kpi = metrics.calculate_kpis(financials, tickets, uptime)
    kpi_cards: List[html.Div] = [
        _kpi_card("Recurring Revenue", _format_currency(kpi.recurring_revenue), "Across selected months"),
        _kpi_card("Project Revenue", _format_currency(kpi.project_revenue), "Services and project work"),
        _kpi_card("Gross Margin", _format_percentage(kpi.gross_margin), "Net of expenses"),
        _kpi_card("SLA Compliance", _format_percentage(kpi.sla_compliance), "Tickets meeting SLA"),
        _kpi_card("First Response", _format_minutes(kpi.avg_first_response_minutes), "Average response speed"),
        _kpi_card("Avg Uptime", f"{kpi.avg_uptime:.2f}%", "Service availability"),
    ]

    revenue_trend = metrics.monthly_recurring_revenue(financials)
    fig_revenue = px.line(
        revenue_trend,
        x="month",
        y="recurring_revenue",
        title="Monthly Recurring Revenue",
        markers=True,
    )
    fig_revenue.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    ticket_trend = metrics.ticket_backlog(tickets)
    fig_ticket = px.bar(
        ticket_trend,
        x="month",
        y="tickets_opened",
        title="Tickets Opened vs Resolved",
        labels={"tickets_opened": "Tickets"},
    )
    fig_ticket.add_scatter(x=ticket_trend["month"], y=ticket_trend["tickets_resolved"], mode="lines+markers", name="Resolved")
    fig_ticket.add_scatter(x=ticket_trend["month"], y=ticket_trend["backlog"], mode="lines", name="Backlog")
    fig_ticket.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    uptime_trend = metrics.uptime_trend(uptime)
    fig_uptime = px.line(
        uptime_trend,
        x="month",
        y="uptime_percentage",
        title="Average Uptime",
        markers=True,
    )
    fig_uptime.update_layout(yaxis=dict(range=[95, 100]), margin=dict(l=20, r=20, t=50, b=20))

    forecast_df = forecasting.forecast_recurring_revenue(financials)
    combined = pd.concat([revenue_trend.assign(type="Actual"), forecast_df.assign(type="Forecast")])
    fig_forecast = px.line(
        combined,
        x="month",
        y="recurring_revenue",
        color="type",
        title="Recurring Revenue Forecast",
        markers=True,
    )
    fig_forecast.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    health_df = metrics.client_health_score(financials, tickets, uptime)
    renewals_df = metrics.renewal_pipeline(contracts_df)
    if client and client != "All":
        renewals_df = renewals_df[renewals_df["client"] == client]

    renewals_table = renewals_df.assign(
        contract_end=lambda df: df["contract_end"].dt.strftime("%Y-%m-%d"),
        contract_value=lambda df: df["contract_value"].map(_format_currency),
    )

    health_table = health_df.to_dict("records")
    renewals_data = renewals_table.to_dict("records")

    return (
        kpi_cards,
        fig_revenue,
        fig_ticket,
        fig_uptime,
        fig_forecast,
        health_table,
        renewals_data,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
