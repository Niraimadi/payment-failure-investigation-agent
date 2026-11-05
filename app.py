import streamlit as st
from src.agent import investigate_payment

# Page configuration
st.set_page_config(
    page_title="Payment Failure Investigation",
    page_icon="💳",
    layout="centered"
)

# Application title
st.title("💳 Payment Failure Investigation Agent")

st.write(
    "Investigate payment transactions using AI. "
    "Enter a transaction ID to understand its status, "
    "possible failure reasons, and recommended next steps."
)

st.divider()

# Transaction input
transaction_id = st.text_input(
    "Enter Transaction ID",
    placeholder="Example: TXN-10025"
)

# Investigation button
if st.button("Investigate Payment", type="primary"):

    if not transaction_id.strip():
        st.warning("Please enter a transaction ID.")

    else:
        try:
            with st.spinner("Investigating transaction using AI..."):

                result = investigate_payment(transaction_id.strip())

            transaction = result.get("transaction")

            if not transaction:
                st.error("Transaction not found.")
                st.write(result.get("report"))

            else:
                # Display transaction information
                st.subheader("Transaction Details")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Amount",
                    f"₹{transaction['amount']:,.2f}"
                )

                col2.metric(
                    "Status",
                    transaction["status"]
                )

                col3.metric(
                    "Retry Count",
                    transaction["retry_count"]
                )

                st.write("**Transaction ID:**", transaction["transaction_id"])
                st.write("**Payment Method:**", transaction["payment_method"])
                st.write("**Failure Code:**", transaction["failure_code"] or "N/A")
                st.write("**Failure Message:**", transaction["failure_message"] or "N/A")

                st.divider()

                # Display AI investigation report
                st.subheader("🤖 AI Investigation Report")

                st.markdown(result.get("report", "No report generated."))

                st.caption(
                    "AI-generated analysis based on the available "
                    "transaction data. No payment operation has been performed."
                )

        except Exception as e:
            st.error(f"Investigation failed: {e}")