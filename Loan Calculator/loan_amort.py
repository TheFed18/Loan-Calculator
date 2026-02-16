import streamlit as st

st.title("Loan Amortization Calculator")

loan_amount = st.number_input("Loan Amount", min_value=0.0)
interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0)
term_years = st.number_input("Term (years)", min_value=1)
if loan_amount > 0 and interest_rate > 0 and term_years > 0:
    # Calculate monthly payment
    monthly_rate = interest_rate / 100 / 12
    num_payments = term_years * 12
    
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    # Build amortization schedule
    balance = loan_amount
    schedule = []
    
    for payment_num in range(1, num_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        schedule.append({
            'Payment': payment_num,
            'Payment Amount': round(monthly_payment, 2),
            'Principal': round(principal_payment, 2),
            'Interest': round(interest_payment, 2),
            'Balance': round(balance, 2)
        })
    
    import pandas as pd
    df = pd.DataFrame(schedule)
    
    st.write(f"Monthly Payment: ${monthly_payment:,.2f}")
    st.dataframe(df)