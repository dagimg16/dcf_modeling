"""
General utility functions for formatting, conversions, reusable helpers
"""
import pandas as pd


def change_timestamp_to_year(value):
    return value.groupby(value.index.year).sum()


def forecast_balance_item(statement, line_item, projection, stock, past_revenue, revenue_output):

    margin, historical_values = get_margin_item(stock, statement, line_item, past_revenue)

    forecast = projection * margin

    full_series = pd.concat([historical_values, forecast])

    margin_output = full_series / revenue_output

    return full_series, margin_output

def get_margin_item(stock, statement, line_item, past_revenue):
    source = getattr(stock, statement)

    if line_item == "Capital Expenditure":
        values = abs(source.loc[line_item].dropna() / 1e9)
    else:
        values = source.loc[line_item].dropna() / 1e9

    values = change_timestamp_to_year(values)

    margin = (values / past_revenue).mean()

    return margin, values

