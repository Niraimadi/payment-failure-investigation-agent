
import streamlit as st

from src.agent import investigate_payment
from src.database import save_review, get_review, get_all_reviews

st.set_page_config(
    page_title="Payment Failure Investigation",
    page_icon="💳",
    layout="centered"
)

st.title("💳 Payment Failure Investigation Agent")

st.write(
    "Investigate payment transactions using AI. "
    "Understand failure reasons, retrieve troubleshooting "
    "guidance, and record human review decisions."
)

st.divider()

transaction_id = st.text_input(
    "Enter Transaction ID",
    placeholder="Example: TXN-10025"
)

if st.button("Investigate Payment", type="primary"):
    if not transaction_id.strip():
        st.warning("Please enter a transaction ID.")
    else:
        try:
            with st.spinner("Investigating transaction using AI..."):
                result = investigate_payment(transaction_id.strip())

            st.session_state["investigation_result"] = result
            st.session_state["investigated_id"] = transaction_id.strip()

        except Exception as e:
            st.error(f"Investigation failed: {e}")

# Display the stored investigation result
result = st.session_state.get("investigation_result")
investigated_id = st.session_state.get("investigated_id")

if result and investigated_id == transaction_id.strip():

    transaction = result.get("transaction")

    if not transaction:
        st.error("Transaction not found.")
        st.write(result.get("report"))

    else:
        st.subheader("Transaction Details")

        col1, col2, col3 = st.columns(3)
        col1.metric("Amount", f"₹{transaction['amount']:,.2f}")
        col2.metric("Status", transaction["status"])
        col3.metric("Retry Count", transaction["retry_count"])

        st.write("**Transaction ID:**", transaction["transaction_id"])
        st.write("**Payment Method:**", transaction["payment_method"])
        st.write("**Failure Code:**", transaction["failure_code"] or "N/A")
        st.write("**Failure Message:**", transaction["failure_message"] or "N/A")

        st.divider()

        st.subheader("🤖 AI Investigation Report")
        st.markdown(result.get("report", "No report generated."))

        st.caption(
            "AI-generated analysis based on synthetic transaction "
            "data and the available troubleshooting knowledge."
        )

        with st.expander("View Retrieved Troubleshooting Knowledge"):
            knowledge = result.get("knowledge", [])

            if knowledge:
                for item in knowledge:
                    st.markdown(f"**Section:** {item['section']}")
                    st.markdown(f"**Failure Code:** {item['failure_code']}")
                    st.markdown(item["content"])
                    st.divider()
            else:
                st.info("No troubleshooting knowledge was retrieved.")

        st.divider()

        st.subheader("Human Review Assessment")

        if result.get("requires_human_review"):

            st.warning(
                "Manual Review Required: "
                + result.get("review_reason", "")
            )

            existing_review = get_review(investigated_id)

            if existing_review:
                st.markdown("**Previous Review Record**")
                st.write("Reviewer:", existing_review["reviewer"])
                st.write("Decision:", existing_review["decision"])
                st.write("Notes:", existing_review["review_notes"])
                st.write("Reviewed at:", existing_review["reviewed_at"])
                st.divider()

            st.markdown("**Submit Human Review**")

            with st.form(f"review_form_{investigated_id}"):

                reviewer = st.text_input(
                    "Reviewer Name",
                    value="Demo Reviewer"
                )

                decision = st.selectbox(
                    "Review Decision",
                    [
                        "Reviewed - No Further Action",
                        "Escalated for Further Investigation"
                    ]
                )

                review_notes = st.text_area(
                    "Review Notes",
                    placeholder="Enter investigation findings or escalation details..."
                )

                submitted = st.form_submit_button(
                    "Save Review",
                    type="primary"
                )

                if submitted:
                    if not reviewer.strip():
                        st.error("Please enter the reviewer name.")
                    else:
                        save_review(
                            transaction_id=investigated_id,
                            reviewer=reviewer.strip(),
                            decision=decision,
                            review_notes=review_notes.strip()
                        )

                        st.success("Human review saved successfully!")
                        st.rerun()

        else:
            st.success("No immediate manual review required.")

st.divider()

st.subheader("📋 Human Review History")

reviews = get_all_reviews()

if reviews:
    st.caption(f"Showing {len(reviews)} review record(s).")

    st.dataframe(
        reviews,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No human review records available yet.")
