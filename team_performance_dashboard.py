import streamlit as st
import pandas as pd
import datetime
import requests
import json
import os
import plotly.express as px

# Constants
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=EGP"
DATA_FILE = "portfolio_data.json"

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        st.session_state.data = json.load(f)
else:
    st.session_state.data = {
        'salary_usd': 0.0,
        'exchange_rate': 0.0,
        'savings_usd': [],
        'savings_egp': [],
        'gold': [],
        'etfs': [],
        'real_estate': [],
        'cash_usd': 0.0,
        'cash_egp': 0.0
    }

# Sidebar settings
st.sidebar.header("Settings")
salary_usd = st.sidebar.number_input("Monthly Salary (USD)", value=st.session_state.data['salary_usd'], step=100.0)
st.session_state.data['salary_usd'] = salary_usd

# Currency display toggle
currency_display = st.sidebar.radio("Display Currency", ["USD", "EGP"])

# Fetch exchange rate
try:
    response = requests.get(EXCHANGE_API_URL)
    exchange_rate = response.json()['rates']['EGP']
except:
    exchange_rate = 50.0  # Fallback rate
st.session_state.data['exchange_rate'] = exchange_rate
st.sidebar.write(f"Current USD to EGP: {exchange_rate:.2f}")

# Main dashboard
st.title("📊 Investment Portfolio Tracker")

# Aggregating values
savings_usd_total = sum([x['amount'] for x in st.session_state.data['savings_usd']])
savings_egp_total = sum([x['amount'] for x in st.session_state.data['savings_egp']])
gold_total_egp = sum([x['current_price'] * x['grams'] for x in st.session_state.data['gold']])
etf_total_usd = sum([x['shares'] * x['current_price'] for x in st.session_state.data['etfs']])
real_estate_total = sum([x['estimated_value'] for x in st.session_state.data['real_estate']])
cash_usd = st.session_state.data['cash_usd']
cash_egp = st.session_state.data['cash_egp']

# Currency conversion function
def to_display_currency(usd=0.0, egp=0.0):
    try:
        usd = float(usd) if usd is not None else 0.0
        egp = float(egp) if egp is not None else 0.0
    except (TypeError, ValueError):
        usd = 0.0
        egp = 0.0

    if currency_display == "USD":
        return usd + (egp / exchange_rate if exchange_rate else 0.0)
    else:
        return egp + (usd * exchange_rate if exchange_rate else 0.0)


total_portfolio_value = to_display_currency(
    usd=savings_usd_total + etf_total_usd + cash_usd,
    egp=savings_egp_total + gold_total_egp + real_estate_total + cash_egp
)

st.metric("💼 Total Portfolio Value", f"{total_portfolio_value:,.2f} {currency_display}")

# Tabs for different assets
tabs = st.tabs(["Savings", "Gold", "ETFs", "Real Estate", "Cash", "Analytics"])

# Savings Tab
with tabs[0]:
    st.subheader("💵 Savings Overview")
    st.write("Total in USD:", savings_usd_total)
    st.write("Total in EGP:", savings_egp_total)

    if st.checkbox("Add USD Saving"):
        amount = st.number_input("Amount (USD)", step=10.0)
        st.session_state.data['savings_usd'].append({"amount": amount, "date": str(datetime.date.today())})

    if st.checkbox("Add EGP Saving"):
        amount = st.number_input("Amount (EGP)", step=100.0)
        st.session_state.data['savings_egp'].append({"amount": amount, "date": str(datetime.date.today())})

# Gold Tab
with tabs[1]:
    st.subheader("🥇 Gold Holdings")
    if st.checkbox("Add Gold Coin"):
        carat = st.selectbox("Carat", [21, 24])
        grams = st.number_input("Weight (grams)", step=0.1)
        price_per_gram = st.number_input("Current Price per Gram (EGP)", step=10.0)
        st.session_state.data['gold'].append({
            "carat": carat,
            "grams": grams,
            "current_price": price_per_gram
        })

# ETFs Tab
with tabs[2]:
    st.subheader("📈 ETFs")
    if st.checkbox("Add ETF"):
        ticker = st.text_input("Ticker")
        shares = st.number_input("Shares", step=1.0)
        purchase_price = st.number_input("Purchase Price", step=1.0)
        current_price = st.number_input("Current Price", step=1.0)
        st.session_state.data['etfs'].append({
            "ticker": ticker,
            "shares": shares,
            "purchase_price": purchase_price,
            "current_price": current_price
        })

# Real Estate Tab
with tabs[3]:
    st.subheader("🏠 Real Estate")
    if st.checkbox("Add Property Share"):
        name = st.text_input("Property Name")
        paid_amount = st.number_input("Paid Installment to Date (EGP)", step=1000.0)
        estimated_value = st.number_input("Estimated Current Value (EGP)", step=1000.0)
        st.session_state.data['real_estate'].append({
            "name": name,
            "paid_amount": paid_amount,
            "estimated_value": estimated_value
        })

# Cash Tab
with tabs[4]:
    st.subheader("💵 Cash")
    st.session_state.data['cash_usd'] = st.number_input("Cash in USD", value=st.session_state.data['cash_usd'], step=10.0)
    st.session_state.data['cash_egp'] = st.number_input("Cash in EGP", value=st.session_state.data['cash_egp'], step=100.0)

# Analytics Tab
with tabs[5]:
    st.subheader("📊 Portfolio Insights")

    labels = ['Savings USD', 'Savings EGP', 'Gold', 'ETFs', 'Real Estate', 'Cash']
    values = [
        to_display_currency(usd=savings_usd_total),
        to_display_currency(egp=savings_egp_total),
        to_display_currency(egp=gold_total_egp),
        to_display_currency(usd=etf_total_usd),
        to_display_currency(egp=real_estate_total),
        to_display_currency(usd=cash_usd, egp=cash_egp)
    ]
    fig = px.pie(values=values, names=labels, title="Portfolio Allocation")
    st.plotly_chart(fig)

    # Savings trend
    all_savings = st.session_state.data['savings_usd'] + st.session_state.data['savings_egp']
    if all_savings:
        df_savings = pd.DataFrame(all_savings)
        df_savings['date'] = pd.to_datetime(df_savings['date'])
        df_monthly = df_savings.groupby(df_savings['date'].dt.to_period('M')).sum().reset_index()
        df_monthly['date'] = df_monthly['date'].dt.to_timestamp()
        st.line_chart(df_monthly.set_index('date'))

# Save data to file
with open(DATA_FILE, "w") as f:
    json.dump(st.session_state.data, f, indent=2)
