"""
Task 2 – Query Understanding / Decomposition
============================================
Uses OpenRouter (free model) to break a natural‑language question into
structured components that map directly to the WK2 Customer‑API database.

Database schema (derived from WK2 customer-API pydantic schemas)
----------------------------------------------------------------
Table            | Key Columns
-----------------|--------------------------------------------------------------
customers        | customerNumber (PK), customerName, contactLastName,
                 | contactFirstName, phone, addressLine1, addressLine2,
                 | city, state, postalCode, country,
                 | salesRepEmployeeNumber (FK→employees), creditLimit
orders           | orderNumber (PK), orderDate, requiredDate, shippedDate,
                 | status, comments, customerNumber (FK→customers)
orderdetails     | orderNumber (FK→orders), productCode (FK→products),
                 | quantityOrdered, priceEach, orderLineNumber
products         | productCode (PK), productName, productLine (FK→productlines),
                 | productScale, productVendor, productDescription,
                 | quantityInStock, buyPrice, MSRP
productlines     | productLine (PK), textDescription, htmlDescription, image
payments         | customerNumber (FK→customers), checkNumber (PK part),
                 | paymentDate, amount
employees        | employeeNumber (PK), lastName, firstName, extension, email,
                 | officeCode (FK→offices), reportsTo (FK→employees), jobTitle
offices          | officeCode (PK), city, phone, addressLine1, addressLine2,
                 | state, country, postalCode, territory
"""

import json
import os

import requests
from dotenv import load_dotenv

# ── env ───────────────────────────────────────────────────────────────────────
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError(
        "OPENROUTER_API_KEY not found. " "Add it to the .env file in this directory."
    )

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/auto"  # OpenRouter picks the best free model automatically

# ── system prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are an expert SQL analyst assistant specialising in the Classic Models
e-commerce database. Your job is to decompose a natural-language question
into a structured analysis that a downstream SQL-generation layer can use
directly — no SQL is written here, only analysis.

## Database Schema

### customers
| Column                  | Type    | Notes                          |
|-------------------------|---------|--------------------------------|
| customerNumber          | INT     | PRIMARY KEY                    |
| customerName            | VARCHAR |                                |
| contactLastName         | VARCHAR |                                |
| contactFirstName        | VARCHAR |                                |
| phone                   | VARCHAR |                                |
| addressLine1            | VARCHAR |                                |
| addressLine2            | VARCHAR | nullable                       |
| city                    | VARCHAR |                                |
| state                   | VARCHAR | nullable                       |
| postalCode              | VARCHAR |                                |
| country                 | VARCHAR |                                |
| salesRepEmployeeNumber  | INT     | FK → employees.employeeNumber  |
| creditLimit             | DECIMAL | nullable                       |

### orders
| Column         | Type    | Notes                           |
|----------------|---------|---------------------------------|
| orderNumber    | INT     | PRIMARY KEY                     |
| orderDate      | DATE    |                                 |
| requiredDate   | DATE    |                                 |
| shippedDate    | DATE    | nullable                        |
| status         | VARCHAR | Shipped/Resolved/Cancelled/...  |
| comments       | TEXT    | nullable                        |
| customerNumber | INT     | FK → customers.customerNumber   |

### orderdetails
| Column          | Type    | Notes                        |
|-----------------|---------|------------------------------|
| orderNumber     | INT     | FK → orders.orderNumber      |
| productCode     | VARCHAR | FK → products.productCode    |
| quantityOrdered | INT     |                              |
| priceEach       | DECIMAL |                              |
| orderLineNumber | INT     |                              |

### products
| Column             | Type    | Notes                             |
|--------------------|---------|-----------------------------------|
| productCode        | VARCHAR | PRIMARY KEY                       |
| productName        | VARCHAR |                                   |
| productLine        | VARCHAR | FK → productlines.productLine     |
| productScale       | VARCHAR |                                   |
| productVendor      | VARCHAR |                                   |
| productDescription | TEXT    |                                   |
| quantityInStock    | INT     |                                   |
| buyPrice           | DECIMAL |                                   |
| MSRP               | DECIMAL |                                   |

### productlines
| Column          | Type    | Notes       |
|-----------------|---------|-------------|
| productLine     | VARCHAR | PRIMARY KEY |
| textDescription | TEXT    | nullable    |
| htmlDescription | TEXT    | nullable    |

### payments
| Column         | Type    | Notes                          |
|----------------|---------|--------------------------------|
| customerNumber | INT     | FK → customers.customerNumber  |
| checkNumber    | VARCHAR | part of composite PK           |
| paymentDate    | DATE    |                                |
| amount         | DECIMAL |                                |

### employees
| Column               | Type    | Notes                          |
|----------------------|---------|--------------------------------|
| employeeNumber       | INT     | PRIMARY KEY                    |
| lastName             | VARCHAR |                                |
| firstName            | VARCHAR |                                |
| extension            | VARCHAR |                                |
| email                | VARCHAR |                                |
| officeCode           | VARCHAR | FK → offices.officeCode        |
| reportsTo            | INT     | FK → employees.employeeNumber  |
| jobTitle             | VARCHAR |                                |

### offices
| Column       | Type    | Notes       |
|--------------|---------|-------------|
| officeCode   | VARCHAR | PRIMARY KEY |
| city         | VARCHAR |             |
| phone        | VARCHAR |             |
| addressLine1 | VARCHAR |             |
| addressLine2 | VARCHAR | nullable    |
| state        | VARCHAR | nullable    |
| country      | VARCHAR |             |
| postalCode   | VARCHAR |             |
| territory    | VARCHAR |             |

## Relationship Map (for JOIN guidance)
customers  ──< orders          (customers.customerNumber = orders.customerNumber)
orders     ──< orderdetails    (orders.orderNumber = orderdetails.orderNumber)
products   ──< orderdetails    (products.productCode = orderdetails.productCode)
productlines ──< products      (productlines.productLine = products.productLine)
customers  ──< payments        (customers.customerNumber = payments.customerNumber)
employees  ──< customers       (employees.employeeNumber = customers.salesRepEmployeeNumber)
offices    ──< employees       (offices.officeCode = employees.officeCode)
employees  ──< employees       (self-join: employees.reportsTo = employees.employeeNumber)

## Output Rules
- ALWAYS respond with valid JSON — no markdown fences, no extra text.
- Use EXACTLY the following top-level keys:
  "question", "intent", "tables", "columns", "filters", "joins", "aggregations", "notes"
- "tables"      → array of table name strings
- "columns"     → object  { "<table>": ["col1", "col2", ...] }
- "filters"     → array of condition strings, e.g. "country = 'USA'"
- "joins"       → array of join strings, e.g. "orders ON customers.customerNumber = orders.customerNumber"
                  or [] if no joins are needed
- "aggregations"→ array of strings, e.g. "COUNT(customerNumber)" or [] if none
- "notes"       → any extra reasoning helpful for the SQL-generation layer

## Example
Input : "How many customers are from the USA?"
Output:
{
  "question": "How many customers are from the USA?",
  "intent": "Count total customers from a specific country",
  "tables": ["customers"],
  "columns": { "customers": ["customerNumber"] },
  "filters": ["country = 'USA'"],
  "joins": [],
  "aggregations": ["COUNT(customerNumber)"],
  "notes": "Simple single-table count with a WHERE filter on country."
}
""".strip()


# ── core function ─────────────────────────────────────────────────────────────
def decompose_query(question: str) -> dict:
    """
    Send a natural-language question to OpenRouter and return a structured
    decomposition as a Python dict.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "response_format": {"type": "json_object"},  # enforce JSON output
        "temperature": 0,  # deterministic results
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw_content = response.json()["choices"][0]["message"]["content"]

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON:\n{raw_content}") from exc


# ── questions ─────────────────────────────────────────────────────────────────
QUESTIONS = [
    # --- provided example ---
    "How many customers are from the USA?",
    # --- additional practice questions ---
    "List all orders that have been shipped but not yet delivered.",
    "Which products have a quantity in stock less than 100?",
    "Find the total amount paid by each customer.",
    "Who are the top 5 customers by total order value?",
    "Which employees report to the employee with employeeNumber 1143?",
    "What is the average credit limit of customers in France?",
    "List all products in the 'Classic Cars' product line along with their MSRP.",
    "How many orders were placed in each month of 2004?",
    "Which office has the most employees?",
]


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Task 2 – Query Decomposition using OpenRouter")
    print("=" * 70)

    results = []

    for idx, question in enumerate(QUESTIONS, start=1):
        print(f"\n[{idx}/{len(QUESTIONS)}] Processing: {question}")
        try:
            decomposition = decompose_query(question)
            results.append(decomposition)
            print(json.dumps(decomposition, indent=2))
        except Exception as exc:
            error_entry = {"question": question, "error": str(exc)}
            results.append(error_entry)
            print(f"  ERROR: {exc}")

    # ── save all results to a JSON file ──────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "decomposition_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"  All results saved to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
