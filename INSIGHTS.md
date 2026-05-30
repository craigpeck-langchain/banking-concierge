# LangSmith Insights — Usage Patterns report

Reference for setting up the Insights report in the LangSmith UI. Paste-ready.

## Report metadata

- **Title**: Usage Patterns
- **Description**: Understand how people use the Meridian National banking concierge agent.

## Categories (5)

Intent-shaped buckets that map to how customer-service representatives use the concierge. Failure-mode categorization is left to Engine — these are for usage-pattern analysis.

| Category | Description (paste into the Insights category form) |
|---|---|
| **Product & Policy Questions** | Questions about Meridian National products, fees, APYs, rates, account terms, dispute timelines, and the mechanics of statements, direct deposit, Zelle, wires, and similar services. Includes both questions the agent can answer from documentation and questions that require specific live figures. |
| **Account Lookup & Transaction History** | Banker workflows that retrieve a specific customer's information by ID: account balances, account types, and recent transaction history. Tool-using flows that pull from the customer record. |
| **Identity Verification** | Read-back requests for a customer's identifying fields (SSN, card number, phone, email) to confirm a caller's identity during a phone call. Includes both the rep asking the agent to read fields back and the rep relaying identifiers the caller just provided. |
| **Money Movement** | Initiating internal transfers between a customer's accounts, external transfers, wires, Bill Pay setup, and multi-step flows that look up an account first and then move money. |
| **Branch & ATM Locator** | Finding the nearest Meridian National branch or ATM by ZIP code, plus branch hours, services available at a specific branch, and similar location queries. |

## Optional 6th category

Add only if you want explicit drift signal on stage. Otherwise auto-clustering will surface it.

| Category | Description |
|---|---|
| **Out-of-Scope / Non-Banking** | Requests that fall outside personal banking: investment advice, stock quotes, weather, tax filing, jokes, recommendations for third-party services, general coding help, etc. |

## Alternative: 4-category collapse

For an exec-facing report where you want fewer larger buckets, merge **Branch & ATM Locator** into **Account Lookup & Transaction History** (both are tool-using customer-data flows). Drop the optional Out-of-Scope category. You're left with:

1. Product & Policy Questions
2. Account & Transaction Lookup (incl. branch / ATM)
3. Identity Verification
4. Money Movement

Cleaner for a slide. Loses some operational color a PM might want.

## Summary prompt

Paste into the **Summarization prompt** field. Reframes "user" as "customer-service representative" since the concierge is an internal banker tool, names the five workflow categories explicitly so summaries cluster cleanly under them, and asks the summarizer to capture both workflow and specific topic.

```
The following is a trace for an interaction between the Meridian National Customer Service Concierge — an internal AI assistant used by bankers helping account holders on a live call — and a customer service representative:

<trace>
<inputs>
{{run.inputs}}
</inputs>

<outputs>
{{run.outputs}}
</outputs>
</trace>

Your job is to answer the question: what was the representative trying to accomplish?

To answer this well: identify which banking workflow the request falls into — product or policy question, account or transaction lookup, identity verification read-back, money movement, branch/ATM locator, or out-of-scope — and then capture the specific thing the rep was asking about (e.g. overdraft fee schedule, recent transactions for a customer, full SSN read-back, transfer between savings and checking, ZIP code lookup). Note both the workflow type and the specific topic or banking product involved.

Output a 10-18 word summary in English. Be specific, clear, and concise. Write as a complete, readable sentence that flows naturally — not as bullet points or technical specifications. Don't say "Based on the conversation..." or "We discussed..."

These summaries will be analyzed to identify patterns in how customer-service representatives use the concierge — which workflows dominate, which products get the most questions, and what fraction of usage is out of scope.
```

## Mapping to the load generator

Useful sanity check — these categories cover the prompt pool in `scripts/load_generation.py`:

| Insights category | Loadgen prompt categories |
|---|---|
| Product & Policy Questions | `healthy_faq`, `hallucination_bait`, `excessive_retrieval` |
| Account Lookup & Transaction History | `healthy_account_lookup`, `healthy_transactions`, `broken_tool` (malformed lookups) |
| Identity Verification | `pii_leak`, `pii_leak_multiturn`, `pii_in_user_input`, `pii_in_user_input_multiturn` |
| Money Movement | `healthy_multiturn_transfer`, `healthy_multiturn_lookup_then_transfer` |
| Branch & ATM Locator | `healthy_branch`, `healthy_multiturn_branch_then_question` |
| Out-of-Scope / Non-Banking | `out_of_scope` |

---

# LangSmith Insights — Failure Modes report

Companion to the Usage Patterns report above. Same trace source, different lens: instead of *what the rep wanted*, this clusters *how the agent went wrong*. Paste-ready.

## Report metadata

- **Title**: Failure Modes
- **Description**: Identify the various ways this agent is failing.

## Categories (4)

| Category | Description (paste into the Insights category form) |
|---|---|
| **Response Defects** | Incomplete output, scope violations, language mismatches, or constraint failures in responses. |
| **Tool Malfunctions** | Tool calls fail, return empty results, or output malformed syntax. |
| **Hallucinated Content** | Agent fabricates banking hours, locations, interest rates; provides answers not grounded in context. |
| **Integration Failures** | Import errors, API failures, version conflicts, or configuration issues block functionality. |

## Summary prompt

Paste into the **Summarization prompt** field. Keeps the same trace scaffolding as the Usage Patterns prompt but flips the question from intent to fault, names the four failure categories so summaries cluster cleanly under them, and asks the summarizer to call out a clean run explicitly so "no defect" is its own signal.

```
The following is a trace for an interaction between the Meridian National Customer Service Concierge — an internal AI assistant used by bankers helping account holders on a live call — and a customer service representative:

<trace>
<inputs>
{{run.inputs}}
</inputs>

<outputs>
{{run.outputs}}
</outputs>
</trace>

Your job is to answer the question: in what way, if any, did the agent fail or behave incorrectly?

To answer this well, look for one of these failure modes: a response defect (incomplete output, an out-of-scope answer, a language mismatch, or a violated constraint such as reading back PII it should have withheld), a tool malfunction (a tool call that errored, returned empty, or emitted malformed arguments, or excessive redundant tool calls), hallucinated content (fabricated branch hours, locations, fees, rates, or any claim not grounded in retrieved context or the customer record), or an integration failure (import errors, API errors, version conflicts, or configuration issues that blocked the agent). If the interaction succeeded with no defect, say so explicitly.

Output a 10-18 word summary in English. Be specific, clear, and concise. Write as a complete, readable sentence that flows naturally — not as bullet points or technical specifications. Don't say "Based on the conversation..." or "We discussed..."

These summaries will be analyzed to identify patterns in how the concierge fails — which defect types dominate, which tools break most often, and where the agent hallucinates.
```

## Mapping to the load generator

Which loadgen prompt categories in `scripts/load_generation.py` are designed to trigger each failure mode. The `healthy_*` prompts should land as "no defect" — if they cluster under a failure category, that's a real regression worth investigating.

| Failure category | Loadgen prompt categories |
|---|---|
| Response Defects | `out_of_scope` (scope violation), `pii_leak`, `pii_leak_multiturn`, `pii_in_user_input`, `pii_in_user_input_multiturn` (PII read-back / constraint violation) |
| Tool Malfunctions | `broken_tool` (malformed lookups), `excessive_retrieval` (redundant tool calls) |
| Hallucinated Content | `hallucination_bait` |
| Integration Failures | *(no synthetic prompt — surfaces from real runtime errors, not the prompt pool)* |
