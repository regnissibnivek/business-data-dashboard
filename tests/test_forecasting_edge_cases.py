"""Regression tests for sparse forecast selections; no network or server required."""
import unittest

import numpy as np
import pandas as pd

from src.dashboard import forecasting


class ForecastEdgeCases(unittest.TestCase):
    def setUp(self):
        self.forecasters = [
            (forecasting.forecast_recurring_revenue, "recurring_revenue"),
            (forecasting.forecast_ticket_volume, "tickets_opened"),
        ]

    def dataset(self, column, values):
        return pd.DataFrame({
            "month": pd.date_range("2024-01-01", periods=len(values), freq="MS"),
            column: pd.Series(values, dtype=float),
        })

    def test_empty_selection_returns_empty_schema(self):
        for forecast, column in self.forecasters:
            with self.subTest(metric=column):
                result = forecast(self.dataset(column, []), periods=3)
                self.assertTrue(result.empty)
                self.assertEqual(list(result.columns), ["month", column])
                self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["month"]))

    def test_single_month_repeats_observed_total(self):
        for forecast, column in self.forecasters:
            with self.subTest(metric=column):
                data = pd.DataFrame({
                    "month": pd.to_datetime(["2024-01-01", "2024-01-01"]),
                    column: [10.0, 20.0],
                })
                original = data.copy(deep=True)
                result = forecast(data, periods=3)
                self.assertEqual(result[column].tolist(), [30.0, 30.0, 30.0])
                self.assertEqual(
                    result["month"].dt.strftime("%Y-%m").tolist(),
                    ["2024-02", "2024-03", "2024-04"],
                )
                pd.testing.assert_frame_equal(data, original)

    def test_zero_horizon_returns_empty_schema(self):
        for forecast, column in self.forecasters:
            for values in ([], [10.0], [10.0, 20.0]):
                with self.subTest(metric=column, values=values):
                    result = forecast(self.dataset(column, values), periods=0)
                    self.assertTrue(result.empty)
                    self.assertEqual(list(result.columns), ["month", column])

    def test_negative_horizon_is_rejected_even_without_data(self):
        for forecast, column in self.forecasters:
            for values in ([], [10.0], [10.0, 20.0]):
                with self.subTest(metric=column, values=values):
                    with self.assertRaisesRegex(ValueError, "periods must be non-negative"):
                        forecast(self.dataset(column, values), periods=-1)

    def test_multi_month_linear_trend_is_preserved(self):
        for forecast, column in self.forecasters:
            with self.subTest(metric=column):
                result = forecast(self.dataset(column, [10.0, 20.0, 30.0]), periods=2)
                np.testing.assert_allclose(result[column], [40.0, 50.0])
                self.assertEqual(
                    result["month"].dt.strftime("%Y-%m").tolist(), ["2024-04", "2024-05"]
                )


if __name__ == "__main__":
    unittest.main()
