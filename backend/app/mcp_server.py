from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field


mcp = FastMCP(
    "OnboardOps Tools",
    host="0.0.0.0",
    port=8001,
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "mcp-tools:8001",
            "localhost:8001",
            "127.0.0.1:8001",
        ],
    ),
)


class Employee(BaseModel):
    employee_id: str
    name: str
    department: str
    location: str
    manager: str


class EmployeeLookupResult(BaseModel):
    found: bool
    employee: Employee | None = None


EMPLOYEES = {
    "EMP-001": Employee(
        employee_id="EMP-001",
        name="Maya Example",
        department="Engineering",
        location="Berlin",
        manager="Sam Example",
    ),
    "EMP-002": Employee(
        employee_id="EMP-002",
        name="Alex Example",
        department="People",
        location="Munich",
        manager="Taylor Example",
    ),
}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def lookup_employee(
    employee_id: Annotated[
        str,
        Field(pattern=r"^EMP-\d{3}$"),
    ],
) -> EmployeeLookupResult:
    """Look up a fictional employee by ID, for example EMP-001."""
    employee = EMPLOYEES.get(employee_id)

    return EmployeeLookupResult(
        found=employee is not None,
        employee=employee,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")