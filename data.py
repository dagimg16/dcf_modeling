"""
Handles all data fetching and projection logic using yfinance
"""
import yfinance as yf
import pandas as pd
from utils import (change_timestamp_to_year, get_best_match_index)

def get_spy500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    df = tables[0]
    spy_tickers= [x for x in df['Symbol']]

    return spy_tickers


#5 year revenue projection
def get_revenue_projection(stock, growth_rate=None):
    income_stmt = stock.income_stmt.sort_index(axis=1)
    revenue = income_stmt.loc['Total Revenue'].dropna() / 1e9

    avg_growth = revenue.pct_change().dropna().mean()

    growth = growth_rate if growth_rate is not None else avg_growth

    revenue_projection = []
    projection_years=[]

    last_year = income_stmt.columns[-1].year
    last_year_revenue = revenue.iloc[-1]

    for years in range(5):
        next_year_revenue = (last_year_revenue * (1 + growth))
        revenue_projection.append(round(next_year_revenue, 2))
        last_year_revenue = next_year_revenue
    
        projection_years.append(last_year + (years + 1))
    
    projections = pd.Series(revenue_projection, projection_years) 

    return round(revenue,2), projections, avg_growth

def get_ebit_projection(stock, revenue_projection, past_revenue, growth_rate=None):
    income_s = stock.income_stmt
    line_item = 'Operating Income'
    # income_s[income_s.index.to_series().str.contains('Operating Income', regex= True)].index[0]

    if line_item in income_s.index:
        ebit = income_s.loc[line_item].dropna() / 1e9
        ebit = ebit.sort_index()

        margin = (ebit / past_revenue).mean()

        growth = growth_rate if growth_rate is not None else margin

        projected_ebit = [round(rev * growth, 2) for rev in revenue_projection]

        projected_ebit = pd.Series(projected_ebit, revenue_projection.index) 

        return ebit, projected_ebit, margin
    else:
        print(f"Operating Income not found for ticker {stock.ticker}")

def get_net_debt(stock):
    if 'Cash Cash Equivalents And Short Term Investments' in stock.balance_sheet.index:  
        bs = stock.balance_sheet
        line_item = bs[bs.index.to_series().str.contains('Long Term Debt', regex=True)].index[0]
        cash = bs.loc['Cash Cash Equivalents And Short Term Investments'].iloc[0] / 1e9
        debt = bs.loc[line_item].iloc[0] / 1e9
        if pd.isna(debt):
            debt=0
        return cash, debt, debt - cash
    else:
        print(f"Cash Cash Equivalents And Short Term Investments for ticker {stock.ticker}")

def get_shares_outstanding(stock):
    return round(stock.info.get('sharesOutstanding', 0) / 1e9, 2)

def get_depreciation_and_amortization(stock, projection, past_revenue):
    cf = stock.cashflow.index
    target = 'Depreciation And Amortization'
    line_item = get_best_match_index(cf, target)

    if pd.notnull(line_item):
        da = stock.cashflow.loc[line_item].dropna()/1e9
        da_rate = (da/past_revenue).mean()
        da = change_timestamp_to_year(da)
        return da, da_rate * projection
    else:
        print(f"Depreciation & Amortization not found for ticker {stock.ticker}")
  