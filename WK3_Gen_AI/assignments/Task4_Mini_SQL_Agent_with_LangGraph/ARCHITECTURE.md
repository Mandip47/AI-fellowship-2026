# Agentic AI Architecture: Theory to Implementation

This document maps the theoretical concepts from the briefing document directly to the working code.

## 1. What Is an Agent? (Principles)

An AI agent is a system that:

1. **Perceives** its environment (reads database schema)
2. **Reasons** about what to do (creates plan)
3. **Acts** using tools (generates and executes SQL)
4. **Observes** results (captures query outcome)
5. **Self-corrects** without human intervention (retry loop)

### Our System's Agent Properties

| Property            | Implementation                                              |
| ------------------- | ----------------------------------------------------------- |
| **Autonomy**        | `schema_discovery_node` discovers tables without hardcoding |
| **Tool Use**        | Three tools: `list_tables()`, `get_schema()`, `run_query()` |
| **Self-Correction** | `should_retry()` + `increment_retry_node` + retry loop      |

---

## 2. Prompt Chaining vs Agentic (Comparison)

### Prompt Chaining Example (What NOT to do)

```python
# Fixed, linear, developer-hardcoded sequence
schema_hardcoded = "customers(id, name), orders(id, customer_id, total)"
response1 = llm("Summarize schema: " + schema_hardcoded)
response2 = llm("Write SQL for: " + question + response1)
response3 = llm("Fix this SQL: " + response2)
result = db.run(response3)  # If error → CRASH, no recovery
```

### Agentic LangGraph Example (What We Built)

```python
# Dynamic, agent-decides, self-correcting
result = compiled_graph.invoke({
    "question": question,
    "retries": 0,
    "trace": []
})
# Behind the scenes:
# 1. schema_discovery discovers REAL schema (not hardcoded)
# 2. planner creates strategy
# 3. sql_generator creates SQL
# 4. sql_validator reviews
# 5. executor runs query
# 6. If error: should_retry() DECIDES to retry
# 7. increment_retry loops back to sql_validator
# 8. sql_validator sees error context, FIXES the query
# 9. executor tries again (up to 3 times)
# 10. Returns full trace of every decision
```

---

## 3. Four Pillars of Agentic AI (Mapping to Code)

### Pillar 1: THINK — Schema Discovery

**Concept**: Agent observes environment before acting.

**Code File**: `app/agents/schema_discoverer.py`

```python
def schema_discovery_node(state: AgentState) -> Dict[str, Any]:
    # TOOL 1: Discover all tables
    tables = list_tables()  # Queries information_schema

    # TOOL 2: Get full DDL
    schema = get_schema(tables)  # Retrieves CREATE TABLE statements

    # Append to trace for observability
    trace.append(f"[Schema Discovery] Found tables: {tables}")

    # Return PARTIAL state
    return {**state, "tables": tables, "schema": schema, "trace": trace}
```

**Why It's Agentic**:

- Schema is discovered at RUNTIME, not hardcoded
- Works on ANY PostgreSQL database
- If schema changes, agent discovers new state automatically

---

### Pillar 2: PLAN — SQL Strategy

**Concept**: Before acting, agent reasons about strategy.

**Code File**: `app/agents/planner.py`

```python
def create_plan(question: str, tables: list, schema: str) -> str:
    prompt = f"""Available tables: {', '.join(tables)}

    Schema: {schema}

    Question: {question}

    Create a step-by-step SQL strategy WITHOUT writing SQL.
    For each step: describe joins, filters, aggregations."""

    plan = llm_call(prompt)
    return plan
```

**Output Example**:

```
1. Join customers with orders on customerNumber
2. Filter orders where status = 'Shipped' and country = 'USA'
3. Count the rows
4. Return as single scalar result
```

**Why It's Agentic**:

- Separates reasoning from execution
- Strategy guides SQL generation toward correct query
- Improves accuracy over direct SQL generation

---

### Pillar 3: ACT — SQL Generation & Validation

**Concept**: Agent takes action and validates before committing.

**Code Files**:

- `app/agents/sql_generator.py` (generation)
- `app/agents/sql_validator.py` (validation)

```python
# STEP 1: Generate SQL based on plan
def sql_generation_node(state: AgentState):
    sql = generate_sql(
        question=state['question'],
        schema=state['schema'],
        plan=state['plan']
    )
    return {**state, "sql": sql, "trace": trace}

# STEP 2: Validate before execution
def sql_validation_node(state: AgentState):
    # If retrying, pass error context to validator
    error = state['execution'].get('error') if state['execution'] else None

    validated_sql = validate_sql(
        sql=state['sql'],
        schema=state['schema'],
        error=error  # ← Critical: error context for self-correction
    )
    return {**state, "validated_sql": validated_sql, "trace": trace}
```

**Why It's Agentic**:

- Validation catches errors BEFORE execution (prevents crashes)
- Error context is passed to validator (enables intelligent self-correction)
- Separates concerns: generation vs validation vs execution

---

### Pillar 4: EXECUTE — Query Execution & Self-Correction

**Concept**: Agent executes, observes, and adapts based on results.

**Code Files**:

- `app/agents/executor.py` (execution)
- `app/graph/workflow.py` (retry logic)
- `app/agents/retry_handler.py` (retry counter)

```python
# STEP 1: Execute query
def execution_node(state: AgentState):
    result = run_query(state['validated_sql'])  # ← Tool 3: Real DB

    return {
        **state,
        "execution": {
            "success": result['success'],
            "rows": result['rows'],
            "error": result['error']
        },
        "trace": trace
    }

# STEP 2: Decide: retry or end?
def should_retry(state: AgentState) -> Literal["retry", "done"]:
    if state['execution']['success']:
        return "done"  # ← Success: end workflow

    if state['retries'] < state['max_retries']:
        return "retry"  # ← Failure + retries left: retry

    return "done"  # ← Give up after max retries

# STEP 3: If retrying, increment and loop back
def increment_retry_node(state: AgentState):
    return {
        **state,
        "retries": state['retries'] + 1,
        "sql": state['validated_sql'],  # Feed corrected SQL back
        "trace": trace
    }
```

**Retry Loop Topology** (in workflow.py):

```python
graph.add_edge("execution", "increment_retry")  # if should_retry returns "retry"
graph.add_edge("increment_retry", "sql_validation")  # loops back (KEY!)
```

**Why It's Agentic**:

- Agent OBSERVES result (success or error)
- DECIDES what to do next (end or retry)
- Self-CORRECTS by reading actual DB error and fixing the exact issue
- Repeats up to 3 times automatically

---

## 4. What Is LangGraph? (Architecture)

LangGraph is a graph-based workflow engine. All concepts map directly to code:

| Concept              | What It Is                 | Our Code                                             |
| -------------------- | -------------------------- | ---------------------------------------------------- |
| **StateGraph**       | Container for workflow     | `workflow.py`: `StateGraph(AgentState)`              |
| **AgentState**       | Shared state (TypedDict)   | `app/graph/__init__.py`: `AgentState` class          |
| **Node**             | Unit of work (function)    | Each `*_node` in `agents/` folder                    |
| **Edge**             | Control flow               | `graph.add_edge()` in `workflow.py`                  |
| **Conditional Edge** | Dynamic routing            | `graph.add_conditional_edges()` + `should_retry()`   |
| **END**              | Workflow completion        | `from langgraph.graph import END`                    |
| **compile()**        | Validate and make runnable | `compiled_graph = graph.compile()`                   |
| **invoke()**         | Execute with initial state | `final_state = compiled_graph.invoke(initial_state)` |

### Building the Graph (workflow.py)

```python
from langgraph.graph import StateGraph, END

# 1. Create container
graph = StateGraph(AgentState)

# 2. Add nodes (units of work)
graph.add_node("schema_discovery", schema_discovery_node)
graph.add_node("planning", planning_node)
graph.add_node("sql_generation", sql_generation_node)
graph.add_node("sql_validation", sql_validation_node)
graph.add_node("execution", execution_node)
graph.add_node("increment_retry", increment_retry_node)

# 3. Set entry point
graph.set_entry_point("schema_discovery")

# 4. Add linear edges (deterministic)
graph.add_edge("schema_discovery", "planning")
graph.add_edge("planning", "sql_generation")
graph.add_edge("sql_generation", "sql_validation")
graph.add_edge("sql_validation", "execution")

# 5. Add conditional edge (the retry loop!)
graph.add_conditional_edges(
    "execution",
    should_retry,
    {"retry": "increment_retry", "done": END}
)

# 6. Add loop edge
graph.add_edge("increment_retry", "sql_validation")

# 7. Compile
compiled_graph = graph.compile()
```

---

## 5. AgentState — Shared Brain

**File**: `app/graph/__init__.py`

```python
class AgentState(TypedDict, total=False):
    # Input
    question: str

    # [THINK]
    tables: List[str]
    schema: str

    # [PLAN]
    plan: str

    # [ACT]
    sql: str
    validated_sql: str

    # [EXECUTE]
    execution: Dict[str, Any]

    # [RECOVER]
    retries: int
    max_retries: int

    # Observability
    trace: List[str]
```

**Pattern**: Every node reads/writes to AgentState, never directly to other nodes.

```python
def my_node(state: AgentState) -> Dict[str, Any]:
    # 1. Read
    input_val = state.get("input_field", "")

    # 2. Process
    output_val = process(input_val)

    # 3. Write PARTIAL dict
    return {
        **state,  # Preserve all fields
        "output_field": output_val,  # New/updated field
        "trace": trace  # Always update trace
    }
```

LangGraph automatically merges PARTIAL dicts into full state.

---

## 6. Nodes — Pure Functions

Each node is a pure function with single responsibility:

| Node               | File                   | Responsibility                   |
| ------------------ | ---------------------- | -------------------------------- |
| `schema_discovery` | `schema_discoverer.py` | [THINK] Discover tables & schema |
| `planning`         | `planner.py`           | [PLAN] Create SQL strategy       |
| `sql_generation`   | `sql_generator.py`     | [ACT] Generate SQL               |
| `sql_validation`   | `sql_validator.py`     | [ACT] Validate SQL & fix errors  |
| `execution`        | `executor.py`          | [EXECUTE] Run query              |
| `increment_retry`  | `retry_handler.py`     | [RECOVER] Increment counter      |

**Node Implementation Pattern**:

```python
def node_name(state: AgentState) -> Dict[str, Any]:
    trace = state.get("trace", [])

    try:
        # Do work
        result = some_work(state)
        trace.append(f"[Step] Success: {result}")
        return {**state, "field": result, "trace": trace}

    except Exception as e:
        trace.append(f"[Step] Error: {e}")
        return {**state, "trace": trace}
```

---

## 7. Tools — How Agent Interacts with World

**File**: `app/tools/__init__.py`

Three tools give agent autonomous access to PostgreSQL:

### Tool 1: list_tables()

```python
def list_tables() -> List[str]:
    """Discover all tables in database."""
    # Query information_schema
    return ["customers", "orders", "products", ...]
```

**Used by**: `schema_discovery_node`

### Tool 2: get_schema(table_names)

```python
def get_schema(table_names: List[str]) -> str:
    """Get full DDL with column info and foreign keys."""
    return """CREATE TABLE customers (
      customerNumber INT NOT NULL,
      customerName VARCHAR(50) NOT NULL,
      ...
      FOREIGN KEY (salesRepEmployeeNumber) REFERENCES employees(...)
    )"""
```

**Used by**: `schema_discovery_node`

### Tool 3: run_query(sql)

```python
def run_query(query: str) -> Dict[str, Any]:
    """Execute SELECT against real PostgreSQL."""
    return {
        "success": True,
        "rows": [...],
        "error": None
    }
```

**Used by**: `execution_node`

---

## 8. Retry Loop — The Magic (Self-Correction)

This is what makes the system truly agentic:

**Scenario**: User asks "How many customers?" but schema has typo.

### Attempt 1: Generation → Validation → Execution ❌

```
Generated SQL:  SELECT customer_count FROM customers
Error:          column "customer_count" does not exist
```

### Attempt 2: Validation receives ERROR context → Fixes ✓

```python
# In sql_validation_node:
previous_error = state['execution'].get('error')  # ← ERROR CONTEXT!

validated_sql = validate_sql(
    sql=state['sql'],
    schema=state['schema'],
    error=previous_error  # ← Passed to LLM
)

# LLM sees:
# - Original SQL: SELECT customer_count FROM customers
# - Error: column "customer_count" does not exist
# - Schema shows: "customerNumber" and "customerName" are valid columns
# - Fixes to: SELECT COUNT(*) FROM customers
```

### Attempt 3: Execution ✓

```
Fixed SQL:  SELECT COUNT(*) FROM customers
Result:     42
Success!
```

**Code Flow**:

```python
# workflow.py
def should_retry(state) -> Literal["retry", "done"]:
    if not state['execution']['success'] and state['retries'] < 3:
        return "retry"  # Loop back
    return "done"  # Exit

# increment_retry feeds corrected SQL back:
return {
    **state,
    "sql": state['validated_sql'],  # ← KEY: corrected SQL goes back
    "retries": state['retries'] + 1
}

# sql_validation_node gets called AGAIN with:
# - error context from previous execution
# - corrected SQL from increment_retry
# - Full schema for reference
```

---

## 9. Full System Walkthrough Example

**User Question**: "Show me the top 3 customers by total spent"

### Node 1: schema_discovery

```
Input state:  {question: "Show me the top 3 customers by total spent"}
Action:       list_tables() → ["customers", "orders", "payments", ...]
              get_schema(tables) → Full DDL
Output state: {question: "...", tables: [...], schema: "...", trace: ["[Schema Discovery] Found tables: [...]"]}
```

### Node 2: planning

```
Input:  {question, tables, schema}
Action: "Given question + tables + schema, create step-by-step strategy"
        LLM returns: "1. Join customers with payments. 2. SUM(amount) per customer. 3. Order by sum DESC. 4. LIMIT 3"
Output: {plan: "1. Join...", trace: [...]}
```

### Node 3: sql_generation

```
Input:  {question, schema, plan}
Action: "Given plan, generate PostgreSQL SELECT"
        LLM returns: "SELECT c.customerName, SUM(p.amount) as total FROM customers c JOIN payments p ON..."
Output: {sql: "SELECT...", trace: [...]}
```

### Node 4: sql_validation

```
Input:  {sql, schema}
Action: "Validate column names, join conditions, syntax"
        LLM returns: "SELECT c.customerName, SUM(p.amount) as total FROM customers c JOIN payments p ON..."
Output: {validated_sql: "SELECT...", trace: [...]}
```

### Node 5: execution

```
Input:  {validated_sql}
Action: run_query() → PostgreSQL executes
Result: {"success": True, "rows": [{"customerName": "Alpha", "total": 5000}, ...], "error": None}
Output: {execution: {...success: True...}, trace: [...]}
```

### Node 6: should_retry router

```
Check: execution['success'] == True?
Answer: YES
Decision: Return "done" → go to END
```

### END

```
Return final state to API
API responds with:
{
  "sql": "SELECT c.customerName, SUM(p.amount) as total FROM customers c...",
  "result": [{"customerName": "Alpha", "total": 5000}, ...],
  "status": "success",
  "retries": 0,
  "trace": ["[Schema Discovery]...", "[Planning]...", ...]
}
```

---

## 10. Why This Architecture Wins

| Criterion            | Prompt Chain        | LangGraph Agent         |
| -------------------- | ------------------- | ----------------------- |
| **Reliability**      | Crashes on error    | Retries + self-corrects |
| **Adaptability**     | Schema-dependent    | Schema-independent      |
| **Observability**    | Black box           | Full trace              |
| **Error Recovery**   | Manual intervention | Automatic               |
| **Code Reusability** | Monolithic          | Modular nodes           |
| **Extensibility**    | Rewrite chain       | Add node + edge         |

---

## 11. Implementation Checklist

✅ **StateGraph + AgentState**

- `app/graph/__init__.py`: AgentState TypedDict defined
- `app/graph/workflow.py`: StateGraph created with 6 nodes

✅ **Nodes (Pure Functions)**

- `schema_discoverer.py`: [THINK] node
- `planner.py`: [PLAN] node
- `sql_generator.py`: [ACT] generation
- `sql_validator.py`: [ACT] validation
- `executor.py`: [EXECUTE] node
- `retry_handler.py`: [RECOVER] node

✅ **Tools**

- `app/tools/__init__.py`: list_tables(), get_schema(), run_query()

✅ **Control Flow**

- Linear edges: discovery → planning → generation → validation → execution
- Conditional edge: execution → should_retry() → {retry: increment_retry, done: END}
- Loop edge: increment_retry → validation (self-correction)

✅ **FastAPI Integration**

- `app/main.py`: FastAPI app, POST /agent/sql endpoint, invoke compiled graph

✅ **Observability**

- Trace list appended to by every node
- Full trace included in API response

---

## References

- **LangGraph**: Graph-based workflow engine for AI applications
- **StateGraph**: Container for multi-node workflows with typed state
- **Conditional Edges**: Enable dynamic routing and loops
- **Retry Pattern**: Self-correction mechanism core to agentic behavior
- **Tool Calling**: How agents interact with external systems (DB, APIs, etc.)
