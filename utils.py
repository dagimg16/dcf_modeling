"""
General utility functions for formatting, conversions, reusable helpers
"""
import pandas as pd
import difflib


def change_timestamp_to_year(value):
    return value.groupby(value.index.year).sum()


def forecast_balance_item(statement, line_item, projection, stock, past_revenue, revenue_output):

    margin, historical_values = get_margin_item(stock, statement, line_item, past_revenue)

    forecast = projection * margin

    full_series = pd.concat([historical_values, forecast])

    margin_output = full_series / revenue_output

    full_series = full_series if not margin_output.isna().all() else pd.Series(0, index=margin_output.index)
    
    return full_series, margin_output

def get_margin_item(stock, statement, line_item, past_revenue):
    source = getattr(stock, statement)

    if line_item in source.index:
        values = source.loc[line_item].dropna() / 1e9
        if line_item == "Capital Expenditure":
            values = abs(values)
        values = change_timestamp_to_year(values)    
    else:
        values = pd.Series(dtype=float)

    # Ensure past_revenue and values are aligned and safe
    try:
        margin = (values / past_revenue).mean()
    except Exception as e:
        margin = float('nan')  

    return margin, values

def get_best_match_index(index_list, target_name, cutoff=0.6):
    # Check for exact match first
    if target_name in index_list:
        return target_name
    else:
        # Find closest matches using difflib
        close_matches = difflib.get_close_matches(target_name, index_list, n=1, cutoff=cutoff)
        if close_matches:
            return close_matches[0]
        else:
            return None 