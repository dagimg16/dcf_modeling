"""
All core DCF valuation logic: terminal value, PVs, enterprise/equity value, share price
"""
import yfinance as yf
import pandas as pd


def get_terminal_value(fcf_projection, wacc, terminal_growth = 0.02):
    final_year_fcf = fcf_projection.iloc[-1]
    tv = (final_year_fcf * (1 + terminal_growth))/(wacc - terminal_growth)
    return round(tv,2)

def get_pv_tv(tv, wacc, forecast_years = 5):
    pv_tv= tv/((1 + wacc) ** forecast_years)
    return round(pv_tv, 2)

def get_enterprise_value(pv_fcf, pv_tv):
    pv_fcf_sum = pv_fcf.sum()
    return round(pv_fcf_sum + pv_tv, 2)

def get_equity_value(ev, net_debt):
    return round(ev - net_debt, 2)

def get_implied_share_price(share_outstanding, equity_value):
    return round(equity_value / share_outstanding,2)

def get_risk_free_rate():
    """
    Get the current 10-year Treasury yield (risk-free rate) from an API.
    """
    try:
        tnx = yf.Ticker("^TNX")
        current_yield = tnx.history(period="1d")['Close'].iloc[-1] * 0.01
        return round(current_yield, 3)
    except:
        return 0.04

def get_wacc(stock):
    market_cap = stock.info.get('marketCap', 0)

    total_debt = stock.balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in stock.balance_sheet.index else 0

    beta = stock.info.get('beta', 1)

    # Get Interest Expense & Total Revenue to estimate Cost of Debt (Rd)
    interest_expense = stock.financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in stock.financials.index else 0
    cost_of_debt = abs(interest_expense / total_debt) if total_debt and not pd.isna(interest_expense) else 0.05 # Default 5% if no data

    tax_rate = 0.21  # Default to 21%

    # Get Risk-Free Rate and Market Return (estimated ~8%)
    risk_free_rate = get_risk_free_rate()
    market_return = 0.08

    #Calculate Cost of Equity (Re) using CAPM
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
    
    # Total Value (V = E + D)
    total_value = market_cap + total_debt

    # Calculate WACC
    wacc = (market_cap / total_value * cost_of_equity) + (total_debt / total_value * cost_of_debt * (1 - tax_rate))

    return round(wacc, 4), round(beta, 2), cost_of_debt, tax_rate, risk_free_rate, market_return, cost_of_equity, total_debt, market_cap, total_value     

def get_ufcf_pv(ufcf, wacc): 
    pv_ufcf = []
    
    for t, fcf in enumerate(ufcf, start=1):
        pv = fcf/((1 + wacc) ** t)
        pv_ufcf.append(pv)

    return pd.Series(pv_ufcf, ufcf.index) 
