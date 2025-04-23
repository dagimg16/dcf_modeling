import streamlit as st

st.set_page_config(page_title="Finance Hub", layout="wide")

st.title("📈 Welcome to Finance Hub")
st.markdown("Get the latest financial headlines and run a DCF analysis on any stock.")

# Search bar
ticker = st.text_input("🔍 Search by Stock Ticker", key="ticker_input")

if ticker:
    # Store input in session state
    st.session_state.ticker = ticker.upper()
    # Navigate to DCF page
    st.switch_page("pages/app.py")

# Mocked headlines
st.subheader("📰 Market Headlines")
st.write("- Apple hits new all-time high")
st.write("- Nvidia announces next-gen AI chips")
st.write("- Tesla sees surge in deliveries this quarter")