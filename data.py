"""
Handles all data fetching and projection logic using yfinance
"""
import yfinance as yf
import pandas as pd
from utils import (change_timestamp_to_year)

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
    if 'Operating Income' in stock.income_stmt.index:
        ebit = stock.income_stmt.loc['Operating Income'].dropna() / 1e9
        ebit = ebit.sort_index()

        margin = (ebit / past_revenue).mean()

        growth = growth_rate if growth_rate is not None else margin

        projected_ebit = [round(rev * growth, 2) for rev in revenue_projection]

        projected_ebit = pd.Series(projected_ebit, revenue_projection.index) 

        return ebit, projected_ebit, margin
    else:
        print("Operating Income not found")

def get_net_debt(stock):  
    bs = stock.balance_sheet
    cash = bs.loc['Cash Cash Equivalents And Short Term Investments'].iloc[0] / 1e9
    debt = bs.loc['Long Term Debt'].iloc[0] / 1e9
    return cash, debt, debt - cash

def get_shares_outstanding(stock):
    return round(stock.info.get('sharesOutstanding', 0) / 1e9, 2)

def get_depreciation_and_amortization(stock, projection):
    if 'Depreciation And Amortization' in stock.cashflow.index:
        da = stock.cashflow.loc['Depreciation And Amortization'].dropna()/1e9
        revenue= stock.income_stmt.loc['Total Revenue'].dropna()/1e9
        da_rate = (da/revenue).mean()
        da = change_timestamp_to_year(da)
        return da, da_rate * projection
    else:
        print("Depreciation & Amortization not found")
  