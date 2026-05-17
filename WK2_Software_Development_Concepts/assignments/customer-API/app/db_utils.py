from sqlalchemy.exc import IntegrityError


def integrity_message(exc: IntegrityError) -> str:
    orig = getattr(exc, "orig", None)
    return str(orig) if orig else str(exc)


def customer_integrity_detail(msg: str) -> str:
    """Map Postgres / SQLAlchemy integrity text to a clearer customer API message."""
    lower = msg.lower()
    if "duplicate key" in lower or "unique constraint" in lower:
        return (
            "This customerNumber already exists. Use a different customerNumber, "
            "or update the existing customer instead."
        )
    if "foreign key" in lower and (
        "salesrep" in lower
        or "sales_rep" in lower
        or "employeenumber" in lower
        or 'table "employees"' in lower
    ):
        return (
            "salesRepEmployeeNumber must match an existing employees.employeeNumber. "
            "Create the employee (and their office) first, or omit / set salesRepEmployeeNumber to null."
        )
    if "foreign key" in lower:
        return "Could not save customer: a foreign key reference is invalid."
    return "Could not save customer: invalid reference or duplicate key."
