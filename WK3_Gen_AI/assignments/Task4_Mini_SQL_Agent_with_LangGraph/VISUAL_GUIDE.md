# LangGraph SQL Agent - Visual Guide

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH WORKFLOW                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    USER QUESTION                            │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│                    AgentState (TypedDict)                        │
│                    Shared Brain for all nodes                    │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐ │
│  │ [THINK] schema_discovery_node                              │ │
│  │ ├─ Tool 1: list_tables()   → discovers tables             │ │
│  │ ├─ Tool 2: get_schema()    → retrieves DDL                │ │
│  │ └─ Output: tables[], schema str                           │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐ │
│  │ [PLAN] planning_node                                        │ │
│  │ ├─ LLM: create_plan()                                      │ │
│  │ ├─ Input: question, tables, schema                         │ │
│  │ └─ Output: step-by-step strategy                           │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐ │
│  │ [ACT] sql_generation_node                                   │ │
│  │ ├─ LLM: generate_sql()                                     │ │
│  │ ├─ Input: question, schema, plan                           │ │
│  │ └─ Output: raw SQL                                         │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐ │
│  │ [ACT] sql_validation_node                                   │ │
│  │ ├─ LLM: validate_sql()                                     │ │
│  │ ├─ Input: sql, schema, (error if retrying)               │ │
│  │ └─ Output: validated/corrected SQL                         │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐ │
│  │ [EXECUTE] execution_node                                    │ │
│  │ ├─ Tool 3: run_query()  → executes against PostgreSQL     │ │
│  │ ├─ Output: {success, rows, error}                          │ │
│  └────────────────────────┬────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────────────────────┐ │
│  │ Conditional Router: should_retry()                               │ │
│  │                                                                   │ │
│  │  IF execution['success'] == True  THEN return "done" → END       │ │
│  │  ELSE IF retries < max_retries    THEN return "retry"            │ │
│  │  ELSE                             THEN return "done" → END       │ │
│  └────┬──────────────────────────────────────────────────────┬──────┘ │
│       │ (retry)                                    (success) │        │
│  ┌────▼──────────────────────────────────────────────────────▼──────┐ │
│  │                              OR                                   │ │
│  │ [RECOVER] increment_retry_node                              END  │ │
│  │ ├─ retries += 1                                                  │ │
│  │ ├─ sql ← validated_sql  (feed corrected SQL back)               │ │
│  │ └─ loops to sql_validation                                      │ │
│  └────────────────────────┬──────────────────────────────────────────┘ │
│                           │                                           │
│                    (loops back to validation)                         │
│                                                                      │
│  ┌────────────────────────▼──────────────────────────────────────────┐ │
│  │ FINAL STATE                                                        │ │
│  │ {question, sql, execution, result, trace[], retries}             │ │
│  └────────────────────────┬──────────────────────────────────────────┘ │
│                           │                                            │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   API Response │
                    └────────────────┘
```

---

## State Flow Through Nodes

```
Initial State:
{
  question: "How many customers are in USA?",
  tables: [],
  schema: "",
  plan: "",
  sql: "",
  validated_sql: "",
  execution: {success: false, rows: [], error: null},
  retries: 0,
  max_retries: 3,
  trace: []
}
        ↓
    schema_discovery
        ↓
{
  question: "...",
  tables: ["customers", "orders", ...],        ← Added
  schema: "CREATE TABLE customers(...)",        ← Added
  plan: "",
  sql: "",
  validated_sql: "",
  execution: {...},
  retries: 0,
  max_retries: 3,
  trace: ["[Schema Discovery] Found tables: [...]"]  ← Added
}
        ↓
     planning
        ↓
{
  question: "...",
  tables: [...],
  schema: "...",
  plan: "1. Query customers table 2. Filter by country",  ← Added
  sql: "",
  validated_sql: "",
  execution: {...},
  retries: 0,
  max_retries: 3,
  trace: [..., "[Planning] Strategy created: ..."]  ← Added
}
        ↓
   sql_generation
        ↓
{
  question: "...",
  tables: [...],
  schema: "...",
  plan: "...",
  sql: "SELECT COUNT(*) FROM customers WHERE country = 'USA'",  ← Added
  validated_sql: "",
  execution: {...},
  retries: 0,
  max_retries: 3,
  trace: [..., "[SQL Generation] Generated SQL: ..."]
}
        ↓
   sql_validation
        ↓
{
  question: "...",
  tables: [...],
  schema: "...",
  plan: "...",
  sql: "SELECT COUNT(*) FROM customers WHERE country = 'USA'",
  validated_sql: "SELECT COUNT(*) FROM customers WHERE country = 'USA'",  ← Added
  execution: {...},
  retries: 0,
  max_retries: 3,
  trace: [..., "[SQL Validation] Validated SQL: ..."]
}
        ↓
    execution
        ↓
{
  question: "...",
  tables: [...],
  schema: "...",
  plan: "...",
  sql: "SELECT COUNT(*) FROM customers WHERE country = 'USA'",
  validated_sql: "SELECT COUNT(*) FROM customers WHERE country = 'USA'",
  execution: {success: true, rows: [{"COUNT(*)": 97}], error: null},  ← Updated
  retries: 0,
  max_retries: 3,
  trace: [..., "[Execution] Query executed. Success: true"]
}
        ↓
  should_retry router → "done" (success)
        ↓
      END
        ↓
   Return final state to API
```

---

## Retry Loop Example

```
Initial Attempt (with typo in schema knowledge):

    sql_generation
        ↓
    SQL: "SELECT COUNT(*) FROM customers WHERE total_spent > 100000"
        ↓
    sql_validation (LLM reviews)
        ↓
    SQL looks okay syntactically
        ↓
    execution
        ↓
    PostgreSQL Error: column "total_spent" does not exist
        ↓
    execution: {success: false, error: "column 'total_spent' does not exist"}
        ↓
    should_retry() → "retry" (retries=0 < max=3)
        ↓
    increment_retry_node
    - retries: 0 → 1
    - sql ← validated_sql (gets the last SQL)
    - trace appended
        ↓
    back to sql_validation (LOOP!)
        ↓
    sql_validation (CALLED AGAIN)
    - Previous error context: "column 'total_spent' does not exist"
    - Schema shows: available columns are "customerName", "amount", etc.
    - LLM reads error + schema
    - FIXES: "SELECT COUNT(*) FROM customers c JOIN payments p ON c.customerNumber = p.customerNumber WHERE SUM(p.amount) > 100000"
        ↓
    execution
        ↓
    PostgreSQL runs corrected SQL successfully
        ↓
    execution: {success: true, rows: [...], error: null}
        ↓
    should_retry() → "done" (success)
        ↓
    END

Final State:
{
  sql: "SELECT COUNT(*) FROM ... WHERE SUM(p.amount) > 100000",
  result: [...],
  retries: 1,  ← One retry was made
  trace: [
    "[SQL Generation] Generated SQL: SELECT COUNT(*) FROM customers WHERE total_spent > 100000",
    "[SQL Validation] Validated SQL: SELECT COUNT(*) FROM customers WHERE total_spent > 100000",
    "[Execution] Query executed. Success: false",
    "[Execution] Error: column 'total_spent' does not exist",
    "[Retry Loop] Attempt 1 - feeding validated SQL back to validator",
    "[SQL Validation] Validated SQL: SELECT COUNT(*) FROM customers c JOIN payments p ... WHERE SUM(p.amount) > 100000",
    "[Execution] Query executed. Success: true",
    "[Execution] Returned 12 rows"
  ]
}
```

---

## Node Independence

```
┌─────────────────────────────────────────────┐
│         schema_discovery_node               │
├─────────────────────────────────────────────┤
│ Input State:                                │
│   - question                                │
│                                             │
│ Reads Tools:                                │
│   - list_tables()                           │
│   - get_schema()                            │
│                                             │
│ Output State:                               │
│   + tables                                  │
│   + schema                                  │
│   + trace (appended)                        │
├─────────────────────────────────────────────┤
│ Can be tested independently:                │
│   schema_discovery_node({question: "..."})  │
│   → {tables: [...], schema: "..."}          │
│                                             │
│ Can be replaced:                            │
│   Swap list_tables() with different tool    │
│   No changes to other nodes                 │
│                                             │
│ Can be extended:                            │
│   Add new output fields                     │
│   Add new tools                             │
└─────────────────────────────────────────────┘
```

---

## Graph Topology Visualization

```
           START
             │
             ▼
    ┌────────────────┐
    │ Schema         │
    │ Discovery      │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ Planning       │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ SQL            │
    │ Generation     │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ SQL            │
    │ Validation     │◄──────┐
    └────────┬───────┘       │
             │               │
             ▼               │
    ┌────────────────┐       │
    │ Execution      │       │
    └────────┬───────┘       │
             │               │
             ▼               │
    ┌─────────────────────┐  │
    │ should_retry()      │  │
    │ (router function)   │  │
    └────┬────────┬───────┘  │
         │        │          │
      success  retry & retry<3
         │        │          │
         │        ▼          │
         │    ┌──────────────┐
         │    │ Increment    │
         │    │ Retry        │
         │    └──────────────┘
         │              │
         │              └──────┘
         │
         ▼
       END/RETURN
```

---

## File Relationships

```
main.py (FastAPI)
    │
    ├─ imports: compile_graph()
    │   │
    │   └─ app/graph/workflow.py
    │       ├─ defines: StateGraph, nodes, edges
    │       └─ imports all node functions:
    │           ├─ app/agents/schema_discoverer.py
    │           ├─ app/agents/planner.py
    │           ├─ app/agents/sql_generator.py
    │           ├─ app/agents/sql_validator.py
    │           ├─ app/agents/executor.py
    │           └─ app/agents/retry_handler.py
    │
    ├─ imports: AgentState
    │   └─ app/graph/__init__.py (TypedDict definition)
    │
    └─ each agent node imports:
        └─ app/tools/__init__.py
            ├─ list_tables()
            ├─ get_schema()
            └─ run_query()
```

---

## Think-Plan-Act-Execute Mapping

```
User: "What are the top 5 products by revenue?"

┌─────────────┐
│   [THINK]   │  schema_discovery_node
├─────────────┤
│ Observe     │  ← Discovers: tables, columns, FK relationships
│ Environment │     No guessing, query real database
│             │     Agent knows EXACTLY what data exists
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   [PLAN]    │  planning_node
├─────────────┤
│ Reason      │  ← Creates strategy: which joins, filters, aggregations?
│ Strategy    │     Plans BEFORE acting
│             │     Guides SQL generation toward correct query
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    [ACT]    │  sql_generation_node + sql_validation_node
├─────────────┤
│ Generate    │  ← Generates SQL based on plan
│ & Validate  │     Validates BEFORE execution
│             │     Catches syntax errors, missing columns early
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  [EXECUTE]  │  execution_node
├─────────────┤
│ Run Action  │  ← Executes real SQL against real database
│ & Observe   │     Reads actual results OR actual errors
│             │     No assumptions, real feedback
└──────┬──────┘
       │
       ├─ Success? → END ✓
       │
       └─ Error? & retries < 3?
           │
           ├─ YES → increment_retry_node + loop back
           │        ├─ Error gets fed to sql_validation
           │        ├─ Validator READS error + schema
           │        ├─ Validator FIXES the exact issue
           │        └─ Retry execution
           │
           └─ NO (max retries) → END with error ✗
```

---

## Execution Trace Example

```json
{
  "trace": [
    "[Schema Discovery] Found tables: ['customers', 'orders', 'orderdetails', 'products', 'productlines', 'payments', 'employees', 'offices']",
    "[Schema Discovery] Retrieved schema for 8 tables",
    "[Planning] Strategy created: 1. Join products with orderdetails. 2. SUM(quantityOrdered * priceEach) per product. 3. Sort DESC. 4. LIMIT 5",
    "[SQL Generation] Generated SQL: SELECT p.productCode, p.productName, SUM(od.quantityOrdered * od.priceEach) as revenue FROM products p JOIN orderdetails od ON p.productCode = od.productCode GROUP BY p.productCode, p.productName ORDER BY revenue DESC LIMIT 5",
    "[SQL Validation] Validated SQL: SELECT p.productCode, p.productName, SUM(od.quantityOrdered * od.priceEach) as revenue FROM products p JOIN orderdetails od ON p.productCode = od.productCode GROUP BY p.productCode, p.productName ORDER BY revenue DESC LIMIT 5",
    "[Execution] Query executed. Success: true",
    "[Execution] Returned 5 rows"
  ]
}
```

Each trace entry shows:

- What step was executed
- What decision was made
- What inputs/outputs occurred
- Complete visibility into agent reasoning

---

## Key Differences: LangGraph vs Prompt Chaining

```
PROMPT CHAINING:
┌─────────────────────────────────────────────┐
│ Fixed Sequence                              │
├─────────────────────────────────────────────┤
│ LLM Call 1 → Result 1                       │
│ LLM Call 2 → Result 2 (uses Result 1)       │
│ LLM Call 3 → Result 3 (uses Result 2)       │
│ Execute SQL                                 │
│ IF error → crash OR human intervention      │
└─────────────────────────────────────────────┘

LANGGRAPH (AGENTIC):
┌─────────────────────────────────────────────┐
│ Dynamic Graph with Tools                    │
├─────────────────────────────────────────────┤
│ [THINK] Discover environment (tools)        │
│ [PLAN] Reason about strategy (LLM)          │
│ [ACT] Generate and validate (LLM)           │
│ [EXECUTE] Run and observe (tools)           │
│ IF error AND retries < max:                 │
│   [RECOVER] Loop back with error context    │
│   [ACT] Fix and retry automatically         │
│ ELSE: Done                                  │
└─────────────────────────────────────────────┘
```

The key difference: **Self-correction without human intervention**
