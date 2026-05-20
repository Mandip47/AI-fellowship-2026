# Quick Start Guide - LangGraph SQL Agent

## 1. Setup (5 minutes)

### Prerequisites

- Python 3.9+
- PostgreSQL running with `classicmodels` database
- OpenRouter API key (free: https://openrouter.ai/)

### Install

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# - PostgreSQL connection details
# - OpenRouter API key
```

## 2. Run (30 seconds)

```bash
# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run tests
python test_agent.py
```

API will be available at: `http://localhost:8000`

Swagger docs: `http://localhost:8000/docs`

## 3. Test

### Option A: Automated Test Suite

```bash
python test_agent.py
```

Runs 5 predefined questions and shows results + trace.

### Option B: cURL

```bash
curl -X POST http://localhost:8000/agent/sql \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are in USA?"}'
```

### Option C: Swagger UI

Go to `http://localhost:8000/docs` and try it from the browser.

## 4. Understanding the Trace

Every response includes a `trace` array showing every step:

```json
{
  "trace": [
    "[Schema Discovery] Found tables: ['customers', 'orders', ...]",
    "[Planning] Strategy created: Join customers with orders...",
    "[SQL Generation] Generated SQL: SELECT...",
    "[SQL Validation] Validated SQL: SELECT...",
    "[Execution] Query executed. Success: true",
    "[Execution] Returned 42 rows"
  ]
}
```

This is your window into how the agent thinks.

## 5. Key Differences from Original Mini Agent

| Aspect               | Original                                                 | LangGraph                                                |
| -------------------- | -------------------------------------------------------- | -------------------------------------------------------- |
| **Architecture**     | Linear steps (decompose → generate → validate → execute) | StateGraph with Think-Plan-Act-Execute                   |
| **Schema**           | Hardcoded in prompts                                     | Discovered at runtime from database                      |
| **Retry Loop**       | Simple: try fixing SQL on error                          | Sophisticated: conditional routing with feedback context |
| **State Management** | Passed between function calls                            | Centralized AgentState (TypedDict)                       |
| **Tool Access**      | Database calls in executor                               | Three explicit tools for schema discovery                |
| **Graph Topology**   | Implicit in code flow                                    | Explicit StateGraph with nodes + edges                   |
| **Observability**    | Logs only                                                | Full trace + detailed execution state                    |

## 6. Example Walkthrough

### Question

"What are the top 3 most expensive products?"

### Automatic Workflow

1. **[THINK]** schema_discovery
   - Tool: list_tables() → finds all tables
   - Tool: get_schema(tables) → reads column definitions
   - Result: Agent knows exact schema without hardcoding

2. **[PLAN]** planning
   - LLM creates step-by-step strategy
   - Result: "Join products, get MSRP, sort DESC, LIMIT 3"

3. **[ACT]** sql_generation
   - LLM generates SQL based on plan
   - Result: "SELECT productCode, productName, MSRP FROM products ORDER BY MSRP DESC LIMIT 3"

4. **[ACT]** sql_validation
   - LLM validates column names, syntax, joins
   - Result: SQL is correct ✓

5. **[EXECUTE]** execution
   - Tool: run_query(sql) → executes against PostgreSQL
   - Result: Returns 3 rows with product data

6. **Router** should_retry()
   - Check: success == True?
   - Decision: Done! End workflow

### Response

```json
{
  "question": "What are the top 3 most expensive products?",
  "sql": "SELECT productCode, productName, MSRP FROM products ORDER BY MSRP DESC LIMIT 3",
  "result": [
    {"productCode": "S10_1678", "productName": "1969 Harley Davidson Ultimate Chopper", "MSRP": 95.70},
    {"productCode": "S10_2016", "productName": "1996 Moto Guzzi 1100i", "MSRP": 68.99},
    {"productCode": "S10_4962", "productName": "1962 LanciaA Appia", "MSRP": 61.46}
  ],
  "status": "success",
  "retries": 0,
  "trace": [...]
}
```

## 7. Self-Correction Example

### Question

"Show me customers who spent over 100000"

### First Attempt (If schema had typo)

```
Generated: SELECT * FROM customers WHERE lifetime_spent > 100000
Error: column "lifetime_spent" does not exist
```

### Retry Logic Kicks In

1. should_retry() sees error + retries (0 < 3) → return "retry"
2. increment_retry increments counter, feeds corrected SQL back
3. sql_validator called AGAIN with error context
4. Validator reads error, sees schema, fixes to correct column

### Second Attempt

```
Fixed: SELECT * FROM orders o JOIN customers c WHERE SUM(amount) > 100000
Result: Success! ✓
```

This happens automatically - no human intervention needed.

## 8. Architecture Files

```
app/
├── graph/
│   ├── __init__.py          # AgentState definition
│   └── workflow.py          # StateGraph + compile
├── agents/
│   ├── schema_discoverer.py # [THINK] node
│   ├── planner.py           # [PLAN] node
│   ├── sql_generator.py     # [ACT] generation
│   ├── sql_validator.py     # [ACT] validation
│   ├── executor.py          # [EXECUTE] node
│   └── retry_handler.py     # [RECOVER] node
├── tools/
│   └── __init__.py          # list_tables, get_schema, run_query
├── main.py                  # FastAPI app
└── logger.py                # Logging setup
```

For detailed architecture docs, see: `ARCHITECTURE.md`

## 9. Troubleshooting

### "OPENROUTER_API_KEY is not configured"

- Check .env file has OPENROUTER_API_KEY
- Ensure you copied .env.example to .env
- Restart API after changing .env

### "Could not connect to PostgreSQL"

- Verify Docker container is running: `docker-compose up -d` (from parent directory)
- Check POSTGRES\_\* env vars match container settings
- Test: `psql -h localhost -p 5433 -U postgres -d classicmodels`

### "column X does not exist"

- This is expected behavior
- Agent will self-correct on retry
- Check trace to see what error was and how it was fixed

### Slow Response Times

- First run may be slow (LLM cold start)
- Typical: 10-20 seconds per query
- Check trace for where time is spent (schema discovery, planning, etc.)

## 10. Next Steps

1. **Understand the architecture**
   - Read `ARCHITECTURE.md` for deep dive
   - Study `app/graph/workflow.py` to see StateGraph structure

2. **Experiment with questions**
   - Try complex joins: "customers who bought specific products"
   - Try aggregations: "total revenue by product line"
   - Try filters: "orders from specific countries"

3. **Extend the system**
   - Add new tools (e.g., table statistics, query suggestions)
   - Add new nodes (e.g., result formatting, natural language summaries)
   - Customize retry logic (e.g., different retry count per question type)

4. **Deploy**
   - Switch to production ASAP settings in main.py
   - Add authentication (FastAPI security)
   - Add rate limiting
   - Add database connection pooling

## 11. Key Concepts

- **StateGraph**: Container for multi-node workflows
- **AgentState**: Shared state (TypedDict) - whiteboard for all nodes
- **Node**: Pure function that reads/mutates state
- **Edge**: Control flow between nodes
- **Conditional Edge**: Dynamic routing based on state (enables retry loop)
- **Tool**: How agent interacts with world (DB, APIs, etc.)
- **Trace**: Observable log of every decision

For a full explanation of why this is agentic (not just prompt chaining), see: `README.md`
