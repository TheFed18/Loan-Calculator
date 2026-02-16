import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io

# ───────────────────────────────────────────────────────────────
# PMT FUNCTION
# ───────────────────────────────────────────────────────────────
def calculate_pmt(annual_rate, nper, pv, fv=0):
    """Calculate payment for annuity with optional future value (residual)."""
    if annual_rate == 0:
        return -(pv + fv) / nper
    r = annual_rate / 12
    z = (1 + r) ** nper
    pmt = -r * (pv * z + fv) / (z - 1)
    return round(pmt, 2)


# ───────────────────────────────────────────────────────────────
# STREAMLIT CONFIG
# ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Shpitz Loan Generator – FEDGROUP", layout="wide")

# FEDGROUP Branding
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #001F3F !important; }
        .stButton > button {
            background-color: #E91E63;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
        }
        .stButton > button:hover { background-color: #d81b60; }
        button[kind="primary"] {
            background-color: #001F3F !important;
            color: white !important;
            border-radius: 8px;
        }
        button[kind="primary"]:hover { background-color: #0A2540 !important; }
        hr {
            background: linear-gradient(to right, transparent, #E91E63, transparent);
            height: 3px;
            border: none;
            margin: 20px 0;
        }
        .fed-title { color: #001F3F; text-align: center; margin-bottom: 0; }
        .fed-subtitle { color: #666; text-align: center; font-size: 1.1em; margin-top: 4px; }
        .fed-accent { color: #E91E63; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Header
logo_col, title_col = st.columns([1, 5])
with logo_col:
    st.image(
        "https://www.fedgroup.co.za/wp-content/uploads/2023/05/FEDGROUP-Logo.png",
        width=180
    )
with title_col:
    st.markdown('<h1 class="fed-title">Shpitz Loan Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="fed-subtitle">Powered by <span class="fed-accent">FEDGROUP</span></p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Session state
if 'df' not in st.session_state:
    st.session_state.df = None

# ───────────────────────────────────────────────────────────────
# INPUT SECTIONS
# ───────────────────────────────────────────────────────────────

st.header("Deal Information")
col_client, col_fac = st.columns(2)
with col_client:
    client_name = st.text_input("Client Name", value="Client XYZ")
with col_fac:
    facility_name = st.text_input("Facility / Deal Name", value="Development Facility A")

st.header("Loan Parameters")
col1, col2 = st.columns([1, 1])
with col1:
    facility_amount = st.number_input("Facility Amount", value=100_000_000.0, step=1_000_000.0, format="%.0f")
    residual = st.number_input("Residual / Balloon Amount", value=0.0, step=1_000_000.0, format="%.0f")
with col2:
    repayment_structure = st.selectbox(
        "Repayment Structure",
        ["Equal Installments", "Interest Only", "Capitalised Interest", "Structured Capital"]
    )
    term_months = st.number_input("Term (Months)", value=120, step=1, min_value=1)

# Capitalised Fees
st.header("Capitalised Fees")
capitalise_fees = st.checkbox("Capitalise fees into principal?", value=True)
custom_fees = []

if capitalise_fees:
    st.info("Define custom fees to capitalise into the loan")
    num_fees = st.number_input("Number of fee items", min_value=1, max_value=10, value=2, step=1)
    
    for i in range(num_fees):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fee_name = st.text_input(
                f"Fee Name {i+1}", 
                value="Legal Fees" if i == 0 else "Raising Fee", 
                key=f"fee_name_{i}"
            )
        with col_f2:
            fee_type = st.selectbox(f"Type {i+1}", ["Nominal Amount", "% of Facility"], key=f"fee_type_{i}")
        with col_f3:
            if fee_type == "Nominal Amount":
                fee_amount = st.number_input(
                    f"Amount {i+1}", 
                    value=200_000.0 if i == 0 else 2_300_000.0, 
                    step=10_000.0, 
                    format="%.2f", 
                    key=f"fee_amount_{i}"
                )
            else:
                fee_pct = st.number_input(f"Percentage {i+1}", value=2.3, step=0.1, format="%.2f", key=f"fee_pct_{i}")
                fee_amount = round(facility_amount * fee_pct / 100, 2)
                st.caption(f"Amount: R{fee_amount:,.2f}")
        
        custom_fees.append({'name': fee_name, 'type': fee_type, 'amount': fee_amount})

total_fees = sum(f['amount'] for f in custom_fees) if capitalise_fees else 0.0
full_capital = round(facility_amount + total_fees, 2) if capitalise_fees else facility_amount

# Drawdown Structure
st.header("Drawdown Structure")
drawdown_structure = st.selectbox("Drawdown Type", ["Single Drawdown", "Multiple Drawdowns"])
drawdown_schedule = None

if drawdown_structure == "Single Drawdown":
    drawdown_date = st.date_input("Drawdown Date", value=datetime(2025, 3, 1))
    first_payment_date = st.date_input("First Payment Date", value=datetime(2025, 4, 1))
else:
    st.info("Define multiple drawdown tranches")
    num_drawdowns = st.number_input("Number of drawdowns", min_value=1, max_value=20, value=2, step=1)
    
    drawdown_schedule = []
    for i in range(num_drawdowns):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dd_date = st.date_input(
                f"Drawdown Date {i+1}", 
                value=datetime(2025, 3, 1) + relativedelta(months=i*3), 
                key=f"dd_date_{i}"
            )
        with col_d2:
            dd_amount = st.number_input(
                f"Drawdown Amount {i+1}", 
                value=facility_amount / num_drawdowns, 
                step=100_000.0, 
                format="%.2f", 
                key=f"dd_amount_{i}"
            )
        
        drawdown_schedule.append({'date': dd_date, 'amount': dd_amount})
    
    drawdown_schedule = sorted(drawdown_schedule, key=lambda x: x['date'])
    first_payment_date = st.date_input(
        "First Payment Date", 
        value=drawdown_schedule[0]['date'] + relativedelta(months=1)
    )

# Interest Rate Structure
st.header("Interest Rate Structure")
rate_structure = st.selectbox("Rate Structure", ["Fixed Rate", "Variable Rate"])

if rate_structure == "Fixed Rate":
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        prime_rate = st.number_input("Prime Rate %", value=11.75, step=0.25, format="%.2f")
    with col_r2:
        delta_margin = st.number_input("Delta / Margin %", value=2.0, step=0.25, format="%.2f")
    
    interest_rate = prime_rate + delta_margin
    rate_schedule = None
else:
    st.info("Define variable interest rates by period range")
    num_rate_periods = st.number_input("Number of rate periods", min_value=1, max_value=10, value=2, step=1)
    
    rate_schedule = []
    for i in range(num_rate_periods):
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            from_period = st.number_input(
                f"From Period {i+1}", 
                min_value=1, 
                value=1 if i == 0 else (rate_schedule[i-1]['to_period'] + 1), 
                step=1, 
                key=f"from_{i}"
            )
        with col_r2:
            to_period = st.number_input(
                f"To Period {i+1}", 
                min_value=from_period, 
                value=term_months if i == num_rate_periods - 1 else from_period + 11, 
                step=1, 
                key=f"to_{i}"
            )
        with col_r3:
            prime = st.number_input(f"Prime % {i+1}", value=11.75, step=0.25, format="%.2f", key=f"prime_{i}")
        with col_r4:
            margin = st.number_input(f"Margin % {i+1}", value=2.0, step=0.25, format="%.2f", key=f"margin_{i}")
        
        rate_schedule.append({
            'from_period': from_period,
            'to_period': to_period,
            'prime': prime,
            'margin': margin,
            'total_rate': prime + margin
        })
    
    # FIX #1: Always set interest_rate for variable rate mode
    interest_rate = rate_schedule[0]['total_rate'] if rate_schedule else 12.25

# Custom Capital Repayments
st.header("Custom Capital Repayments")
use_custom_capital = st.checkbox("Add custom capital repayments", value=False)
custom_capital_schedule = None

if use_custom_capital:
    st.info("Define one-off principal payments by date")
    num_custom_payments = st.number_input("Number of custom capital payments", min_value=1, max_value=20, value=1, step=1)
    
    custom_capital_schedule = []
    for i in range(num_custom_payments):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            payment_date = st.date_input(
                f"Payment Date {i+1}", 
                value=first_payment_date + relativedelta(months=12 * (i+1)), 
                key=f"custom_date_{i}"
            )
        with col_c2:
            payment_amount = st.number_input(
                f"Capital Amount {i+1}", 
                value=1_000_000.0, 
                step=100_000.0, 
                format="%.2f", 
                key=f"custom_amount_{i}"
            )
        
        custom_capital_schedule.append({'date': payment_date, 'amount': payment_amount})

# Structured Capital Payments
structured_payments = None
if repayment_structure == "Structured Capital":
    st.header("Structured Capital Payments")
    st.info("Define custom principal payment amounts by period range")
    num_payment_periods = st.number_input("Number of payment structures", min_value=1, max_value=10, value=2, step=1)
    
    structured_payments = []
    for i in range(num_payment_periods):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            from_p = st.number_input(
                f"From Period {i+1}", 
                min_value=1, 
                value=1 if i == 0 else (structured_payments[i-1]['to_period'] + 1), 
                step=1, 
                key=f"pay_from_{i}"
            )
        with col_p2:
            to_p = st.number_input(
                f"To Period {i+1}", 
                min_value=from_p, 
                value=term_months if i == num_payment_periods - 1 else from_p + 11, 
                step=1, 
                key=f"pay_to_{i}"
            )
        with col_p3:
            payment = st.number_input(
                f"Monthly Principal Repayment {i+1}", 
                value=0.0, 
                step=10_000.0, 
                format="%.2f", 
                key=f"payment_{i}"
            )
        
        structured_payments.append({'from_period': from_p, 'to_period': to_p, 'payment': payment})

# Capitalised Interest Parameters
capitalisation_months = 0
if repayment_structure == "Capitalised Interest":
    st.header("Capitalisation Period")
    capitalisation_months = st.number_input(
        "Months to Capitalise Interest", 
        min_value=1, 
        max_value=term_months, 
        value=12, 
        step=1
    )

# ───────────────────────────────────────────────────────────────
# CALCULATE SUGGESTED PAYMENT
# ───────────────────────────────────────────────────────────────

if repayment_structure == "Equal Installments":
    suggested_payment = abs(calculate_pmt(interest_rate / 100, term_months, full_capital, -residual))

elif repayment_structure == "Interest Only":
    suggested_payment = round(full_capital * (interest_rate / 100 / 12), 2)

elif repayment_structure == "Capitalised Interest":
    # FIX #2: Use compound interest, not simple interest
    remaining_months = term_months - capitalisation_months
    if remaining_months > 0:
        # Simulate actual compounding during capitalisation period
        sim_balance = full_capital
        for p in range(capitalisation_months):
            # Use variable rate if applicable
            if rate_structure == "Variable Rate":
                sim_rate = interest_rate  # Default
                for rp in rate_schedule:
                    if rp['from_period'] <= (p+1) <= rp['to_period']:
                        sim_rate = rp['total_rate']
                        break
            else:
                sim_rate = interest_rate
            
            sim_interest = round(sim_balance * (sim_rate / 100 / 12), 2)
            sim_balance = round(sim_balance + sim_interest, 2)
        
        estimated_balance = sim_balance
        suggested_payment = abs(calculate_pmt(interest_rate / 100, remaining_months, estimated_balance, -residual))
    else:
        suggested_payment = 0.0
else:
    suggested_payment = 0.0

st.subheader("Monthly Payment")
if repayment_structure != "Structured Capital":
    override = st.checkbox("Override calculated payment", value=False)
    if override:
        monthly_payment = st.number_input(
            "Monthly Payment Amount", 
            value=suggested_payment, 
            step=1000.0, 
            format="%.2f"
        )
    else:
        monthly_payment = suggested_payment
        st.info(f"Calculated payment: **R{monthly_payment:,.2f}**")
else:
    monthly_payment = 0.0
    st.info("Using structured payment schedule defined above")

# ───────────────────────────────────────────────────────────────
# GENERATE AMORTISATION SCHEDULE
# ───────────────────────────────────────────────────────────────

if st.button("Generate Amortisation Schedule", type="primary"):
    schedule = []
    balance = 0.0
    current_date = first_payment_date
    
    # FIX #3: Unified drawdown lookup - handles fees in multi-drawdown mode
    drawdown_lookup = {}
    
    if drawdown_structure == "Single Drawdown":
        drawdown_lookup[1] = full_capital
    else:
        # Multiple drawdowns
        for dd in drawdown_schedule:
            months_diff = (dd['date'].year - first_payment_date.year) * 12 + \
                         (dd['date'].month - first_payment_date.month)
            
            # FIX #4: Assign drawdowns before first payment to period 1
            period_num = 1 if months_diff < 0 else months_diff + 1
            
            if period_num > term_months:
                st.warning(f"Drawdown on {dd['date']} is after loan term – ignored")
                continue
            
            if period_num not in drawdown_lookup:
                drawdown_lookup[period_num] = 0.0
            drawdown_lookup[period_num] += dd['amount']
        
        # Add capitalised fees to period 1 in multi-drawdown mode
        if capitalise_fees and total_fees > 0:
            if 1 not in drawdown_lookup:
                drawdown_lookup[1] = 0.0
            drawdown_lookup[1] += total_fees
    
    # FIX #5: Custom capital by year-month only (not exact date)
    custom_capital_lookup = {}
    if use_custom_capital and custom_capital_schedule:
        for cc in custom_capital_schedule:
            # Match by year-month only
            key = f"{cc['date'].year}-{cc['date'].month:02d}"
            custom_capital_lookup[key] = cc['amount']
    
    # Main amortisation loop
    for period in range(1, term_months + 1):
        opening_balance = balance
        
        # Apply drawdown at beginning of period
        drawdown = drawdown_lookup.get(period, 0.0)
        balance += drawdown
        balance_before_interest = round(balance, 2)
        
        # Determine interest rate for this period
        if rate_structure == "Variable Rate":
            # FIX #6: Better variable rate lookup with forward-fill
            current_rate = None
            for rp in rate_schedule:
                if rp['from_period'] <= period <= rp['to_period']:
                    current_rate = rp['total_rate']
                    break
            
            # If no match, forward-fill from last known rate
            if current_rate is None:
                for rp in reversed(rate_schedule):
                    if rp['to_period'] < period:
                        current_rate = rp['total_rate']
                        break
            
            # Final fallback
            if current_rate is None:
                current_rate = rate_schedule[0]['total_rate']
        else:
            current_rate = interest_rate
        
        # Calculate interest
        interest = round(balance_before_interest * (current_rate / 100 / 12), 2)
        
        # Initialize payment variables
        regular_principal = 0.0
        regular_payment = interest
        is_cap_period = (repayment_structure == "Capitalised Interest" and period <= capitalisation_months)
        
        # Determine regular principal payment based on structure
        if is_cap_period:
            # Capitalise interest - negative principal
            regular_principal = -interest
            regular_payment = 0.0
        
        elif repayment_structure == "Equal Installments":
            regular_principal = monthly_payment - interest
            
            # Guard against negative amortisation
            if regular_principal < 0:
                regular_principal = 0.0
            
            regular_payment = monthly_payment
        
        elif repayment_structure == "Capitalised Interest":
            # After capitalisation period, treat like equal installments
            regular_principal = monthly_payment - interest
            
            # Guard against negative amortisation
            if regular_principal < 0:
                regular_principal = 0.0
            
            regular_payment = monthly_payment
        
        elif repayment_structure == "Interest Only":
            regular_principal = 0.0
            regular_payment = interest
        
        elif repayment_structure == "Structured Capital":
            # Find applicable payment structure
            structured_principal = 0.0
            for pay in structured_payments:
                if pay['from_period'] <= period <= pay['to_period']:
                    structured_principal = pay['payment']
                    break
            
            regular_principal = structured_principal
            regular_payment = interest + regular_principal
        
        # FIX #7: Proper residual handling for final period - ALL structures
        if period == term_months:
            if repayment_structure == "Interest Only":
                # Interest-only final period pays off balance minus residual
                regular_principal = max(0, balance_before_interest - residual)
                regular_payment = interest + regular_principal
            elif residual > 0:
                # All other structures: cap principal at balance minus residual
                max_principal = max(0, balance_before_interest - residual)
                regular_principal = min(regular_principal, max_principal)
                regular_payment = interest + regular_principal
        
        # Apply custom capital repayments
        custom_capital = 0.0
        date_key = f"{current_date.year}-{current_date.month:02d}"
        if date_key in custom_capital_lookup:
            custom_capital = custom_capital_lookup[date_key]
            # Cannot exceed what's left after regular repayment
            remaining_after_regular = balance_before_interest - regular_principal
            custom_capital = min(custom_capital, max(0, remaining_after_regular))
        
        # Calculate totals
        total_principal = regular_principal + custom_capital
        total_payment = interest + total_principal
        
        # Update balance
        balance = round(balance_before_interest - total_principal, 2)
        balance = max(0.0, balance)  # Never negative
        
        # Build row
        schedule.append({
            "Period": period,
            "Payment Date": current_date.strftime("%Y-%m-%d"),
            "Opening Balance": round(opening_balance, 2),
            "Drawdown": round(drawdown, 2),
            "Balance Before Interest": balance_before_interest,
            "Interest Rate %": round(current_rate, 4),
            "Interest": interest,
            "Regular Principal": round(regular_principal, 2),
            "Custom Capital": round(custom_capital, 2),
            "Total Principal": round(total_principal, 2),
            "Total Payment": round(total_payment, 2),
            "Ending Balance": balance,
        })
        
        current_date += relativedelta(months=1)
    
    # Final validation
    final_balance = balance
    if residual > 0:
        expected_final = residual
    else:
        expected_final = 0.0
    
    if abs(final_balance - expected_final) > 1.0:  # Allow R1 rounding tolerance
        st.warning(f"⚠️ Final balance R{final_balance:,.2f} differs from expected R{expected_final:,.2f}")
    
    df = pd.DataFrame(schedule)
    st.session_state.df = df
    
    # Display schedule
    st.subheader("Amortisation Schedule")
    st.dataframe(
        df.style.format({
            "Drawdown": "R{:,.2f}",
            "Opening Balance": "R{:,.2f}",
            "Balance Before Interest": "R{:,.2f}",
            "Interest Rate %": "{:.4f}%",
            "Interest": "R{:,.2f}",
            "Regular Principal": "R{:,.2f}",
            "Custom Capital": "R{:,.2f}",
            "Total Principal": "R{:,.2f}",
            "Total Payment": "R{:,.2f}",
            "Ending Balance": "R{:,.2f}",
        }),
        use_container_width=True,
        height=650
    )
    
    # FIX #8: Corrected summary metrics (exclude negative principal)
    st.subheader("Summary")
    cols = st.columns(5)
    
    total_drawn = df['Drawdown'].sum()
    total_interest = df['Interest'].sum()
    
    # Only sum positive principal (exclude capitalised interest periods)
    total_principal_repaid = df[df['Total Principal'] > 0]['Total Principal'].sum()
    
    total_custom = df['Custom Capital'].sum()
    final_bal = df['Ending Balance'].iloc[-1]
    
    cols[0].metric("Total Drawn", f"R{total_drawn:,.2f}")
    cols[1].metric("Total Interest", f"R{total_interest:,.2f}")
    cols[2].metric("Total Principal Repaid", f"R{total_principal_repaid:,.2f}")
    cols[3].metric("Total Custom Capital", f"R{total_custom:,.2f}")
    cols[4].metric("Final Balance", f"R{final_bal:,.2f}")
    
    # Excel export
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Input summary
        input_fields = [
            "Client Name", "Facility Name", "Facility Amount", "Residual", 
            "Repayment Structure", "Rate Structure", "Drawdown Structure", 
            "Term (Months)", "Capitalise Fees", "First Payment Date", 
            "Custom Capital Repayments"
        ]
        input_values = [
            client_name, facility_name, f"R{facility_amount:,.2f}", f"R{residual:,.2f}",
            repayment_structure, rate_structure, drawdown_structure,
            term_months, "Yes" if capitalise_fees else "No",
            first_payment_date.strftime("%Y-%m-%d"),
            "Yes" if use_custom_capital else "No"
        ]
        
        if capitalise_fees:
            for fee in custom_fees:
                input_fields.append(f"{fee['name']} ({fee['type']})")
                input_values.append(f"R{fee['amount']:,.2f}")
            input_fields.append("Total Fees")
            input_values.append(f"R{total_fees:,.2f}")
        
        input_fields.append("Full Capital Amount")
        input_values.append(f"R{full_capital:,.2f}")
        
        inputs_df = pd.DataFrame({"Field": input_fields, "Value": input_values})
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        
        # Schedule
        df.to_excel(writer, sheet_name="Schedule", index=False)
        
        # Additional sheets for complex structures
        if drawdown_structure == "Multiple Drawdowns":
            dd_df = pd.DataFrame(drawdown_schedule)
            dd_df['date'] = dd_df['date'].apply(lambda x: x.strftime("%Y-%m-%d"))
            dd_df.to_excel(writer, sheet_name="Drawdown Schedule", index=False)
        
        if rate_structure == "Variable Rate":
            rate_df = pd.DataFrame(rate_schedule)
            rate_df.to_excel(writer, sheet_name="Rate Schedule", index=False)
        
        if repayment_structure == "Structured Capital":
            payment_df = pd.DataFrame(structured_payments)
            payment_df.to_excel(writer, sheet_name="Payment Structure", index=False)
        
        if use_custom_capital:
            custom_df = pd.DataFrame(custom_capital_schedule)
            custom_df['date'] = custom_df['date'].apply(lambda x: x.strftime("%Y-%m-%d"))
            custom_df.to_excel(writer, sheet_name="Custom Capital", index=False)
    
    buffer.seek(0)
    
    # Smart filename
    clean_client = "".join(c for c in client_name if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    clean_facility = "".join(c for c in facility_name if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    filename = f"{clean_client}_{clean_facility}_Amort_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    st.download_button(
        "Download Excel", 
        buffer, 
        file_name=filename, 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )