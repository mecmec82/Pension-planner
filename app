import numpy as np
import pandas as pd
import plotly.graph_objects as gg
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Financial Planning & Retirement Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Personal Financial & Retirement Planner")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================
st.sidebar.header("👤 Age & Demographics")
current_age = st.sidebar.number_input(
    "Current Age", min_value=18, max_value=80, value=40, step=1
)
retirement_age = st.sidebar.number_input(
    "Retirement Age (Access Pension)",
    min_value=current_age + 1,
    max_value=90,
    value=60,
    step=1,
)
end_age = st.sidebar.number_input(
    "Target Horizon / End Age",
    min_value=retirement_age + 1,
    max_value=110,
    value=90,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.header("💼 Income & Salary Sacrifice")
gross_salary = st.sidebar.number_input(
    "Annual Gross Salary (£)", min_value=0.0, value=75000.0, step=1000.0
)
ee_pension_pct = st.sidebar.slider(
    "Employee Pension Contribution (%)", 0.0, 50.0, 5.0, step=0.5
)
er_pension_pct = st.sidebar.slider(
    "Employer Pension Contribution (%)", 0.0, 30.0, 10.0, step=0.5
)
other_sal_sac = st.sidebar.number_input(
    "Other Annual Salary Sacrifice (EV, Cycle, etc.) (£)",
    min_value=0.0,
    value=0.0,
    step=500.0,
)

st.sidebar.markdown("---")
st.sidebar.header("📊 Current Balances & Growth Rates")
current_pension = st.sidebar.number_input(
    "Current Pension Pot (£)", min_value=0.0, value=150000.0, step=5000.0
)
pension_growth_rate = (
    st.sidebar.slider(
        "Net Pension Growth Rate (Post-Fees) (%)", 0.0, 15.0, 6.0, step=0.5
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.header("🏡 Mortgage Details")
mortgage_balance = st.sidebar.number_input(
    "Current Mortgage Balance (£)", min_value=0.0, value=220000.0, step=5000.0
)
mortgage_rate = (
    st.sidebar.slider(
        "Mortgage Interest Rate (%)", 0.0, 12.0, 4.0, step=0.25
    )
    / 100
)
mortgage_monthly_payment = st.sidebar.number_input(
    "Monthly Mortgage Payment (£)", min_value=0.0, value=1200.0, step=50.0
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Retirement Goals")
desired_pension_income = st.sidebar.number_input(
    "Desired Annual Net Income in Retirement (£)",
    min_value=0.0,
    value=35000.0,
    step=1000.0,
)
inflation_rate = (
    st.sidebar.slider(
        "Expected Inflation Rate (%)", 0.0, 10.0, 2.5, step=0.25
    )
    / 100
)

# ==========================================
# 2. TAX CALCULATIONS (UK 2024/25 Baseline)
# ==========================================
def calculate_take_home(salary, ee_pen_pct, sal_sac):
    ee_pen_annual = salary * (ee_pen_pct / 100)
    taxable_salary = max(0.0, salary - ee_pen_annual - sal_sac)

    # Personal Allowance & Tapering above £100k
    personal_allowance = 12570.0
    if taxable_salary > 100000:
        reduction = (taxable_salary - 100000) / 2
        personal_allowance = max(0.0, personal_allowance - reduction)

    # Income Tax Bands
    taxable_income = max(0.0, taxable_salary - personal_allowance)
    income_tax = 0.0

    basic_band = 37700.0  # Up to 50,270 total
    higher_band = 74730.0  # 50,271 to 125,140

    if taxable_income > 0:
        b_tax = min(taxable_income, basic_band) * 0.20
        income_tax += b_tax
    if taxable_income > basic_band:
        h_tax = (
            min(taxable_income - basic_band, higher_band) * 0.40
        )
        income_tax += h_tax
    if taxable_income > (basic_band + higher_band):
        a_tax = (taxable_income - basic_band - higher_band) * 0.45
        income_tax += a_tax

    # National Insurance (Class 1 Employee - 8% main rate, 2% upper)
    ni = 0.0
    ni_threshold = 12570.0
    upper_reg_limit = 50270.0

    if taxable_salary > ni_threshold:
        main_ni_income = min(taxable_salary, upper_reg_limit) - ni_threshold
        ni += main_ni_income * 0.08
    if taxable_salary > upper_reg_limit:
        upper_ni_income = taxable_salary - upper_reg_limit
        ni += upper_ni_income * 0.02

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
# 3. PROJECTION LOGIC
# ==========================================
years_to_sim = end_age - current_age
years = np.arange(current_age, end_age + 1)

pension_balances = []
mortgage_balances = []
desired_incomes = []
actual_incomes = []
deltas = []

curr_pension_pot = current_pension
curr_mortgage_pot = mortgage_balance
annual_mortgage_payment = mortgage_monthly_payment * 12

for yr in range(current_age, end_age + 1):
    # Adjust target income for inflation
    years_from_start = yr - current_age
    inflated_desired_income = desired_pension_income * (
        (1 + inflation_rate) ** years_from_start
    )

    # 1. Accumulation Phase
    if yr < retirement_age:
        # Pension growth + contributions
        curr_pension_pot = (
            curr_pension_pot * (1 + pension_growth_rate)
            + total_annual_pension_contrib
        )
        actual_inc = 0.0
        delta = -inflated_desired_income  # Not drawing yet

        # Mortgage repayment schedule
        if curr_mortgage_pot > 0:
            interest = curr_mortgage_pot * mortgage_rate
            principal_paid = min(
                curr_mortgage_pot, annual_mortgage_payment - interest
            )
            if principal_paid < 0:  # Payment doesn't cover interest
                curr_mortgage_pot += interest - annual_mortgage_payment
            else:
                curr_mortgage_pot = max(0.0, curr_mortgage_pot - principal_paid)
        else:
            curr_mortgage_pot = 0.0

    # 2. Decumulation Phase (Retirement)
    else:
        curr_mortgage_pot = 0.0  # Assume mortgage cleared or frozen at retirement
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
    pot_at_retire = df_proj.loc[
        df_proj["Age"] == retirement_age, "Pension Balance (£)"
    ].values[0]
    st.metric(
        label=f"Pension Pot at Age {retirement_age}",
        value=f"£{pot_at_retire:,.0f}",
    )

with col_m3:
    total_gap = sum(
        [d for d in df_proj.loc[df_proj["Age"] >= retirement_age, "Income Delta (£)"] if d < 0]
    )
    st.metric(
        label="Total Retirement Shortfall",
        value=f"£{abs(total_gap):,.0f}" if total_gap < 0 else "£0",
        delta_color="inverse" if total_gap < 0 else "normal",
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

st.markdown("---")

# ==========================================
# 5. CHARTS & DETAILED ANALYSIS
# ==========================================
tab1, tab2, tab3 = st.tabs(
    ["📊 Wealth & Income Trajectory", "🧮 Income Tax & NI Split", "📋 Year-by-Year Data"]
)

with tab1:
    st.subheader("Asset Accumulation vs. Decumulation")
    fig_wealth = gg.Figure()
    fig_wealth.add_trace(
        gg.Scatter(
            x=df_proj["Age"],
            y=df_proj["Pension Balance (£)"],
            name="Pension Balance",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig_wealth.add_trace(
        gg.Scatter(
            x=df_proj["Age"],
            y=df_proj["Mortgage Balance (£)"],
            name="Mortgage Balance",
            line=dict(color="#d62728", width=3, dash="dash"),
        )
    )
    fig_wealth.add_vline(
        x=retirement_age,
        line_dash="dot",
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
    fig_inc = gg.Figure()
    fig_inc.add_trace(
        gg.Bar(
            x=df_retire["Age"],
            y=df_retire["Projected Actual Income (£)"],
            name="Projected Actual Income",
            marker_color="#2ca02c",
        )
    )
    fig_inc.add_trace(
        gg.Scatter(
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
