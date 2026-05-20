# Integration Architecture Diagram

## Complete System Flow with LangSmith

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                                       │
│                                                                                   │
│  curl -X POST http://localhost:8000/agent/sql \                                 │
│    -d '{"question": "How many customers?"}'                                      │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI SERVER (main.py)                                 │
│                                                                                   │
│  • Receives request                                                              │
│  • Initializes AgentState                                                        │
│  • Calls setup_langsmith() → Enables tracing                                     │
│  • Invokes compiled_graph.invoke(state)                                          │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW (workflow.py)                              │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ [THINK] schema_discoverer Node                                        │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  Input: question                                                      │    │
│  │  ├─ Tool: list_tables()                                              │    │
│  │  │   └─ PostgreSQL → Get all tables                                  │    │
│  │  ├─ Tool: get_schema(tables)                                         │    │
│  │  │   └─ PostgreSQL → Get CREATE TABLE DDL                           │    │
│  │  Output: tables[], schema                                            │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures:                                              │    │
│  │     • Tool call inputs and outputs                                   │    │
│  │     • Execution time                                                 │    │
│  │     • Any errors during discovery                                    │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                              ↓                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ [PLAN] planning Node                                                  │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  Input: question, tables, schema                                      │    │
│  │  ├─ LLM Call: "Create step-by-step SQL strategy"                      │    │
│  │  └─ Output: plan (joins, filters, aggregations)                       │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures:                                               │    │
│  │     • LLM prompt sent                                                 │    │
│  │     • LLM response (model, tokens, cost)                             │    │
│  │     • Generation time                                                 │    │
│  │     • Plan quality assessment                                         │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                              ↓                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ [ACT] sql_generation Node                                             │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  Input: question, schema, plan                                        │    │
│  │  ├─ LLM Call: "Generate PostgreSQL based on plan"                     │    │
│  │  ├─ Output: SQL (with markdown stripping)                             │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures:                                               │    │
│  │     • LLM prompt and response                                         │    │
│  │     • Raw SQL generated                                               │    │
│  │     • Markdown stripping operation                                    │    │
│  │     • Generation latency                                              │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                              ↓                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ [ACT] sql_validation Node  (❌ ERROR DETECTION START)                 │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  Input: sql, schema, (error context if retrying)                      │    │
│  │  ├─ Check: SQL syntax                                                 │    │
│  │  ├─ Check: Table names exist in schema                                │    │
│  │  ├─ Check: Column names exist                                         │    │
│  │  ├─ If error:                                                         │    │
│  │  │   ├─ LLM Call: "Fix this SQL error"                                │    │
│  │  │   │   (ERROR CONTEXT PASSED HERE!)                                 │    │
│  │  │   └─ Output: corrected validated_sql                               │    │
│  │  └─ If success: Output: validated_sql                                 │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures (DETAILED):                                     │    │
│  │     • Validation checks performed                                      │    │
│  │     • Error detection (if any)                                         │    │
│  │     • Error context passed to LLM                                      │    │
│  │     • LLM self-correction attempt                                      │    │
│  │     • Fixed SQL output                                                 │    │
│  │     • Validation latency                                               │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                              ↓                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ [EXECUTE] executor Node                                               │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  Input: validated_sql                                                 │    │
│  │  ├─ Tool: run_query(validated_sql)                                    │    │
│  │  │   ├─ PostgreSQL: Execute actual query                              │    │
│  │  │   └─ Return: {success, rows, columns, error}                       │    │
│  │  Output: execution dict                                               │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures:                                                │    │
│  │     • SQL being executed                                               │    │
│  │     • Query result (rows, columns)                                     │    │
│  │     • Success/error status                                             │    │
│  │     • Execution time (DB latency)                                      │    │
│  │     • Row count                                                        │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                              ↓                                                   │
│  ┌─────── CONDITIONAL ROUTING: should_retry() ─────┐                          │
│  │  Check: execution.success?                       │                          │
│  │  Check: retries < max_retries (3)?               │                          │
│  └─────────────┬──────────────────────┬─────────────┘                          │
│               │                        │                                        │
│            NO │                        │ YES                                    │
│               │                        │                                        │
│               │                        ↓                                        │
│               │          ┌──────────────────────────────┐                      │
│               │          │ [RECOVER] retry_handler Node │                      │
│               │          ├──────────────────────────────┤                      │
│               │          │ retries += 1                 │                      │
│               │          │ sql ← validated_sql          │ ← LOOP BACK          │
│               │          │ (corrected SQL for next try) │   (max 3 times)      │
│               │          └────────────┬─────────────────┘                      │
│               │                       │                                        │
│               │                       ↓ (Loop edge)                            │
│               │                  [ACT] sql_validation  ← WITH ERROR CONTEXT    │
│               │                                                                │
│               └─────────────────────┬─────────────────────────────────────────┘
│                                     ↓                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ END - Return Final State                                              │    │
│  ├────────────────────────────────────────────────────────────────────────┤    │
│  │  • question, sql, executed_sql                                        │    │
│  │  • execution (result/error)                                           │    │
│  │  • retries (0-3)                                                      │    │
│  │  • trace (all steps)                                                  │    │
│  │                                                                      │    │
│  │  📊 LangSmith Captures:                                                │    │
│  │     • Final state of all variables                                     │    │
│  │     • Total execution time                                             │    │
│  │     • Retry count (if any)                                             │    │
│  │     • Trace of all nodes                                               │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │ final_state
                  ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    RESPONSE PREPARATION (main.py)                               │
│                                                                                   │
│  • Extract results from final_state                                              │
│  • Get LangSmith URL: get_langsmith_url()                                        │
│  • Build SQLAgentResponse                                                        │
│  • Include langsmith_url field                                                   │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         HTTP RESPONSE                                            │
│                                                                                   │
│  {                                                                               │
│    "question": "How many customers?",                                            │
│    "sql": "SELECT COUNT(*) FROM customers",                                      │
│    "result": 122,                                                                │
│    "status": "success",                                                          │
│    "retries": 0,                                                                 │
│    "trace": [                                                                    │
│      "[Schema Discovery] Found tables: ['customers', 'orders', ...]",            │
│      "[Planning] Planning SQL strategy: ...",                                    │
│      "[SQL Generation] Generated SQL: ...",                                      │
│      "[SQL Validation] SQL validation successful",                               │
│      "[Execution] Query executed successfully"                                   │
│    ],                                                                            │
│    "langsmith_url": "https://smith.langchain.com/o/projects/p/..."             │
│  }                                                                               │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    LANGSMITH OBSERVABILITY PLATFORM                              │
│                    (https://smith.langchain.com/)                                │
│                                                                                   │
│  Dashboard shows:                                                                │
│  ├─ Trace Timeline                                                               │
│  │  └─ All 5-6 nodes visualized with timing                                      │
│  │                                                                               │
│  ├─ Node Details (Expandable)                                                    │
│  │  ├─ schema_discoverer: Tool calls + results                                   │
│  │  ├─ planner: LLM prompt + response + tokens + cost                            │
│  │  ├─ sql_generator: LLM prompt + response + tokens + cost                       │
│  │  ├─ sql_validator: Validation logic + error context + fix                     │
│  │  ├─ executor: SQL executed + rows returned + latency                          │
│  │  └─ retry_handler: Retry count + loop decision                                │
│  │                                                                               │
│  ├─ Performance Analytics                                                        │
│  │  ├─ Total latency per trace                                                   │
│  │  ├─ Latency per node                                                          │
│  │  ├─ LLM token usage                                                           │
│  │  ├─ LLM cost estimate                                                         │
│  │  └─ Success/failure rate                                                      │
│  │                                                                               │
│  ├─ Error Analysis (if failed)                                                   │
│  │  ├─ Error message from DB                                                     │
│  │  ├─ Which node failed                                                         │
│  │  ├─ Retry attempts shown                                                      │
│  │  └─ Final error if max retries exceeded                                       │
│  │                                                                               │
│  └─ Comparison & Export                                                          │
│     ├─ Compare variants (v1 vs v2)                                               │
│     ├─ Export traces for analysis                                                │
│     └─ Share with team                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Self-Correction Loop - Detailed View

```
┌─────────────────────────────────────────────────────────────┐
│           RETRY LOOP WITH ERROR CONTEXT (LangSmith View)     │
└─────────────────────────────────────────────────────────────┘

ATTEMPT 1 (First Try)
═════════════════════════════════════════════════════════════

[sql_generation]
  LLM → "Generate SQL"
  Output: SELECT total_amount FROM payments

                         ↓

[sql_validation]
  Check: Syntax ✓
  Check: Table "payments" exists? ✓
  Check: Column "total_amount" exists? ✗

  ERROR DETECTED!
  Error Message: "column 'total_amount' does not exist"

                         ↓

[execution]
  Query Failed ✗
  Error: column 'total_amount' does not exist

                         ↓

[should_retry]
  success = false
  retries = 0 < 3
  Decision: RETRY

                         ↓

[retry_handler]
  retries = 1
  sql ← validated_sql  (ready for another attempt)
  Loop back to sql_validation ↻

                         ↓

ATTEMPT 2 (With Error Context)
═════════════════════════════════════════════════════════════

[sql_validation] (Called again with error context)
  Input:
    • sql: SELECT total_amount FROM payments
    • schema: CREATE TABLE payments (id INT, amount DECIMAL, ...)
    • error: "column 'total_amount' does not exist"  ← ERROR CONTEXT!

  LLM sees error!
  LLM → "Fix this: column 'total_amount' does not exist"
  LLM Output: SELECT amount FROM payments  ← FIXED!

  Check: Syntax ✓
  Check: Table "payments" exists? ✓
  Check: Column "amount" exists? ✓

  Output: validated_sql = "SELECT amount FROM payments"

                         ↓

[execution]
  Query Succeeded ✓
  Result: 2500 rows

                         ↓

[should_retry]
  success = true
  Decision: DONE

                         ↓

LANGSMITH SHOWS:
═════════════════════════════════════════════════════════════

Trace Timeline:
  1. schema_discoverer: 0.5s ✓
  2. planner: 2.1s ✓
  3. sql_generation: 1.8s ✓
  4. sql_validation: 0.3s ⚠ (detected error)
  5. execution: 0.1s ✗ (query failed)
  6. retry_handler: 0.1s ↻ (retry initiated)
  ───────────────── RETRY LOOP ─────────────────
  7. sql_validation: 0.4s ✓ (error fixed by LLM!)
  8. execution: 0.1s ✓ (query succeeded)

Total: 5.3s with 1 retry

Observability View:
  ✓ Error detected at step 5
  ✓ Retry loop triggered
  ✓ LLM received error context
  ✓ LLM generated fix
  ✓ Query succeeded on retry
  ✓ Complete trace captured
```

## Data Flow Through AgentState

```
┌─────────────────────────────────────────────────────────────┐
│              AGENTSTATE EVOLUTION                            │
│         (TypedDict - Type Safe + Observable)                │
└─────────────────────────────────────────────────────────────┘

INITIAL STATE
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": [],
  "schema": "",
  "plan": "",
  "sql": "",
  "validated_sql": "",
  "execution": {},
  "retries": 0,
  "max_retries": 3,
  "trace": []
}

                         ↓

AFTER schema_discoverer
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", "orders", "products", "employees", "offices"],
  "schema": "CREATE TABLE customers (...columns...)",
  "plan": "",
  "sql": "",
  "validated_sql": "",
  "execution": {},
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: ['customers', 'orders', ...]"
  ]
}

                         ↓

AFTER planner
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", ...],
  "schema": "CREATE TABLE customers (...)",
  "plan": "Step 1: Count from customers table",  ← NEW
  "sql": "",
  "validated_sql": "",
  "execution": {},
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: [...]",
    "[Planning] Planning SQL strategy: Step 1 - Count..."  ← NEW
  ]
}

                         ↓

AFTER sql_generator
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", ...],
  "schema": "CREATE TABLE customers (...)",
  "plan": "Step 1: Count from customers table",
  "sql": "SELECT COUNT(*) FROM customers",  ← NEW
  "validated_sql": "",
  "execution": {},
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: [...]",
    "[Planning] Planning SQL strategy: ...",
    "[SQL Generation] Generated SQL: SELECT COUNT(*) FROM customers"  ← NEW
  ]
}

                         ↓

AFTER sql_validator
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", ...],
  "schema": "CREATE TABLE customers (...)",
  "plan": "Step 1: Count from customers table",
  "sql": "SELECT COUNT(*) FROM customers",
  "validated_sql": "SELECT COUNT(*) FROM customers",  ← NEW
  "execution": {},
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: [...]",
    "[Planning] Planning SQL strategy: ...",
    "[SQL Generation] Generated SQL: ...",
    "[SQL Validation] SQL validation successful"  ← NEW
  ]
}

                         ↓

AFTER executor
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", ...],
  "schema": "CREATE TABLE customers (...)",
  "plan": "Step 1: Count from customers table",
  "sql": "SELECT COUNT(*) FROM customers",
  "validated_sql": "SELECT COUNT(*) FROM customers",
  "execution": {  ← NEW
    "success": true,
    "rows": [{"count": 122}],
    "columns": ["count"],
    "row_count": 1,
    "error": null
  },
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: [...]",
    "[Planning] Planning SQL strategy: ...",
    "[SQL Generation] Generated SQL: ...",
    "[SQL Validation] SQL validation successful",
    "[Execution] Query executed successfully"  ← NEW
  ]
}

                         ↓

[should_retry] checks: execution.success = true
Decision: END (no retry needed)

                         ↓

FINAL STATE (sent to API response)
════════════════════════════════════════════════════════════════
{
  "question": "How many customers?",
  "tables": ["customers", ...],
  "schema": "CREATE TABLE customers (...)",
  "plan": "Step 1: Count from customers table",
  "sql": "SELECT COUNT(*) FROM customers",
  "validated_sql": "SELECT COUNT(*) FROM customers",
  "execution": {
    "success": true,
    "rows": [{"count": 122}],
    "columns": ["count"],
    "row_count": 1,
    "error": null
  },
  "retries": 0,
  "max_retries": 3,
  "trace": [
    "[Schema Discovery] Found tables: [...]",
    "[Planning] Planning SQL strategy: ...",
    "[SQL Generation] Generated SQL: ...",
    "[SQL Validation] SQL validation successful",
    "[Execution] Query executed successfully"
  ]
}

LangSmith Captures:
═════════════════════════════════════════════════════════════════
✓ Every state mutation
✓ Every variable change
✓ Input/output of each node
✓ Timing of each step
✓ Tool calls and results
✓ LLM calls and costs
✓ Retry decisions
✓ Final outcome
```

This is the **complete visibility** you get with LangSmith! 🎯
