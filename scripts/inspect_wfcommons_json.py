from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect one WfCommons WfFormat JSON file.")
    parser.add_argument("--workflow-json", required=True)
    parser.add_argument("--limit", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.workflow_json)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    workflow = data.get("workflow", {})
    specification = workflow.get("specification", {})
    execution = workflow.get("execution", {})
    tasks = specification.get("tasks", [])
    files = specification.get("files", [])
    execution_tasks = execution.get("tasks", [])
    edges = _edges(tasks)

    print(f"workflow: {path}")
    print(f"tasks: {len(tasks)}")
    print(f"edges: {len(edges)}")
    print(f"files: {len(files)}")
    print(f"execution tasks: {len(execution_tasks)}")
    print(f"first {args.limit} task ids:")
    for task_id in [str(task.get("id", "")) for task in tasks[: args.limit]]:
        print(f"- {task_id}")
    print(f"first {args.limit} edges:")
    for parent_id, child_id in sorted(edges)[: args.limit]:
        print(f"- {parent_id} -> {child_id}")


def _edges(tasks: list[dict]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for task in tasks:
        task_id = str(task.get("id", ""))
        for parent_id in task.get("parents", []):
            edges.add((str(parent_id), task_id))
        for child_id in task.get("children", []):
            edges.add((task_id, str(child_id)))
    return edges


if __name__ == "__main__":
    main()
