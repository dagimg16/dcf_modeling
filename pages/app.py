import pandas as pd
import yfinance as yf
from datetime import datetime as dt
import streamlit as st
pd.set_option('future.no_silent_downcasting', True)

from dcf import ( get_terminal_value, get_pv_tv, get_enterprise_value, get_equity_value, get_implied_share_price, get_wacc, get_ufcf_pv)
from data import (get_revenue_projection, get_ebit_projection, get_net_debt, get_shares_outstanding, get_depreciation_and_amortization, get_spy500_tickers)
from utils import (change_timestamp_to_year, forecast_balance_item)

# Run the selected page

st.set_page_config(page_title="DCF Valuation App", layout="wide")

ticker = st.session_state.get("ticker", "")

if not ticker:
    ticker = st.sidebar.text_input("Enter Ticker Symbol", value='AAPL').upper()
    st.title(f"📊 DCF Analysis for {ticker}")
    st.write("Estimate the intrinsic value of a stock using the DCF method.")
else:
    st.title(f"📊 DCF Analysis for {ticker}")
    st.write("Estimate the intrinsic value of a stock using the DCF method.")

# Get Ticker from the user
st.sidebar.header("Model Parameters")

stock= yf.Ticker(ticker)

try:
    info = stock.info
    if not info or "shortName" not in info or info["regularMarketPrice"] is None:
        raise ValueError
except Exception:
    st.error("Invalid ticker symbol or data not available. Please try again.")
    st.stop()

past_revenue, _, avg_growth = get_revenue_projection(stock)

custom_growth = st.sidebar.slider("Revenue Growth Rate", 
                                min_value = 0.01, 
                                    max_value= 0.50, 
                                        value=float(round(avg_growth,2)),
                                            step = 0.01 
                                )

_, projection, _ = get_revenue_projection(stock,custom_growth)

#Call functions to get data about the ticker and start projection

wacc, beta, cost_of_debt, tax_rate, risk_free_rate, market_return, cost_of_equity, total_debt, market_cap, total_value = get_wacc(stock)

past_ebit, _, ebit_margin  = get_ebit_projection(stock, projection, past_revenue)

custom_ebit_margin = st.sidebar.slider("Ebit %", 
                                min_value = 0.01, 
                                    max_value= 0.70, 
                                        value=float(round(ebit_margin,2)),
                                            step = 0.01 
                                )

_, ebit ,_= get_ebit_projection(stock, projection, past_revenue, custom_ebit_margin)

past_da, da_estimite = get_depreciation_and_amortization(stock, projection, past_revenue)

wacc = st.sidebar.slider("Discount Rate (WACC)",
                        min_value=0.05, 
                            max_value=0.25,
                                value= wacc,  
                                step=0.005)
# Operating Data
past_revenue = change_timestamp_to_year(past_revenue)
revenue_output = pd.concat([past_revenue, projection])
revenue_pct_change = revenue_output.pct_change()
past_ebit = change_timestamp_to_year(past_ebit)
ebit_output = pd.concat([past_ebit, ebit])
ebit_margin_output = ebit_output / revenue_output
da_output = pd.concat([past_da, da_estimite])
da_rate_output = da_output / revenue_output

operating_data_df = pd.DataFrame(data=[revenue_output, revenue_pct_change, ebit_output, ebit_margin_output, da_output, da_rate_output],
                                    index=['Revenue','Revenue %', 'EBIT', 'EBIT %','Depreciation', 'Depreciation %'])

# Balance Sheet
## Total Cash forecast
total_cash_output, cash_margin_output = forecast_balance_item(
    "balance_sheet", "Cash Cash Equivalents And Short Term Investments", projection, stock, past_revenue, revenue_output )

## Receivable forecast
receivable_output, receivable_margin_output = forecast_balance_item(
    "balance_sheet", "Receivables" , projection, stock, past_revenue, revenue_output )

## Inventory forecast
inventory_output, inventory_margin_output = forecast_balance_item(
    "balance_sheet","Inventory", projection, stock, past_revenue, revenue_output )

## Payable forecast
payable_output, payable_margin_output = forecast_balance_item(
    "balance_sheet","Payables", projection, stock, past_revenue, revenue_output )

## CAP EX forecast
capex_output, capex_margin_output = forecast_balance_item(
    "cashflow", "Capital Expenditure", projection, stock, past_revenue, revenue_output)

balance_sheet_df = pd.DataFrame(data=[total_cash_output, cash_margin_output, receivable_output, receivable_margin_output,
                                        inventory_output,inventory_margin_output, payable_output, payable_margin_output, 
                                                capex_output, capex_margin_output],
                                                    index=['Total Cash', 'Total Cash %', 'Receivables', 'Receivables %', 'Inventories', 'Inventories %',
                                                                'Payable', 'Payable %', 'Cap Ex', 'Cap EX %'])

# Weignted Average Cost of Capital
metrics = [
    ('Beta', f"{beta:.2f}"),
    ('Cost of Debt', f"{cost_of_debt:.2%}"),
    ('Tax Rate', f"{tax_rate:.0%}"),
    ('Risk Free Rate', f"{risk_free_rate:.2%}"),
    ('Market Risk Premium', f"{market_return:.2%}"),
    ('Cost of Equity', f"{cost_of_equity:.2%}"),
    ('Total Debt', f"${total_debt/1e9:,.0f}"),
    ('Total Equity', f"${market_cap/1e9:,.0f}"),
    ('Total Capital', f"${total_value/1e9:,.0f}"),
    ('WACC', f"{wacc:.2%}")
]

wacc_df = pd.DataFrame(metrics, columns=['', 'Value']).set_index('')

# Build Up Free Cash Flow
ebiat_output = ebit_output * (1 - tax_rate)
operating_wc = receivable_output + inventory_output - payable_output
delta_operating_wc = operating_wc.diff()
ufcf_output = ebiat_output + da_output - capex_output - delta_operating_wc
pv_ufcf_output = get_ufcf_pv(ufcf_output, wacc)

cash_flow_df = pd.DataFrame(data=[revenue_output, ebit_output, ebiat_output, da_output, receivable_output,
                                        inventory_output, payable_output, capex_output, delta_operating_wc, 
                                            ufcf_output, pv_ufcf_output],                
                                                index=['Revenue','EBIT','EBIT After Tax' ,'Depreciation' , 'Receivables',
                                                        'Inventories', 'Payable', 'Cap Ex', 'Change in NWC(-)','Unlevered FCF',
                                                                'Present Value of FCF'])
# Terminal Value and Intrinsic Value
tv_output, default_growth = get_terminal_value(ufcf_output, wacc)

terminal_growth = st.sidebar.slider("Terminal Growth Rate", 
                                    min_value=0.005, 
                                        max_value=0.05,
                                            value= float(round(default_growth, 4)), 
                                                step=0.0025)

tv_output, _ = get_terminal_value(ufcf_output, wacc, terminal_growth)

pv_tv_output = get_pv_tv(tv_output, wacc)
ev_output = get_enterprise_value(pv_ufcf_output, pv_tv_output)
cash, debt, net_debt = get_net_debt(stock)
equity_value_output = get_equity_value(ev_output, net_debt)
share_count = get_shares_outstanding(stock)
share_price = get_implied_share_price(share_count, equity_value_output)

metrics_2 = [
    ('Terminal Value', f"${tv_output:,.2f}B"),
    ('PV of Terminal Value', f"${pv_tv_output:,.2f}B"),
    ('Enterprise Value', f"${ev_output:,.2f}B"),
    ('Cash (+)', f"${cash:,.2f}B"),
    ('Debt (-)', f"${debt:,.2f}B"),
    ('Equity Value', f"${equity_value_output:,.2f}B"),
    ('Shares Outstanding', f"{share_count:,.0f}"),
    ('Implied Share Price', f"${share_price:,.2f}")
]

interinsic_value_df = pd.DataFrame(metrics_2, columns=['', 'Value']).set_index('')


st.sidebar.header("Weighted Average Cost Of Capital")
st.sidebar.table(wacc_df)

tab1, tab2, tab3, tab4 = st.tabs(["🏁 Terminal Value", "📄 Balance Sheet", "💸 FCF Build-up", "📊 Operating Data"])

with tab1:
    st.table(interinsic_value_df
                 )
    

with tab2:
    st.dataframe(balance_sheet_df.style.format("{:,.2f}"),
                 use_container_width=True,  
                 )

with tab3:
    st.dataframe(cash_flow_df.style.format("{:,.2f}"),
                 use_container_width=True,  
                 height=423

                 )
with tab4:
    st.dataframe(operating_data_df.style.format("{:,.2f}"),
                 use_container_width=True,  
                 )
