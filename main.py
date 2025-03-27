import pandas as pd
import yfinance as yf
from datetime import datetime as dt


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
        
def get_wacc(ticker):
    stock= yf.Ticker(ticker)

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
    
#past 4 year revenue growth
def get_revenue_growth(ticker):
    stock= yf.Ticker(ticker)
    revenue= stock.income_stmt.loc['Total Revenue'].dropna() /1e9
    revenue = revenue.sort_index()

    growth_rates = revenue.pct_change()
    avg_growth = pd.Series(growth_rates[1:]).mean()

    return revenue, avg_growth
    
#5 year revenue projection
def get_revenue_projection(ticker, growth_rate):
    stock= yf.Ticker(ticker)
    revenue_projection = []
    projection_years=[]
    last_year = stock.income_stmt.columns[0].year
    last_year_revenue= stock.income_stmt.loc['Total Revenue'].iloc[0]/1e9
    
    for x in range(5):
        next_year_revenue = (last_year_revenue * (1 + growth_rate))
        revenue_projection.append(round(next_year_revenue, 2))
        last_year_revenue = next_year_revenue
    
        projection_years.append(last_year + (x + 1))
        
    return pd.Series(revenue_projection, projection_years) 

def get_ebit_margin(ticker):
    stock= yf.Ticker(ticker)
    if 'Operating Income' in stock.income_stmt.index:
        operating_income = stock.income_stmt.loc['Operating Income'].dropna()
        revenue = stock.income_stmt.loc['Total Revenue'].dropna()
        operating_margin = operating_income/ revenue
        
        return operating_income/1e9, operating_margin,  operating_margin.mean()
        
    else:
        print("Operating Income not found")
        
def get_ebit_projection(revenue_projection, ebit_margin):
    ebit_projection = []
    
    for revenue in revenue_projection:
        ebit = revenue * ebit_margin
        ebit_projection.append(round(ebit, 2))
    return pd.Series(ebit_projection, revenue_projection.index) 

def get_depreciation_and_amortization(ticker, projection):
    stock= yf.Ticker(ticker)
    if 'Depreciation And Amortization' in stock.cashflow.index:
        da = stock.cashflow.loc['Depreciation And Amortization'].dropna()/1e9
        revenue= stock.income_stmt.loc['Total Revenue'].dropna()/1e9
        da_rate = (da/revenue).mean()
        da = change_timestamp_to_year(da)
        return da, da_rate * projection
    else:
        print("Depreciation & Amortization not found")

def get_fcf_pv(fcf_projection, wacc):
    discounted = []
    
    for t, fcf in enumerate(fcf_projection, start=1):
        pv = fcf/((1 + wacc) ** t)
        discounted.append(pv)
        
    return pd.Series(discounted, fcf_projection.index)  

def get_terminal_value(fcf_projection, wacc):
    terminal_growth = 0.02
    final_year_fcf = fcf_projection.iloc[-1]
    
    terminal_value = (final_year_fcf * (1 + terminal_growth))/(wacc - terminal_growth)
    
    return terminal_value

def get_pv_tv(tv, wacc):
    n = 5
    pv_tv= tv/((1 + wacc) ** n)

    return pv_tv

def get_enterprise_value(pv_fcf, pv_tv):
    pv_fcf_sum = pv_fcf.sum()
    
    ev = pv_fcf_sum + pv_tv

    return ev
def get_net_debt(ticker):  
    stock= yf.Ticker(ticker)
    cash = stock.balance_sheet.loc['Cash Cash Equivalents And Short Term Investments'].iloc[0] 
    debt = stock.balance_sheet.loc['Long Term Debt'].iloc[0] 
    net_debt = debt - cash 

    return cash/1e9, debt/1e9, net_debt/1e9

def get_equity_value(ev, net_debt):
    return ev - net_debt

def get_implied_share_price(ticker, equity_value):
    stock= yf.Ticker(ticker)
    share_outstanding = stock.info['sharesOutstanding']/1e9
    per_share_value = equity_value / share_outstanding

    return share_outstanding, per_share_value

def change_timestamp_to_year(value):
    return value.groupby(value.index.year).sum()

def get_total_cash(ticker, past_revenue):
    stock= yf.Ticker(ticker)
    total_cash = stock.balance_sheet.loc['Cash Cash Equivalents And Short Term Investments'].dropna() /1e9
    total_cash = change_timestamp_to_year(total_cash)
    cash_margin = (total_cash / past_revenue).mean()

    return cash_margin, total_cash

def get_receivables(ticker, past_recenue):
    stock= yf.Ticker(ticker)
    receivables = stock.balance_sheet.loc['Receivables'].dropna() /1e9
    receivables = change_timestamp_to_year(receivables)
    receivables_margin = (receivables/ past_revenue).mean()

    return receivables_margin, receivables
    
def get_inventory(ticker, past_recenue):
    stock= yf.Ticker(ticker)
    inventory = stock.balance_sheet.loc['Inventory'].dropna() /1e9
    inventory = change_timestamp_to_year(inventory)
    inventory_margin = (inventory/ past_revenue).mean()

    return inventory_margin, inventory
    
def get_payables(ticker, past_recenue):
    stock= yf.Ticker(ticker)
    payables = stock.balance_sheet.loc['Payables'].dropna() /1e9
    payables = change_timestamp_to_year(payables)
    payables_margin = (payables/ past_revenue).mean()

    return payables_margin, payables

def get_capEx(ticker, past_revenue):
    stock= yf.Ticker(ticker)
    
    if 'Capital Expenditure' in stock.cashflow.index:
        capex = abs(stock.cashflow.loc['Capital Expenditure'].dropna()/1e9)
        capex = change_timestamp_to_year(capex)
        capex_margin = (capex/past_revenue).mean()
        
        return capex_margin, capex
    else:
        print("Capital Expenditure not found")
def get_ufcf_pv(ufcf, wacc): 
    pv_ufcf = []
    
    for t, fcf in enumerate(ufcf, start=1):
        pv = fcf/((1 + wacc) ** t)
        pv_ufcf.append(pv)

    return pd.Series(pv_ufcf, ufcf.index) 

# Get Ticker from the user
ticker = "AAPL"

#Call functions to get data about the ticker and start projection
past_revenue, rate = get_revenue_growth(ticker)
wacc, beta, cost_of_debt, tax_rate, risk_free_rate, market_return, cost_of_equity, total_debt, market_cap, total_value = get_wacc(ticker)
projection = get_revenue_projection(ticker=ticker, growth_rate= rate)
past_ebit, past_ebit_margin, ebit_margin= get_ebit_margin(ticker)
ebit = get_ebit_projection(projection, ebit_margin)
past_da, da_estimite = get_depreciation_and_amortization(ticker, projection)

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

cash_margin, past_total_cash = get_total_cash(ticker, past_revenue)
total_cash_estimite = projection * cash_margin
total_cash_output = pd.concat([past_total_cash, total_cash_estimite])
cash_margin_output = total_cash_output / revenue_output

## Receivable forecast

receivable_margin, past_receivales = get_receivables(ticker, past_revenue)
receivable_estimite = projection * receivable_margin
receivable_output = pd.concat([past_receivales, receivable_estimite])
receivable_margin_output = receivable_output/ revenue_output

## Inventory forecast

inventory_margin, past_inventory = get_inventory(ticker, past_revenue)
inventory_estimite = projection * inventory_margin
inventory_output = pd.concat([past_inventory, inventory_estimite])
inventory_margin_output = inventory_output/ revenue_output

## Payable forecast

payable_margin, past_payable = get_payables(ticker, past_revenue)
payable_estimite = projection * payable_margin
payable_output = pd.concat([past_payable, payable_estimite])
payable_margin_output = payable_output/ revenue_output

## CAP EX forecast
capex_margin, past_capex = get_capEx(ticker, past_revenue)
capex_estimite = projection * capex_margin
capex_output = pd.concat([past_capex, capex_estimite])
capex_margin_output = capex_output/ revenue_output

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

tv_output = get_terminal_value(ufcf_output, wacc)
pv_tv_output = get_pv_tv(tv_output, wacc)
ev_output = get_enterprise_value(pv_ufcf_output, pv_tv_output)
cash, debt, net_debt = get_net_debt(ticker)
equity_value_output = get_equity_value(ev_output, net_debt)
share_count, share_price = get_implied_share_price(ticker, equity_value_output)

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

print(operating_data_df)