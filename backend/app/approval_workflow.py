from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ReviewState(TypedDict, total=False):
    plan_id: str
    tasks: list[dict]
    status: str


def prepare_review(state: ReviewState) -> dict:
    return {"status": "awaiting_approval"}


def request_decision(state: ReviewState) -> dict:
    decision = interrupt(
        {
            "plan_id": state["plan_id"],
            "tasks": state["tasks"],
            "allowed_decisions": ["approve", "reject"],
        }
    )

    if decision not in ("approve", "reject"):
        raise ValueError("Invalid approval decision")

    return {
        "status": "approved" if decision == "approve" else "rejected"
    }


def build_review_graph(checkpointer):
    builder = StateGraph(ReviewState)

    builder.add_node("prepare_review", prepare_review)
    builder.add_node("request_decision", request_decision)

    builder.add_edge(START, "prepare_review")
    builder.add_edge("prepare_review", "request_decision")
    builder.add_edge("request_decision", END)

    return builder.compile(checkpointer=checkpointer)