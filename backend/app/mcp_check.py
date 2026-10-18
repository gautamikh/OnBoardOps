import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


async def check_connection():
    url = os.environ["MCP_SERVER_URL"]

    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            available = await session.list_tools()
            tool_names = [tool.name for tool in available.tools]

            print("Available tools:", tool_names)
            require(
                "lookup_employee" in tool_names,
                "Employee lookup tool was not discovered",
            )

            known = await session.call_tool(
                "lookup_employee",
                arguments={"employee_id": "EMP-001"},
            )
            require(not known.isError, "Known employee lookup failed")

            data = known.structuredContent
            require(
                isinstance(data, dict) and data.get("found") is True,
                "Expected a matching employee",
            )
            require(
                data["employee"]["employee_id"] == "EMP-001",
                "Returned the wrong employee",
            )
            print(json.dumps(data, indent=2))

            unknown = await session.call_tool(
                "lookup_employee",
                arguments={"employee_id": "EMP-999"},
            )
            require(not unknown.isError, "Unknown lookup failed unexpectedly")
            require(
                unknown.structuredContent == {
                    "found": False,
                    "employee": None,
                },
                "Expected an explicit not-found result",
            )
            print("Unknown employee check: passed")

            invalid = await session.call_tool(
                "lookup_employee",
                arguments={"employee_id": "invalid"},
            )
            require(
                invalid.isError,
                "Invalid employee ID should produce a tool error",
            )
            print("Invalid input check: passed")

            print("MCP connection checks passed.")


async def main():
    async with asyncio.timeout(30):
        await check_connection()


if __name__ == "__main__":
    asyncio.run(main())