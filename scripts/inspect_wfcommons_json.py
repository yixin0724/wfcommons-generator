"""检查单个 WfCommons WfFormat JSON 文件的命令行入口。

该脚本用于快速确认生成文件的基本结构，包括任务数、依赖边数、
文件数、execution task 数量，以及部分任务和边的样例。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """定义并解析 JSON 检查命令的参数。"""

    parser = argparse.ArgumentParser(description="Inspect one WfCommons WfFormat JSON file.")
    parser.add_argument(
        "--workflow-json",
        required=True,
        help="需要检查的 WfCommons WfFormat JSON 文件路径。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="最多打印多少个任务 id 和依赖边样例。",
    )
    return parser.parse_args()


def main() -> None:
    """读取 JSON 文件并打印常用结构统计信息。"""

    args = parse_args()
    path = Path(args.workflow_json)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # WfFormat 的主要信息位于 workflow.specification 和 workflow.execution 下。
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
    """从 task 的 parents 和 children 字段中提取去重后的依赖边。"""

    edges: set[tuple[str, str]] = set()
    for task in tasks:
        task_id = str(task.get("id", ""))
        # WfCommons JSON 中同一条边可能同时出现在 parent 和 child 方向。
        # 使用 set 可以自然去重，避免统计边数时重复计算。
        for parent_id in task.get("parents", []):
            edges.add((str(parent_id), task_id))
        for child_id in task.get("children", []):
            edges.add((task_id, str(child_id)))
    return edges


if __name__ == "__main__":
    main()
