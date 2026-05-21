import streamlit as st
import pandas as pd

# Set page layout to wide
st.set_page_config(page_title="A350 Reserve Modeler", layout="wide")

st.title("✈️ A350-900 Maintenance Reserves & Lease Dashboard")
st.markdown("Interactive 144-Month Fleet Financial Projection with Dynamic Drawdowns & Independent Utilization")

# --- SIDEBAR: USER INPUTS ---
st.sidebar.header("1. Future Utilization (Lease Term)")
st.sidebar.caption("Decorrelated Hours and Cycles Accumulation")
annual_fh = st.sidebar.number_input("Projected Annual Flight Hours (FH)", value=4800, step=100)
annual_fc = st.sidebar.number_input("Projected Annual Flight Cycles (FC)", value=480, step=10)

st.sidebar.header("2. Financial Settings")
lease_rate = st.sidebar.number_input("Monthly Lease Rate ($)", value=865000, step=10000)

st.sidebar.subheader("Reserve Base Rates (Current Year)")
res_144_rate = st.sidebar.number_input("144M Check ($/mo)", value=39500, step=500)
res_lg_rate = st.sidebar.number_input("Landing Gear ($/mo)", value=12000, step=500)
res_llp_rate = st.sidebar.number_input("Engine LLP ($/FC per Engine)", value=1040, step=10)
res_apu_rate = st.sidebar.number_input("APU ($/FH)", value=260, step=5)

st.sidebar.subheader("Annual Escalation Rates (%)")
esc_144 = st.sidebar.number_input("144M Escalation (%)", value=5.0, step=0.5) / 100
esc_lg = st.sidebar.number_input("LG Escalation (%)", value=5.0, step=0.5) / 100
esc_llp = st.sidebar.number_input("Engine LLP Escalation (%)", value=11.0, step=0.5) / 100
esc_apu = st.sidebar.number_input("APU Escalation (%)", value=6.0, step=0.5) / 100

st.sidebar.header("3. Starting Clocks (Legacy Age)")
st.sidebar.caption("Airframe Delivery Age")
af_tsn_start = st.sidebar.number_input("Airframe Initial TSN", value=55962)
af_csn_start = st.sidebar.number_input("Airframe Initial CSN", value=9054)
af_age_months = st.sidebar.number_input("Airframe Age (Months since new)", value=130)

st.sidebar.caption("Engine 1 Delivery Age")
eng1_tsn_start = st.sidebar.number_input("ENG 1 Initial TSN", value=46128)
eng1_csn_start = st.sidebar.number_input("ENG 1 Initial CSN", value=7390)
eng1_tso_start = st.sidebar.number_input("ENG 1 Initial TSO (Hours)", value=17954)
eng1_cso_start = st.sidebar.number_input("ENG 1 Initial CSO (Cycles)", value=2826)

st.sidebar.caption("Engine 2 Delivery Age")
eng2_tsn_start = st.sidebar.number_input("ENG 2 Initial TSN", value=49404)
eng2_csn_start = st.sidebar.number_input("ENG 2 Initial CSN", value=7399)
eng2_tso_start = st.sidebar.number_input("ENG 2 Initial TSO (Hours)", value=15890)
eng2_cso_start = st.sidebar.number_input("ENG 2 Initial CSO (Cycles)", value=2460)

st.sidebar.caption("APU Delivery Age")
apu_tsn_start = st.sidebar.number_input("APU Initial TSN", value=23254)
apu_csn_start = st.sidebar.number_input("APU Initial CSN", value=13637)
apu_tso_start = st.sidebar.number_input("APU Initial TSO (Hours)", value=550)

# --- BACKGROUND CALCULATIONS ---
m_fh = annual_fh / 12
m_fc = annual_fc / 12

timeline_data = []

# Initialize financial pots
acc_144, acc_lg, acc_e1, acc_e2, acc_apu = 0, 0, 0, 0, 0

# Initialize physical clocks
af_tsn, af_csn = af_tsn_start, af_csn_start
eng1_tsn, eng1_csn = eng1_tsn_start, eng1_csn_start
eng1_tso, eng1_cso = eng1_tso_start, eng1_cso_start
eng2_tsn, eng2_csn = eng2_tsn_start, eng2_csn_start
eng2_tso, eng2_cso = eng2_tso_start, eng2_cso_start
apu_tsn, apu_csn, apu_tso = apu_tsn_start, apu_csn_start, apu_tso_start

for m in range(1, 145):
    year_idx = (m - 1) // 12
    current_af_age = af_age_months + m
    
    # Financial Inflows (Escalated based on input sliders)
    in_144 = res_144_rate * ((1 + esc_144)**year_idx)
    in_lg = res_lg_rate * ((1 + esc_lg)**year_idx)
    in_e1 = (res_llp_rate * m_fc) * ((1 + esc_llp)**year_idx)
    in_e2 = (res_llp_rate * m_fc) * ((1 + esc_llp)**year_idx)
    in_apu = (res_apu_rate * m_fh) * ((1 + esc_apu)**year_idx)
    
    # Add to accrued balances
    acc_144 += in_144
    acc_lg += in_lg
    acc_e1 += in_e1
    acc_e2 += in_e2
    acc_apu += in_apu

    # Uninterrupted total time accumulation
    af_tsn += m_fh
    af_csn += m_fc
    eng1_tsn += m_fh
    eng1_csn += m_fc
    eng2_tsn += m_fh
    eng2_csn += m_fc
    apu_tsn += m_fh
    apu_csn += m_fc

    # Check for Drawdowns & Shop Visits (Resets TSO/CSO and Zeros out Cash)
    event_flag = []
    
    if eng1_tso + m_fh >= 25000:
        eng1_tso = (eng1_tso + m_fh) - 25000
        eng1_cso = 0 
        acc_e1 = 0   # Cash pot wiped out (drawdown)
        event_flag.append("[ENG 1 SV]")
    else:
        eng1_tso += m_fh
        eng1_cso += m_fc
        
    if eng2_tso + m_fh >= 25000:
        eng2_tso = (eng2_tso + m_fh) - 25000
        eng2_cso = 0
        acc_e2 = 0   # Cash pot wiped out (drawdown)
        event_flag.append("[ENG 2 SV]")
    else:
        eng2_tso += m_fh
        eng2_cso += m_fc
        
    if apu_tso + m_fh >= 8000:
        apu_tso = (apu_tso + m_fh) - 8000
        acc_apu = 0  # Cash pot wiped out (drawdown)
        event_flag.append("[APU SV]")
    else:
        apu_tso += m_fh
        
    if current_af_age % 72 == 0:
        event_flag.append("[72M Heavy Check]")
        
    if current_af_age % 144 == 0:
        acc_144 = 0  # Drawdown for 12Y Check
        acc_lg = 0   # Drawdown for Landing Gear (every 12Y)
        event_flag.append("[12Y Check & LG Overhaul]")
        
    events_str = " + ".join(event_flag) if len(event_flag) > 0 else "Normal Operations"
    total_accrued = acc_144 + acc_lg + acc_e1 + acc_e2 + acc_apu
    
    timeline_data.append({
        "Month": int(m),
        "Events / Status": events_str,
        "AF TSN": int(af_tsn), "AF CSN": int(af_csn),
        "ENG1 TSN": int(eng1_tsn), "ENG1 CSN": int(eng1_csn), "ENG1 TSO": int(eng1_tso), "ENG1 CSO": int(eng1_cso),
        "ENG2 TSN": int(eng2_tsn), "ENG2 CSN": int(eng2_csn), "ENG2 TSO": int(eng2_tso), "ENG2 CSO": int(eng2_cso),
        "APU TSN": int(apu_tsn), "APU CSN": int(apu_csn), "APU TSO": int(apu_tso),
        "Accrued 144M ($)": int(acc_144),
        "Accrued LG ($)": int(acc_lg),
        "Accrued ENG1 ($)": int(acc_e1),
        "Accrued ENG2 ($)": int(acc_e2),
        "Accrued APU ($)": int(acc_apu),
        "Total Accrued ($)": int(total_accrued),
        "Monthly Cost ($)": int(lease_rate + in_144 + in_lg + in_e1 + in_e2 + in_apu)
    })

df = pd.DataFrame(timeline_data)

# --- MAIN DASHBOARD DISPLAY ---
st.subheader("📊 Fleet Financial Overview")

# Top KPI Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Base Lease Paid (12Y)", f"${int(lease_rate * 144):,}")
col2.metric("Peak Accrued Cash Balance", f"${int(df['Total Accrued ($)'].max()):,}")
col3.metric("Final Airframe TSN", f"{int(af_tsn):,} FH")
col4.metric("Ending Accrued Cash (M144)", f"${int(df['Total Accrued ($)'].iloc[-1]):,}")

st.markdown("---")

# Interactive Line Chart
st.subheader("📈 Cumulative Maintenance Reserves Build-Up & Drawdowns")
chart_data = df.set_index("Month")[["Accrued ENG1 ($)", "Accrued ENG2 ($)", "Accrued APU ($)", "Accrued 144M ($)", "Total Accrued ($)"]]
st.line_chart(chart_data)

# Interactive Data Table
st.subheader("📅 144-Month Granular Timeline")

try:
    st.dataframe(df.style.format({
        "Accrued 144M ($)": "${:,.0f}", "Accrued LG ($)": "${:,.0f}",
        "Accrued ENG1 ($)": "${:,.0f}", "Accrued ENG2 ($)": "${:,.0f}",
        "Accrued APU ($)": "${:,.0f}", "Total Accrued ($)": "${:,.0f}",
        "Monthly Cost ($)": "${:,.0f}",
        "AF TSN": "{:,.0f}", "AF CSN": "{:,.0f}",
        "ENG1 TSN": "{:,.0f}", "ENG1 CSN": "{:,.0f}", "ENG1 TSO": "{:,.0f}", "ENG1 CSO": "{:,.0f}",
        "ENG2 TSN": "{:,.0f}", "ENG2 CSN": "{:,.0f}", "ENG2 TSO": "{:,.0f}", "ENG2 CSO": "{:,.0f}",
        "APU TSN": "{:,.0f}", "APU CSN": "{:,.0f}", "APU TSO": "{:,.0f}"
    }), use_container_width=True, height=600)
except Exception as e:
    st.dataframe(df, use_container_width=True, height=600)