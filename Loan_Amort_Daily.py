import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.title("Daily Prime-Linked Loan Amortization")

# Inputs
loan_amount = st.number_input("Loan Amount", min_value=0.0, value=1000000.0)

rate_type = st.selectbox("Rate Type", ["Floating", "Fixed"])

if rate_type == "Floating":
    prime_rate = st.number_input("Initial Prime Rate (%)", min_value=0.0, value=11.0)
    margin = st.number_input("Margin above Prime (%)", min_value=-5.0, value=2.5, step=0.25)
    effective_rate = prime_rate + margin
    st.write(f"Initial Effective Rate: {effective_rate}%")
    
    st.subheader("Prime Rate Changes")
    num_rate_changes = st.number_input("Number of prime rate changes", min_value=0, max_value=20, value=0)
    
    prime_changes = [{'date': None, 'rate': prime_rate}]  # Start with initial rate
    
    for i in range(num_rate_changes):
        col1, col2 = st.columns(2)
        with col1:
            change_date = st.date_input(f"Rate change {i+1} date", key=f"rate_date_{i}")
        with col2:
            new_prime = st.number_input(f"New prime rate {i+1} (%)", min_value=0.0, value=prime_rate, key=f"rate_{i}")
        prime_changes.append({'date': change_date, 'rate': new_prime})
    
    # Sort by date
    prime_changes.sort(key=lambda x: (x['date'] is None, x['date']))
else:
    effective_rate = st.number_input("Fixed Rate (%)", min_value=0.0, value=13.5)
    prime_rate = None
    margin = None
    prime_changes = []

start_date = st.date_input("Start Date", value=datetime(2025, 3, 1))
term_months = st.number_input("Term (months)", min_value=1, value=12)

# Repayment structure
repayment_type = st.selectbox("Repayment Type", ["Interest Only", "Amortising", "Bullet", "Custom"])

# Payment schedule
st.subheader("Payment Schedule")
payment_frequency = st.selectbox("Payment Frequency", ["Monthly", "Quarterly", "Annual", "Custom"])

# Calculate payment amounts based on repayment type
payment_amount = 0
monthly_payment = 0
custom_payments = []

if repayment_type == "Amortising":
    if payment_frequency == "Monthly":
        # Standard amortizing payment calculation
        monthly_rate = (effective_rate / 100) / 12
        num_payments = term_months
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        st.write(f"Calculated Monthly Payment: ${monthly_payment:,.2f}")
        payment_amount = st.number_input("Monthly Payment Amount (calculated above)", min_value=0.0, value=monthly_payment)
    elif payment_frequency == "Quarterly":
        quarterly_rate = (effective_rate / 100) / 4
        num_payments = term_months / 3
        quarterly_payment = loan_amount * (quarterly_rate * (1 + quarterly_rate)**num_payments) / ((1 + quarterly_rate)**num_payments - 1)
        st.write(f"Calculated Quarterly Payment: ${quarterly_payment:,.2f}")
        payment_amount = st.number_input("Quarterly Payment Amount (calculated above)", min_value=0.0, value=quarterly_payment)
    elif payment_frequency == "Annual":
        annual_rate = effective_rate / 100
        num_payments = term_months / 12
        annual_payment = loan_amount * (annual_rate * (1 + annual_rate)**num_payments) / ((1 + annual_rate)**num_payments - 1)
        st.write(f"Calculated Annual Payment: ${annual_payment:,.2f}")
        payment_amount = st.number_input("Annual Payment Amount (calculated above)", min_value=0.0, value=annual_payment)
elif repayment_type == "Interest Only":
    payment_amount = st.number_input("Principal Payment Amount (optional)", min_value=0.0, value=0.0)
    st.info("Interest capitalizes monthly. Add principal payments if needed.")
elif repayment_type == "Bullet":
    payment_amount = 0
    st.info("Full principal repayment at maturity. Interest capitalizes monthly.")
else:  # Custom
    payment_amount = st.number_input("Payment Amount", min_value=0.0, value=0.0)

if payment_frequency == "Custom":
    st.write("Enter custom payment schedule:")
    num_payments = st.number_input("Number of custom payments", min_value=0, max_value=50, value=0)
    
    for i in range(num_payments):
        col1, col2 = st.columns(2)
        with col1:
            payment_date = st.date_input(f"Payment {i+1} Date", key=f"date_{i}")
        with col2:
            amount = st.number_input(f"Payment {i+1} Amount", min_value=0.0, key=f"amount_{i}")
        custom_payments.append({'date': payment_date, 'amount': amount})
elif payment_frequency != "Custom":
    payment_day = st.number_input("Payment Day of Month", min_value=1, max_value=28, value=1)

if st.button("Generate Amortization"):
    if loan_amount > 0 and effective_rate > 0:
        # Calculate daily schedule
        current_date = start_date
        end_date = start_date + relativedelta(months=term_months)
        
        schedule = []
        balance = loan_amount
        cumulative_interest = 0
        
        while current_date <= end_date:
            beginning_balance = balance
            
            # Determine current prime rate and effective rate (for floating)
            if rate_type == "Floating":
                current_prime = prime_rate
                for change in prime_changes:
                    if change['date'] is not None and current_date >= change['date']:
                        current_prime = change['rate']
                effective_rate = current_prime + margin
                daily_rate = (effective_rate / 100) / 365
            else:
                current_prime = None
                daily_rate = (effective_rate / 100) / 365
            
            # Daily interest
            daily_interest = balance * daily_rate
            cumulative_interest += daily_interest
            
            # Check for payment
            capital_payment = 0
            if payment_frequency == "Monthly" and current_date.day == payment_day:
                capital_payment = payment_amount
                balance -= capital_payment
            elif payment_frequency == "Quarterly" and current_date.day == payment_day and current_date.month % 3 == (start_date.month % 3):
                capital_payment = payment_amount
                balance -= capital_payment
            elif payment_frequency == "Annual" and current_date.day == payment_day and current_date.month == start_date.month:
                capital_payment = payment_amount
                balance -= capital_payment
            elif payment_frequency == "Custom":
                # Check if there's a payment on this date
                for payment in custom_payments:
                    if payment['date'] == current_date:
                        capital_payment = payment['amount']
                        balance -= capital_payment
                        break
            
            # Check if maturity date for bullet repayment
            if repayment_type == "Bullet" and current_date == end_date:
                capital_payment = loan_amount
                balance -= capital_payment
            
            # Check if month-end - capitalize interest
            next_day = current_date + timedelta(days=1)
            if next_day.month != current_date.month or current_date == end_date:
                balance += cumulative_interest
                month_interest = cumulative_interest
                cumulative_interest = 0
            else:
                month_interest = None
            
            schedule.append({
                'Date': current_date,
                'Beginning Principal': round(beginning_balance, 2),
                'Prime Rate (%)': current_prime if rate_type == "Floating" else None,
                'Margin (%)': margin if rate_type == "Floating" else None,
                'Effective Rate (%)': effective_rate,
                'Daily Rate': round(daily_rate, 8),
                'Daily Interest': round(daily_interest, 2),
                'Capital Payment': round(capital_payment, 2) if capital_payment > 0 else None,
                'Ending Principal': round(balance, 2),
                'Monthly Interest': round(month_interest, 2) if month_interest else None
            })
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(schedule)
        st.dataframe(df, height=600)
        
        # Summary
        st.subheader("Summary")
        total_interest = df['Daily Interest'].sum()
        total_payments = df['Capital Payment'].sum()
        st.write(f"Total Interest Paid: ${total_interest:,.2f}")
        st.write(f"Total Capital Payments: ${total_payments:,.2f}")
        st.write(f"Final Balance: ${balance:,.2f}")