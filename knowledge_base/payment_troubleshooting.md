
# Payment Troubleshooting Knowledge Base

## 1. UPI_TIMEOUT

Category: UPI
Description: The UPI payment request did not receive a response within the expected time.

Possible causes:
- Temporary delay in the bank server.
- Network connectivity issues.
- Delayed response from the payment gateway.

Recommended investigation:
- Check the payment gateway response logs.
- Verify the transaction status with the payment provider.
- Check whether a delayed success confirmation was received.

Recommended action:
- Do not immediately initiate another payment.
- Verify the original transaction status before considering a retry.
- Escalate if the status remains unresolved.

## 2. INSUFFICIENT_FUNDS

Category: CARD
Description: The issuing bank declined the transaction because sufficient funds or available credit were not available.

Possible causes:
- Insufficient account balance.
- Insufficient available credit limit.

Recommended investigation:
- Verify the bank's decline response.
- Confirm the transaction amount and response code.

Recommended action:
- Inform the customer that the issuing bank declined the payment.
- Suggest checking the available balance or using another payment method.

## 3. GATEWAY_TIMEOUT

Category: PAYMENT_GATEWAY
Description: The payment gateway did not return a response within the expected time.

Possible causes:
- Temporary gateway service disruption.
- Network latency.
- Delayed communication with the acquiring bank.

Recommended investigation:
- Inspect gateway logs and response timestamps.
- Verify the final payment status with the provider.
- Check for delayed callbacks or webhook events.

Recommended action:
- Avoid duplicate payment attempts until the original status is verified.
- Escalate persistent gateway issues for technical investigation.

## 4. BANK_DECLINED

Category: NET_BANKING
Description: The bank declined the payment request.

Possible causes:
- Bank-side transaction restrictions.
- Temporary banking service issues.
- Bank-specific validation failures.

Recommended investigation:
- Inspect the bank response code.
- Verify whether the bank reported a specific decline reason.

Recommended action:
- Communicate the decline to the customer.
- Escalate unclear or recurring bank declines for further investigation.

## Important Investigation Guidelines

- Always distinguish confirmed transaction facts from possible causes.
- Never assume a payment succeeded or failed without verified status.
- Never initiate refunds, retries, or payment operations automatically.
- Escalate unresolved or ambiguous cases for human review.
- Treat this knowledge base as demonstration guidance, not official payment-provider documentation.
