import argparse
import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.checkpoints import get_checkpointer


class ApprovalState(TypedDict, total=False):
    tasks: list[str]
    status: str


def prepare_review(state: ApprovalState) -> dict:
    return {"status": "awaiting_approval"}


def review_plan(state: ApprovalState) -> dict:
    decision = interrupt(
        {
            "question": "Approve this demonstration plan?",
            "tasks": state["tasks"],
            "allowed_decisions": ["approve", "reject"],
        }
    )

    if decision not in ("approve", "reject"):
        raise ValueError("Decision must be approve or reject")

    return {
        "status": "approved" if decision == "approve" else "rejected"
    }


def build_approval_graph(checkpointer):
    builder = StateGraph(ApprovalState)

    builder.add_node("prepare_review", prepare_review)
    builder.add_node("review_plan", review_plan)

    builder.add_edge(START, "prepare_review")
    builder.add_edge("prepare_review", "review_plan")
    builder.add_edge("review_plan", END)

    return builder.compile(checkpointer=checkpointer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["start", "show", "approve", "reject"],
    )
    parser.add_argument("run_id")
    args = parser.parse_args()

    config = {
        "configurable": {
            "thread_id": f"approval-demo:{args.run_id}"
        }
    }

    with get_checkpointer() as checkpointer:
        graph = build_approval_graph(checkpointer)
        snapshot = graph.get_state(config)

        if args.action == "start":
            if snapshot.values:
                raise SystemExit(
                    "This run already exists. Use show, approve, or reject."
                )

            graph.invoke(
                {"tasks": ["Prepare a laptop for Maya Example"]},
                config=config,
            )

        elif args.action in ("approve", "reject"):
            if not snapshot.values:
                raise SystemExit("Run not found. Start it first.")

            if not snapshot.interrupts:
                raise SystemExit("This run is not waiting for approval.")

            graph.invoke(
                Command(resume=args.action),
                config=config,
            )

        elif not snapshot.values:
            raise SystemExit("Run not found.")

        snapshot = graph.get_state(config)

        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "state": snapshot.values,
                    "waiting_for_approval": bool(snapshot.interrupts),
                    "review": [
                        item.value for item in snapshot.interrupts
                    ],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()