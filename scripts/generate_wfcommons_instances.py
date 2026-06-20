"""生成 WfCommons 工作流实例的命令行入口。

本脚本只负责解析命令行参数并调用 `wfcommons_generator` 包中的核心逻辑。
如果需要修改默认生成参数，优先查看 `parse_args()` 中的参数配置。
"""

from __future__ import annotations

import argparse

from wfcommons_generator import (
    DEFAULT_INSTANCES_PER_SIZE,
    DEFAULT_SIZES,
    WORKFLOW_MIN_TASKS,
    WORKFLOW_RECIPES,
    generate_wfcommons_instances,
)


def parse_args() -> argparse.Namespace:
    """定义并解析生成实例所需的命令行参数。"""

    parser = argparse.ArgumentParser(
        description="Generate WfCommons WfFormat JSON instances.",
        epilog=f"Minimum requested sizes by recipe: {minimum_size_summary()}",
    )
    parser.add_argument(
        "--output-dir",
        default="data/wfcommons",
        help="生成结果根目录，默认按 workflow_type/requested_size 分层写入 data/wfcommons。",
    )
    parser.add_argument(
        "--workflow-types",
        nargs="+",
        default=list(WORKFLOW_RECIPES),
        choices=sorted(WORKFLOW_RECIPES),
        help="要生成的工作流类型，可一次传入多个；默认生成全部支持类型。",
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=DEFAULT_SIZES,
        help=(
            "请求任务规模列表；可传任意大于等于对应 recipe 最低下限的整数。"
            f"默认 {DEFAULT_SIZES}。"
        ),
    )
    parser.add_argument(
        "--instances-per-size",
        type=int,
        default=DEFAULT_INSTANCES_PER_SIZE,
        help="每个 workflow type 和 requested size 组合生成多少个实例。",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=20260516,
        help="随机种子基准值；相同参数和 seed-base 会生成可复现的实例。",
    )
    parser.add_argument(
        "--exclude-graphs",
        nargs="*",
        default=None,
        help="传递给 WfCommons 的基础图排除列表；通常无需设置。",
    )
    parser.add_argument(
        "--runtime-factor",
        type=float,
        default=1.0,
        help="WfCommons runtime 缩放因子，必须大于 0，默认 1.0。",
    )
    parser.add_argument(
        "--input-file-size-factor",
        type=float,
        default=1.0,
        help="WfCommons 输入文件大小缩放因子，必须大于 0，默认 1.0。",
    )
    parser.add_argument(
        "--output-file-size-factor",
        type=float,
        default=1.0,
        help="WfCommons 输出文件大小缩放因子，必须大于 0，默认 1.0。",
    )
    return parser.parse_args()


def main() -> None:
    """命令行主流程：解析参数、生成实例、打印每个文件的元数据。"""

    args = parse_args()
    try:
        for generated in generate_wfcommons_instances(
            output_dir=args.output_dir,
            workflow_types=args.workflow_types,
            sizes=args.sizes,
            instances_per_size=args.instances_per_size,
            seed_base=args.seed_base,
            exclude_graphs=args.exclude_graphs,
            runtime_factor=args.runtime_factor,
            input_file_size_factor=args.input_file_size_factor,
            output_file_size_factor=args.output_file_size_factor,
        ):
            # 打印 requested_tasks 和 actual_tasks，方便观察 WfCommons 是否调整了任务数。
            print(
                f"Generated {generated.path} "
                f"(type={generated.workflow_type}, "
                f"requested_tasks={generated.requested_tasks}, "
                f"actual_tasks={generated.actual_tasks}, "
                f"instance_id={generated.instance_id}, "
                f"seed={generated.seed})"
            )
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc


def minimum_size_summary() -> str:
    """返回 CLI 帮助或外部调用可复用的 recipe 最低规模摘要。"""

    return ", ".join(
        f"{workflow_type}>={min_tasks}"
        for workflow_type, min_tasks in sorted(WORKFLOW_MIN_TASKS.items())
    )


if __name__ == "__main__":
    main()
