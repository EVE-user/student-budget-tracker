import streamlit as st
import pandas as pd
import hashlib
import json
import os
from datetime import date

st.set_page_config(page_title="Uni Budget Tracker", page_icon="💸", layout="centered")

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "budget_data.json")

# --- Helper Functions for Storage & Security ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==========================================
# 1. LOGIN & SIGN-UP SCREEN
# ==========================================
if st.session_state.logged_in_user is None:
    st.title("🔐 Student Budget Tracker")
    st.caption("Log in or create an account to save your expenses.")

    tab_login, tab_signup = st.tabs(["Log In", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Log In")

            if login_btn:
                user_record = data["users"].get(username)
                if user_record and user_record["password"] == hash_password(password):
                    st.session_state.logged_in_user = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_signup:
        with st.form("signup_form"):
            new_user = st.text_input("Choose a Username").strip().lower()
            new_pass = st.text_input("Choose a Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account")

            if signup_btn:
                if not new_user or not new_pass:
                    st.warning("Please enter both a username and password.")
                elif new_user in data["users"]:
                    st.error("That username is already taken.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    data["users"][new_user] = {
                        "password": hash_password(new_pass),
                        "currency": "MUR (Rs)",
                        "budget": 10000.0,
                        "expenses": []
                    }
                    save_data(data)
                    st.success("Account created! Switch to the 'Log In' tab to sign in.")

# ==========================================
# 2. MAIN BUDGET TRACKER (AFTER LOGIN)
# ==========================================
else:
    user = st.session_state.logged_in_user
    user_data = data["users"][user]

    # Top Header & Logout
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title(f"💸 Welcome, {user.capitalize()}!")
    with col_logout:
        if st.button("Log Out"):
            st.session_state.logged_in_user = None
            st.rerun()

    # Sidebar: Monthly Budget Setup (Saved per user)
    st.sidebar.header("⚙️ Monthly Settings")
    currencies = ["MUR (Rs)", "TZS", "USD ($)"]
    curr_idx = currencies.index(user_data.get("currency", "MUR (Rs)"))
    currency = st.sidebar.selectbox("Currency", currencies, index=curr_idx)
    monthly_budget = st.sidebar.number_input(
        "Monthly Allowance / Budget",
        min_value=0.0,
        value=float(user_data.get("budget", 10000.0)),
        step=500.0
    )

    if currency != user_data.get("currency") or monthly_budget != user_data.get("budget"):
        user_data["currency"] = currency
        user_data["budget"] = monthly_budget
        save_data(data)

    # Form to Add a New Expense
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Date", value=date.today())
            category = st.selectbox("Category", ["Food & Snacks", "Shopping", "Transport", "Subscriptions", "Investing / Savings", "Other"])
        with col2:
            item = st.text_input("What did you buy?", placeholder="e.g. Jumbo groceries, coffee")
            amount = st.number_input(f"Amount ({currency})", min_value=0.0, step=50.0)

        submitted = st.form_submit_button("➕ Add Expense")
        if submitted and amount > 0:
            user_data["expenses"].append({
                "Date": str(exp_date),
                "Category": category,
                "Item": item or category,
                "Amount": amount
            })
            save_data(data)
            st.success(f"Saved {item or category} ({currency} {amount:,.0f})")
            st.rerun()

    # Summary Metrics
    df = pd.DataFrame(user_data["expenses"])
    total_spent = df["Amount"].sum() if not df.empty else 0.0
    remaining = monthly_budget - total_spent

    m1, m2, m3 = st.columns(3)
    m1.metric("Budget", f"{monthly_budget:,.0f}")
    m2.metric("Total Spent", f"{total_spent:,.0f}")
    m3.metric("Remaining", f"{remaining:,.0f}", delta=f"{remaining:,.0f}")

    # Breakdown Chart & Table
    if not df.empty:
        st.subheader("📊 Spending by Category")
        category_totals = df.groupby("Category")["Amount"].sum()
        st.bar_chart(category_totals)

        st.subheader("🧾 Recent Transactions")
        st.dataframe(df.iloc[::-1], use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Expenses (CSV)", csv, f"{user}_budget.csv", "text/csv")
    else:
        st.info("Add your first expense above to start tracking!")


