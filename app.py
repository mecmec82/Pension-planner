import json
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Financial Planning & Retirement Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 0. LOAD CONFIGURATION
# ==========================================
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "current_age": 40,
    "lump_sum_payoff_age": 57,
    "retirement_age": 60,
    "end_age": 90,
    "gross_salary": 75000.0,
    "ee_pension_pct": 5.0,
    "er_pension_pct": 10.0,
    "other_sal_sac": 0.0,
    "current_pension": 150000.0,
    "pension_growth_rate": 6.0,
    "mortgage_balance": 220000.0,
    "mortgage_rate": 4.0,
    "mortgage_monthly_payment": 1200.0,
    "desired_pension_income": 35000.0,
    "inflation_rate": 2.5,
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception as e:
            st.warning(f"Error loading {CONFIG_FILE}: {e}. Using defaults.")
    return DEFAULT_CONFIG

config = load_config()

st.title("📈 Personal Financial & Retirement Planner")

# ==========================================
# 1. SIDEBAR INPUTS (Initialized from config.json)
# ==========================================
st.sidebar.header("👤 Age & Demographics")
current_age = st.sidebar.number_input(
    "Current Age", min_value=18, max_value=56, value=int(config["current_age"]), step=1
)
lump_sum_payoff_age = int(config["lump_sum_payoff_age"])
retirement_age = st.sidebar.number_input(
    "Retirement Age (Start Drawing Pension)",
    min_value=57,
    max_value=90,
    value=int(config["retirement_age"]),
    step=1,
)
end_age = st.sidebar.number_input(
    "Target Horizon / End Age",
    min_value=retirement_age + 1,
    max_value=110,
    value=int(config["end_age"]),
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.header("💼 Income & Salary Sacrifice")
gross_salary = st.sidebar.number_input(
    "Annual Gross Salary (£)", min_value=0.0, value=float(config["gross_salary"]), step=1000.0
)
ee_pension_pct = st.sidebar.slider(
    "Employee Pension Contribution (%)", 0.0, 50.0, float(config["ee_pension_pct"]), step=0.5
)
er_pension_pct = st.sidebar.slider(
    "Employer Pension Contribution (%)", 0.0, 30.0, float(config["er_pension_pct"]), step=0.5
)
other_sal_sac = st.sidebar.number_input(
    "Other Annual Salary Sacrifice (£)",
    min_value=0.0,
    value=float(config["other_sal_sac"]),
    step=500.0,
)

st.sidebar.markdown("---")
st.sidebar.header("📊 Current Balances & Growth Rates")
current_pension = st.sidebar.number_input(
    "Current Pension Pot (£)", min_value=0.0, value=float(config["current_pension"]), step=5000.0
)
pension_growth_rate = (
    st.sidebar.slider(
        "Net Pension Growth Rate (Post-Fees) (%)", 0.0, 15.0, float(config["pension_growth_rate"]), step=0.5
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.header("🏡 Mortgage Details")
mortgage_balance = st.sidebar.number_input(
    "Current Mortgage Balance (£)", min_value=0.0, value=float(config["mortgage_balance"]), step=5000.0
)
mortgage_rate = (
    st.sidebar.slider(
        "Mortgage Interest Rate (%)", 0.0, 12.0, float(config["mortgage_rate"]), step=0.25
    )
    / 100
)
mortgage_monthly_payment = st.sidebar.number_input(
    "Monthly Mortgage Payment (£)", min_value=0.0, value=float(config["mortgage_monthly_payment"]), step=50.0
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Retirement Goals")
desired_pension_income = st.sidebar.number_input(
    "Desired Annual Net Income in Retirement (£)",
    min_value=0.0,
    value=float(config["desired_pension_income"]),
    step=1000.0,
)
inflation_rate = (
    st.sidebar.slider(
        "Expected Inflation Rate (%)", 0.0, 10.0, float(config["inflation_rate"]), step=0.25
    )
    / 100
)

# ==========================================
# 2. TAX CALCULATIONS (UK Baseline)
# ==========================================
def calculate_take_home(salary, ee_pen_pct, sal_sac):
    ee_pen_annual = salary * (ee_pen_pct / 100)
    taxable_salary = max(0.0, salary - ee_pen_annual - sal_sac)

    # Personal Allowance & Tapering above £100k
    personal_allowance = 12570.0
    if taxable_salary > 100000:
        reduction = (taxable_salary - 100000) / 2
        personal_allowance = max(0.0, personal_allowance - reduction)

    taxable_income = max(0.0, taxable_salary - personal_allowance)
    income_tax = 0.0

    basic_band = 37700.0
    higher_band = 74730.0

    if taxable_income > 0:
        income_tax += min(taxable_income, basic_band) * 0.20
    if taxable_income > basic_band:
        income_tax += min(taxable_income - basic_band, higher_band) * 0.40
    if taxable_income > (basic_band + higher_band):
        income_tax += (taxable_income - basic_band - higher_band) * 0.45

    # National Insurance (Class 1 Employee)
    ni = 0.0
    ni_threshold = 12570.0
    upper_reg_limit = 50270.0

    if taxable_salary > ni_threshold:
        ni += (min(taxable_salary, upper_reg_limit) - ni_threshold) * 0.08
    if taxable_salary > upper_reg_limit:
        ni += (taxable_salary - upper_reg_limit) * 0.02

    net_annual = taxable_salary - income_tax - ni
    return net_annual, income_tax, ni, ee_pen_annual

(
    net_take_home,
    tax_paid,
    ni_paid,
    ee_contrib_val,
) = calculate_take_home(gross_salary, ee_pension_pct, other_sal_sac)
er_contrib_val = gross_salary * (er_pension_pct / 100)
total_annual_pension_contrib = ee_contrib_val + er_contrib_val

# ==========================================
# 3. PROJECTION LOGIC (WITH LUMP-SUM PAYOFF AT 57)
# ==========================================
years = np.arange(current_age, end_age + 1)

pension_balances = []
mortgage_balances = []
desired_incomes = []
actual_incomes = []
deltas = []
lump_sum_deducted = 0.0
lump_sum_paid_at_57 = 0.0
pension_pot_at_57_pre_payoff = 0.0

curr_pension_pot = current_pension
curr_mortgage_pot = mortgage_balance
annual_mortgage_payment = mortgage_monthly_payment * 12

for yr in range(current_age, end_age + 1):
    years_from_start = yr - current_age
    inflated_desired_income = desired_pension_income * (
        (1 + inflation_rate) ** years_from_start
    )

    # --- AGE 57 SPECIAL EVENT: LUMP-SUM MORTGAGE PAYOFF ---
    if yr == lump_sum_payoff_age:
        pension_pot_at_57_pre_payoff = curr_pension_pot
        if curr_mortgage_pot > 0:
            lump_sum_paid_at_57 = min(curr_mortgage_pot, curr_pension_pot)
            curr_pension_pot -= lump_sum_paid_at_57
            curr_mortgage_pot = max(0.0, curr_mortgage_pot - lump_sum_paid_at_57)
            lump_sum_deducted = lump_sum_paid_at_57

    # 1. Accumulation Phase (Before Retirement)
    if yr < retirement_age:
        curr_pension_pot = (
            curr_pension_pot * (1 + pension_growth_rate)
            + total_annual_pension_contrib
        )
        actual_inc = 0.0
        delta = -inflated_desired_income

        if curr_mortgage_pot > 0 and yr != lump_sum_payoff_age:
            interest = curr_mortgage_pot * mortgage_rate
            principal_paid = min(
                curr_mortgage_pot, annual_mortgage_payment - interest
            )
            if principal_paid < 0:
                curr_mortgage_pot += interest - annual_mortgage_payment
            else:
                curr_mortgage_pot = max(0.0, curr_mortgage_pot - principal_paid)

    # 2. Decumulation Phase (Retirement)
    else:
        curr_mortgage_pot = 0.0
        actual_inc = min(curr_pension_pot, inflated_desired_income)
        curr_pension_pot = (
            curr_pension_pot - actual_inc
        ) * (1 + pension_growth_rate)
        curr_pension_pot = max(0.0, curr_pension_pot)
        delta = actual_inc - inflated_desired_income

    pension_balances.append(curr_pension_pot)
    mortgage_balances.append(curr_mortgage_pot)
    desired_incomes.append(
        inflated_desired_income if yr >= retirement_age else 0.0
    )
    actual_incomes.append(actual_inc)
    deltas.append(delta if yr >= retirement_age else 0.0)

df_proj = pd.DataFrame(
    {
        "Age": years,
        "Pension Balance (£)": pension_balances,
        "Mortgage Balance (£)": mortgage_balances,
        "Desired Annual Income (£)": desired_incomes,
        "Projected Actual Income (£)": actual_incomes,
        "Income Delta (£)": deltas,
    }
)

# ==========================================
# 4. DASHBOARD DISPLAY & METRICS
# ==========================================
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        label="Est. Monthly Take-Home",
        value=f"£{net_take_home / 12:,.2f}",
        help="Net pay after Tax, NI, EE Pension, and Salary Sacrifice",
    )

with col_m2:
    st.metric(
        label="Mortgage Payoff at Age 57",
        value=f"£{lump_sum_paid_at_57:,.0f}",
        delta=f"-£{lump_sum_paid_at_57:,.0f} from Pension Pot",
        delta_color="inverse",
    )

with col_m3:
    pot_at_retire = df_proj.loc[
        df_proj["Age"] == retirement_age, "Pension Balance (£)"
    ].values[0]
    st.metric(
        label=f"Pension Pot at Age {retirement_age}",
        value=f"£{pot_at_retire:,.0f}",
    )

with col_m4:
    depletion_rows = df_proj[
        (df_proj["Age"] >= retirement_age)
        & (df_proj["Pension Balance (£)"] <= 0)
    ]
    runout_age = (
        f"Age {depletion_rows['Age'].iloc[0]}"
        if not depletion_rows.empty
        else "Sustainable"
    )
    st.metric(label="Pot Depletion Age", value=runout_age)

if lump_sum_paid_at_57 > 0:
    tax_free_allowance_cap = 268275.0
    max_tax_free_lump_sum = min(pension_pot_at_57_pre_payoff * 0.25, tax_free_allowance_cap)
    rem_tax_free = max(0.0, max_tax_free_lump_sum - lump_sum_paid_at_57)
    
    st.info(
        f"💡 **Age 57 Mortgage Payoff Event:** Outstanding mortgage of **£{lump_sum_paid_at_57:,.0f}** was cleared using a lump sum from your pension pot at age 57. "
        f"This leaves an estimated **£{rem_tax_free:,.0f}** remaining of your 25% tax-free pension allowance (capped at £268,275)."
    )

st.markdown("---")

# ==========================================
# 5. CHARTS & DETAILED ANALYSIS
# ==========================================
tab1, tab2, tab3 = st.tabs(
    ["📊 Wealth & Income Trajectory", "🧮 Income Tax & NI Split", "📋 Year-by-Year Data"]
)

with tab1:
    st.subheader("Asset Accumulation vs. Decumulation")
    fig_wealth = go.Figure()
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Pension Balance (£)"],
            name="Pension Balance",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Mortgage Balance (£)"],
            name="Mortgage Balance",
            line=dict(color="#d62728", width=3, dash="dash"),
        )
    )
    if lump_sum_paid_at_57 > 0:
        fig_wealth.add_vline(
            x=57,
            line_dash="dot",
            line_color="purple",
            annotation_text="Mortgage Cleared (Age 57)",
            annotation_position="top left",
        )
    fig_wealth.add_vline(
        x=retirement_age,
        line_dash="dot",
        line_color="green",
        annotation_text="Retirement Start",
        annotation_position="top right",
    )
    fig_wealth.update_layout(
        xaxis_title="Age",
        yaxis_title="Amount (£)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_wealth, use_container_width=True)

    st.subheader("Retirement Income: Desired vs. Projected Actual")
    df_retire = df_proj[df_proj["Age"] >= retirement_age]
    fig_inc = go.Figure()
    fig_inc.add_trace(
        go.Bar(
            x=df_retire["Age"],
            y=df_retire["Projected Actual Income (£)"],
            name="Projected Actual Income",
            marker_color="#2ca02c",
        )
    )
    fig_inc.add_trace(
        go.Scatter(
            x=df_retire["Age"],
            y=df_retire["Desired Annual Income (£)"],
            name="Desired Target Income",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )
    fig_inc.update_layout(
        barmode="overlay",
        xaxis_title="Age",
        yaxis_title="Annual Income (£)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_inc, use_container_width=True)

with tab2:
    st.subheader("Current Salary Breakdown")
    breakdown_data = {
        "Component": [
            "Net Take-Home Pay",
            "Income Tax",
            "National Insurance",
            "Employee Pension",
            "Other Salary Sacrifice",
        ],
        "Amount (£)": [
            net_take_home,
            tax_paid,
            ni_paid,
            ee_contrib_val,
            other_sal_sac,
        ],
    }
    df_breakdown = pd.DataFrame(breakdown_data)

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        fig_pie = px.pie(
            df_breakdown,
            values="Amount (£)",
            names="Component",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_t2:
        st.markdown("### Total Annual Package Summary")
        st.write(f"**Gross Salary:** £{gross_salary:,.2f}")
        st.write(
            f"**Employer Pension Contribution:** £{er_contrib_val:,.2f} / yr"
        )
        st.write(
            f"**Total Pension Injection:** £{total_annual_pension_contrib:,.2f} / yr"
        )
        st.dataframe(
            df_breakdown.style.format({"Amount (£)": "£{:,.2f}"}),
            use_container_width=True,
        )

with tab3:
    st.subheader("Projection Master Table")
    st.dataframe(
        df_proj.style.format(
            {
                "Pension Balance (£)": "£{:,.0f}",
                "Mortgage Balance (£)": "£{:,.0f}",
                "Desired Annual Income (£)": "£{:,.0f}",
                "Projected Actual Income (£)": "£{:,.0f}",
                "Income Delta (£)": "£{:,.0f}",
            }
        ),
        use_container_width=True,
    )
