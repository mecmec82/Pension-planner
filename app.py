import json
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Joint Financial Planning & Retirement Dashboard",
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
    "spouse_age": 40,
    "spouse_retirement_age": 60,
    "spouse_current_pension": 100000.0,
    "spouse_annual_contribution": 6000.0,
    "spouse_pension_growth_rate": 6.0,
    "state_pension_age": 67,
    "state_pension_annual_amount": 12548.0,
    "initial_property_value": 450000.0,
    "downsizing_age": 70,
    "equity_release_pct": 30.0,
    "mortgage_balance": 220000.0,
    "mortgage_rate": 4.0,
    "mortgage_monthly_payment": 1200.0,
    "desired_pension_income": 45000.0,
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

st.title("📈 Joint Household Financial & Retirement Planner")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================
st.sidebar.header("👤 User Demographics & Pension")
current_age = st.sidebar.number_input(
    "User Current Age", min_value=18, max_value=56, value=int(config["current_age"]), step=1
)
lump_sum_payoff_age = int(config["lump_sum_payoff_age"])
retirement_age = st.sidebar.number_input(
    "User Retirement Age (Private Pension)",
    min_value=57,
    max_value=90,
    value=int(config["retirement_age"]),
    step=1,
)
current_pension = st.sidebar.number_input(
    "User Current Pension Pot (£)", min_value=0.0, value=float(config["current_pension"]), step=5000.0
)
pension_growth_rate = (
    st.sidebar.slider(
        "User Net Pension Growth Rate (%)", 0.0, 15.0, float(config["pension_growth_rate"]), step=0.5
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.header("👥 Spouse Demographics & Pension")
spouse_age = st.sidebar.number_input(
    "Spouse Current Age", min_value=18, max_value=90, value=int(config["spouse_age"]), step=1
)
spouse_retirement_age = st.sidebar.number_input(
    "Spouse Retirement Age (Private Pension)",
    min_value=55,
    max_value=90,
    value=int(config["spouse_retirement_age"]),
    step=1,
)
spouse_current_pension = st.sidebar.number_input(
    "Spouse Current Pension Pot (£)", min_value=0.0, value=float(config["spouse_current_pension"]), step=5000.0
)
spouse_annual_contribution = st.sidebar.number_input(
    "Spouse Annual Pension Contribution (£)", min_value=0.0, value=float(config["spouse_annual_contribution"]), step=500.0
)
spouse_pension_growth_rate = (
    st.sidebar.slider(
        "Spouse Net Pension Growth Rate (%)", 0.0, 15.0, float(config["spouse_pension_growth_rate"]), step=0.5
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.header("🏛️ UK State Pension Settings")
state_pension_age = st.sidebar.number_input(
    "State Pension Age (Both)", min_value=60, max_value=70, value=int(config["state_pension_age"]), step=1
)
state_pension_annual_amount = st.sidebar.number_input(
    "Full State Pension per Person (£/yr)", min_value=0.0, value=float(config["state_pension_annual_amount"]), step=500.0
)

st.sidebar.markdown("---")
st.sidebar.header("🏡 Property & Downsizing")
initial_property_value = st.sidebar.number_input(
    "Current Property Value (£)", min_value=0.0, value=float(config["initial_property_value"]), step=10000.0
)
downsizing_age = st.sidebar.number_input(
    "Downsizing Age (Equity Release)",
    min_value=50,
    max_value=95,
    value=int(config["downsizing_age"]),
    step=1,
)
equity_release_pct = st.sidebar.slider(
    "Equity Release from Downsizing (%)", 0.0, 100.0, float(config["equity_release_pct"]), step=5.0
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
st.sidebar.header("💼 User Income & Salary Sacrifice")
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
st.sidebar.header("🎯 Household Retirement Goals")
desired_pension_income = st.sidebar.number_input(
    "Desired Household Net Income in Retirement (£)",
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
end_age = st.sidebar.number_input(
    "Target Horizon / End User Age",
    min_value=retirement_age + 1,
    max_value=110,
    value=int(config["end_age"]),
    step=1,
)

# ==========================================
# 2. TAX CALCULATIONS (UK Baseline)
# ==========================================
def calculate_take_home(salary, ee_pen_pct, sal_sac):
    ee_pen_annual = salary * (ee_pen_pct / 100)
    taxable_salary = max(0.0, salary - ee_pen_annual - sal_sac)

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
total_annual_user_pension_contrib = ee_contrib_val + er_contrib_val

# ==========================================
# 3. PROJECTION LOGIC (JOINT MODEL + EQUITY RELEASE)
# ==========================================
years = np.arange(current_age, end_age + 1)

user_pension_balances = []
spouse_pension_balances = []
combined_pension_balances = []
liquid_cash_balances = []
property_values = []
mortgage_balances = []
desired_incomes = []
actual_incomes = []
deltas = []

lump_sum_paid_at_57 = 0.0
equity_released_at_downsizing = 0.0

curr_user_pot = current_pension
curr_spouse_pot = spouse_current_pension
curr_liquid_cash = 0.0
curr_property_val = initial_property_value
curr_mortgage_pot = mortgage_balance
annual_mortgage_payment = mortgage_monthly_payment * 12

spouse_age_offset = spouse_age - current_age

for yr in range(current_age, end_age + 1):
    years_from_start = yr - current_age
    curr_spouse_age = spouse_age_offset + yr
    inflated_desired_income = desired_pension_income * (
        (1 + inflation_rate) ** years_from_start
    )

    # 1. Property appreciation with inflation
    if yr > current_age:
        curr_property_val *= (1 + inflation_rate)

    # --- AGE 57 SPECIAL EVENT: LUMP-SUM MORTGAGE PAYOFF ---
    if yr == lump_sum_payoff_age:
        if curr_mortgage_pot > 0:
            lump_sum_paid_at_57 = min(curr_mortgage_pot, curr_user_pot)
            curr_user_pot -= lump_sum_paid_at_57
            curr_mortgage_pot = max(0.0, curr_mortgage_pot - lump_sum_paid_at_57)

    # --- DOWNSIZING EVENT ---
    if yr == downsizing_age:
        # Equity available at downsizing age (Property Value minus remaining mortgage)
        current_equity = max(0.0, curr_property_val - curr_mortgage_pot)
        equity_released_at_downsizing = current_equity * (equity_release_pct / 100)
        curr_liquid_cash += equity_released_at_downsizing
        # Reduce property value and mortgage proportionally to reflect downsizing
        curr_property_val -= equity_released_at_downsizing
        curr_mortgage_pot = max(0.0, curr_mortgage_pot * (1 - (equity_release_pct / 100)))

    # Accumulation Phase
    if yr < retirement_age:
        curr_user_pot = (
            curr_user_pot * (1 + pension_growth_rate)
            + total_annual_user_pension_contrib
        )
        if curr_mortgage_pot > 0 and yr != lump_sum_payoff_age:
            interest = curr_mortgage_pot * mortgage_rate
            principal_paid = min(
                curr_mortgage_pot, annual_mortgage_payment - interest
            )
            if principal_paid < 0:
                curr_mortgage_pot += interest - annual_mortgage_payment
            else:
                curr_mortgage_pot = max(0.0, curr_mortgage_pot - principal_paid)

    if curr_spouse_age < spouse_retirement_age:
        curr_spouse_pot = (
            curr_spouse_pot * (1 + spouse_pension_growth_rate)
            + spouse_annual_contribution
        )

    # Decumulation & Drawdown Phase
    user_private_drawdown = 0.0
    if yr >= retirement_age:
        target_share = inflated_desired_income / 2
        user_private_drawdown = min(curr_user_pot, target_share)
        curr_user_pot = (
            curr_user_pot - user_private_drawdown
        ) * (1 + pension_growth_rate)
        curr_user_pot = max(0.0, curr_user_pot)

    spouse_private_drawdown = 0.0
    if curr_spouse_age >= spouse_retirement_age:
        target_share = inflated_desired_income / 2
        spouse_private_drawdown = min(curr_spouse_pot, target_share)
        curr_spouse_pot = (
            curr_spouse_pot - spouse_private_drawdown
        ) * (1 + spouse_pension_growth_rate)
        curr_spouse_pot = max(0.0, curr_spouse_pot)

    # Liquid cash buffer drawdown if pension drawdown is less than target
    liquid_cash_drawdown = 0.0
    if (yr >= retirement_age or curr_spouse_age >= spouse_retirement_age):
        current_pension_total = user_private_drawdown + spouse_private_drawdown
        inflated_state_pension = state_pension_annual_amount * ((1 + inflation_rate) ** years_from_start)
        u_state = inflated_state_pension if yr >= state_pension_age else 0.0
        s_state = inflated_state_pension if curr_spouse_age >= state_pension_age else 0.0
        
        current_total = current_pension_total + u_state + s_state
        shortfall = inflated_desired_income - current_total
        if shortfall > 0 and curr_liquid_cash > 0:
            liquid_cash_drawdown = min(curr_liquid_cash, shortfall)
            curr_liquid_cash -= liquid_cash_drawdown

    user_state_pension = (state_pension_annual_amount * ((1 + inflation_rate) ** years_from_start)) if yr >= state_pension_age else 0.0
    spouse_state_pension = (state_pension_annual_amount * ((1 + inflation_rate) ** years_from_start)) if curr_spouse_age >= state_pension_age else 0.0

    total_actual_inc = (
        user_private_drawdown
        + spouse_private_drawdown
        + user_state_pension
        + spouse_state_pension
        + liquid_cash_drawdown
    )
    
    if yr < retirement_age and curr_spouse_age < spouse_retirement_age:
        total_actual_inc = 0.0

    delta = total_actual_inc - inflated_desired_income if (yr >= retirement_age or curr_spouse_age >= spouse_retirement_age) else -inflated_desired_income

    user_pension_balances.append(curr_user_pot)
    spouse_pension_balances.append(curr_spouse_pot)
    combined_pension_balances.append(curr_user_pot + curr_spouse_pot)
    liquid_cash_balances.append(curr_liquid_cash)
    property_values.append(curr_property_val)
    mortgage_balances.append(curr_mortgage_pot)
    desired_incomes.append(inflated_desired_income)
    actual_incomes.append(total_actual_inc)
    deltas.append(delta)

df_proj = pd.DataFrame(
    {
        "Age": years,
        "User Pension (£)": user_pension_balances,
        "Spouse Pension (£)": spouse_pension_balances,
        "Combined Pension Pot (£)": combined_pension_balances,
        "Liquid Cash (£)": liquid_cash_balances,
        "Property Value (£)": property_values,
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
        label=f"Equity Released at Age {downsizing_age}",
        value=f"£{equity_released_at_downsizing:,.0f}",
        delta=f"{equity_release_pct}% of Home Equity",
    )

with col_m3:
    combined_pot_at_retire = df_proj.loc[
        df_proj["Age"] == retirement_age, "Combined Pension Pot (£)"
    ].values[0]
    st.metric(
        label=f"Combined Pots at User Age {retirement_age}",
        value=f"£{combined_pot_at_retire:,.0f}",
    )

with col_m4:
    depletion_rows = df_proj[
        (df_proj["Age"] >= retirement_age)
        & (df_proj["Combined Pension Pot (£)"] <= 0)
        & (df_proj["Liquid Cash (£)"] <= 0)
    ]
    runout_age = (
        f"Age {depletion_rows['Age'].iloc[0]}"
        if not depletion_rows.empty
        else "Sustainable"
    )
    st.metric(label="Depletion / Shortfall Age", value=runout_age)

st.markdown("---")

# ==========================================
# 5. CHARTS & DETAILED ANALYSIS
# ==========================================
tab1, tab2, tab3 = st.tabs(
    ["📊 Household Wealth & Income", "🧮 Income Tax & NI Split", "📋 Year-by-Year Data"]
)

with tab1:
    st.subheader("Combined Wealth: Pensions, Liquid Cash & Property")
    fig_wealth = go.Figure()
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Combined Pension Pot (£)"],
            name="Combined Pension Pots",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Liquid Cash (£)"],
            name="Liquid Cash (Downsizing)",
            line=dict(color="#2ca02c", width=2, dash="dot"),
        )
    )
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Property Value (£)"],
            name="Property Value",
            line=dict(color="#9467bd", width=2),
        )
    )
    fig_wealth.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Mortgage Balance (£)"],
            name="Mortgage Balance",
            line=dict(color="#d62728", width=2, dash="dash"),
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
        x=downsizing_age,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Downsize (Age {downsizing_age})",
        annotation_position="top right",
    )
    fig_wealth.update_layout(
        xaxis_title="User Age",
        yaxis_title="Amount (£)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_wealth, use_container_width=True)

    st.subheader("Retirement Income: Desired vs. Actual")
    fig_inc = go.Figure()
    fig_inc.add_trace(
        go.Bar(
            x=df_proj["Age"],
            y=df_proj["Projected Actual Income (£)"],
            name="Projected Actual Household Income",
            marker_color="#2ca02c",
        )
    )
    fig_inc.add_trace(
        go.Scatter(
            x=df_proj["Age"],
            y=df_proj["Desired Annual Income (£)"],
            name="Desired Target Income",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )
    fig_inc.update_layout(
        barmode="overlay",
        xaxis_title="User Age",
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
        st.write(f"**Employer Pension Contribution:** £{er_contrib_val:,.2f} / yr")
        st.write(f"**Spouse Annual Pension Addition:** £{spouse_annual_contribution:,.2f} / yr")
        st.dataframe(
            df_breakdown.style.format({"Amount (£)": "£{:,.2f}"}),
            use_container_width=True,
        )

with tab3:
    st.subheader("Projection Master Table")
    st.dataframe(
        df_proj.style.format(
            {
                "User Pension (£)": "£{:,.0f}",
                "Spouse Pension (£)": "£{:,.0f}",
                "Combined Pension Pot (£)": "£{:,.0f}",
                "Liquid Cash (£)": "£{:,.0f}",
                "Property Value (£)": "£{:,.0f}",
                "Mortgage Balance (£)": "£{:,.0f}",
                "Desired Annual Income (£)": "£{:,.0f}",
                "Projected Actual Income (£)": "£{:,.0f}",
                "Income Delta (£)": "£{:,.0f}",
            }
        ),
        use_container_width=True,
    )
