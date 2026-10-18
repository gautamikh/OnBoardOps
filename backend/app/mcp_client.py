import asyncio
import logging
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel, ConfigDict, Field


logger = logging.getLogger("uvicorn.error")


class MCPUnavailable(Exception):
    pass


class EmployeeNotFound(Exception):
    pass


class EmployeeRecord(BaseModel):
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    employee_id: str = Field(pattern=r"^EMP-\d{3}$")
    name: str = Field(min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=80)
    location: str = Field(min_length=1, max_length=80)
    manager: str = Field(min_length=1)


class LookupResult(BaseModel):
    model_config = ConfigDict(strict=True)

    found: bool
    employee: EmployeeRecord | None = None


async def lookup_employee(employee_id: str) -> EmployeeRecord:
    try:
        url = os.environ["MCP_SERVER_URL"]

        async with asyncio.timeout(15):
            async with streamable_http_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        "lookup_employee",
                        arguments={"employee_id": employee_id},
                    )

                    if result.isError:
                        raise ValueError("Employee lookup tool failed")

                    lookup = LookupResult.model_validate(
                        result.structuredContent
                    )

                    if lookup.found != (lookup.employee is not None):
                        raise ValueError("Inconsistent employee lookup result")

                    if (
                        lookup.employee is not None
                        and lookup.employee.employee_id != employee_id
                    ):
                        raise ValueError("Employee ID mismatch")

    except Exception as exc:
        logger.warning("MCP lookup failed: %s", type(exc).__name__)
        raise MCPUnavailable("Employee directory unavailable") from exc

    if lookup.employee is None:
        raise EmployeeNotFound(employee_id)

    return lookup.employee