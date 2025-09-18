# Business Data Dashboard

A lightweight demo dashboard that helps a one-person MSP keep tabs on client health, recurring revenue, ticket performance, and upcoming renewals. The project ships with a Dash web application, reusable analytics utilities, and a command line helper that work together on top of the same sample data set.

## What's included

- **Interactive Dash application** with KPI cards, trend visualisations, health scoring, and contract renewal reminders.
- **Reusable analytics utilities** for computing KPIs, backlog trends, uptime, and renewal pipelines that can be embedded in other tooling.
- **Simple forecasting helpers** that project recurring revenue and ticket volume over the next few months.
- **Command line helper** (powered by Typer) for quickly printing summaries, forecasts, and renewal lists in the terminal.
- **Scriptable sample data** generation that produces consistent demo CSV files for experimentation.

## Getting started

1. (Optional but recommended) create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Generate fresh sample data (the CSV files are already committed but can be rebuilt):

   ```bash
   python scripts/generate_sample_data.py
   ```

4. Launch the dashboard UI:

   ```bash
   python app.py
   ```

   The app will start on http://127.0.0.1:8050/ by default.

5. Explore the CLI helper:

   ```bash
   python -m src.dashboard.cli summary --client "Acme Manufacturing" --start 2024-01-01 --end 2024-03-01
   python -m src.dashboard.cli forecast --periods 6
   python -m src.dashboard.cli contracts --within-days 120
   ```

## Project layout

```
├── app.py                     # Dash application entrypoint
├── assets/                    # Custom CSS for Dash
├── data/                      # Generated sample data (CSV)
├── scripts/generate_sample_data.py
├── src/dashboard/             # Reusable analytics package
│   ├── __init__.py
│   ├── data_loader.py         # Shared dataset loading and filtering helpers
│   ├── metrics.py             # KPI, backlog, uptime, and renewal calculations
│   ├── forecasting.py         # Simple linear projections
│   └── cli.py                 # Typer powered command line tool
└── tests/                     # Pytest-based regression checks
```

## Running tests

```bash
pytest
```

The tests exercise the KPI calculations, health scoring, and forecasting utilities to make sure they stay in sync with the sample data set.
