"""WfCommons 工作流实例生成核心模块。

本模块只放稳定、可复用的生成逻辑，不处理命令行参数解析。
外部脚本或其他 Python 代码可以直接调用 `generate_wfcommons_instances`
批量生成 WfFormat JSON 文件。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import re
from typing import Iterator

import numpy as np
from wfcommons import (
    CyclesRecipe,
    EpigenomicsRecipe,
    GenomeRecipe,
    MontageRecipe,
    SeismologyRecipe,
    SoykbRecipe,
    SrasearchRecipe,
    WorkflowGenerator,
)


# WfCommons recipe 名称到 recipe 类的映射。
# 新增工作流类型时，优先在这里扩展，命令行入口会自动读取该列表。
WORKFLOW_RECIPES = {
    "montage": MontageRecipe,
    "epigenomics": EpigenomicsRecipe,
    "seismology": SeismologyRecipe,
    "genome": GenomeRecipe,
    "cycles": CyclesRecipe,
    "soykb": SoykbRecipe,
    "srasearch": SrasearchRecipe,
}

# 各 recipe 的最低请求任务数。该值来自当前项目依赖的 WfCommons 1.4 recipe
# 基础图限制；请求规模低于下限时 WfCommons 无法按该规模生成有效 synthetic graph。
WORKFLOW_MIN_TASKS = {
    "montage": 60,
    "epigenomics": 43,
    "seismology": 103,
    "genome": 54,
    "cycles": 69,
    "soykb": 98,
    "srasearch": 24,
}

# 默认请求任务规模。这里选择所有支持 recipe 都可生成的建议规模；
# 100 也是常用建议规模，但低于 seismology 的 103 下限，默认批量生成时不启用。
DEFAULT_SIZES = [300, 500, 1000]

# 默认每个 workflow type 和 requested size 组合生成 5 个实例。
DEFAULT_INSTANCES_PER_SIZE = 5


@dataclass(frozen=True)
class GeneratedWorkflow:
    """单个已生成工作流实例的元数据。

    Attributes:
        workflow_type: WfCommons recipe 类型，例如 montage 或 genome。
        requested_tasks: 用户请求的任务规模。
        actual_tasks: WfCommons 实际生成的任务数量。
        instance_id: 同一 workflow type 和 size 下的实例序号。
        seed: 当前实例使用的确定性随机种子。
        path: JSON 文件写入路径。
    """

    workflow_type: str
    requested_tasks: int
    actual_tasks: int
    instance_id: int
    seed: int
    path: Path


def generate_wfcommons_instances(
    output_dir: str | Path = "data/wfcommons",
    workflow_types: list[str] | tuple[str, ...] | None = None,
    sizes: list[int] | tuple[int, ...] | None = None,
    instances_per_size: int = DEFAULT_INSTANCES_PER_SIZE,
    seed_base: int = 20260516,
    exclude_graphs: set[str] | list[str] | tuple[str, ...] | None = None,
    runtime_factor: float = 1.0,
    input_file_size_factor: float = 1.0,
    output_file_size_factor: float = 1.0,
) -> Iterator[GeneratedWorkflow]:
    """批量生成 WfCommons WfFormat JSON 文件，并逐个返回生成元数据。

    Args:
        output_dir: 生成结果根目录。默认是 `data/wfcommons`。
        workflow_types: 要生成的工作流类型列表。为 None 时生成全部支持类型。
        sizes: 请求任务规模列表。为 None 时使用 `DEFAULT_SIZES`。
        instances_per_size: 每个 workflow type 和 requested size 组合生成的实例数。
        seed_base: 随机种子基准值。实际 seed 会结合 workflow type、size、
            instance id 计算，保证同一组参数可复现。
        exclude_graphs: 传递给 WfCommons 的基础图排除列表。通常无需设置。
        runtime_factor: WfCommons runtime 缩放因子，用于整体放大或缩小运行时间。
        input_file_size_factor: WfCommons 输入文件大小缩放因子。
        output_file_size_factor: WfCommons 输出文件大小缩放因子。

    Yields:
        GeneratedWorkflow: 每个生成完成的 JSON 文件对应的元数据。

    Raises:
        ValueError: 参数不合法，例如实例数小于等于 0、任务规模低于 recipe
            最低下限、缩放因子小于等于 0，或 workflow type 不在支持列表中。
    """

    if instances_per_size <= 0:
        raise ValueError("instances_per_size must be greater than 0")
    _validate_positive_factor("runtime_factor", runtime_factor)
    _validate_positive_factor("input_file_size_factor", input_file_size_factor)
    _validate_positive_factor("output_file_size_factor", output_file_size_factor)

    # None 表示使用默认配置；传入空列表也会回退到默认值，避免误生成空数据集。
    workflow_types = list(workflow_types or WORKFLOW_RECIPES)
    sizes = list(sizes or DEFAULT_SIZES)
    output_root = Path(output_dir)
    excluded_graphs = set(exclude_graphs or [])

    for workflow_type in workflow_types:
        # 在进入 WfCommons 前先校验类型，错误信息更直接，也便于 CLI 使用者定位问题。
        if workflow_type not in WORKFLOW_RECIPES:
            supported = ", ".join(sorted(WORKFLOW_RECIPES))
            raise ValueError(f"Unsupported workflow type: {workflow_type}. Supported: {supported}")

        recipe_class = WORKFLOW_RECIPES[workflow_type]
        min_tasks = WORKFLOW_MIN_TASKS[workflow_type]
        for size in sizes:
            # WfCommons 的 from_num_tasks 需要不低于 recipe 基础图规模的正整数。
            if size < min_tasks:
                raise ValueError(
                    f"Requested size {size} is below the minimum for {workflow_type}: "
                    f"{min_tasks} tasks"
                )

            for instance_id in range(instances_per_size):
                # 同时设置 Python random 和 NumPy random，覆盖 WfCommons 内部可能使用的
                # 两类随机源，保证相同参数尽量复现相同实例。
                seed = seed_for_instance(seed_base, workflow_type, size, instance_id)
                random.seed(seed)
                np.random.seed(seed % (2**32 - 1))

                # 文件名中保留 requested size 和 instance id，便于实验批量管理。
                workflow_name = f"{workflow_type}_{size}_{instance_id:03d}"
                workflow = build_wfcommons_workflow(
                    recipe_class=recipe_class,
                    requested_size=size,
                    workflow_name=workflow_name,
                    exclude_graphs=excluded_graphs,
                    runtime_factor=runtime_factor,
                    input_file_size_factor=input_file_size_factor,
                    output_file_size_factor=output_file_size_factor,
                )

                # 输出路径按 workflow type / requested size 分层，避免单目录文件过多。
                target_dir = output_root / workflow_type / str(size)
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / f"{workflow_name}.json"
                workflow.write_json(target_path)

                yield GeneratedWorkflow(
                    workflow_type=workflow_type,
                    requested_tasks=size,
                    actual_tasks=workflow.number_of_nodes(),
                    instance_id=instance_id,
                    seed=seed,
                    path=target_path,
                )


def build_wfcommons_workflow(
    recipe_class,
    requested_size: int,
    workflow_name: str,
    exclude_graphs: set[str] | None = None,
    runtime_factor: float = 1.0,
    input_file_size_factor: float = 1.0,
    output_file_size_factor: float = 1.0,
):
    """构建单个 WfCommons workflow。

    这里直接使用 WfCommons 官方的 `from_num_tasks` 入口，并透传官方支持的
    图排除、runtime 缩放和文件大小缩放参数。低于基础图下限的请求不会被自动
    放大重试，而是抛出错误，避免出现“请求规模”和“实际生成规模”含义不一致。
    """

    try:
        recipe = recipe_class.from_num_tasks(
            num_tasks=requested_size,
            exclude_graphs=set(exclude_graphs or []),
            runtime_factor=runtime_factor,
            input_file_size_factor=input_file_size_factor,
            output_file_size_factor=output_file_size_factor,
        )
        return WorkflowGenerator(recipe).build_workflow(workflow_name)
    except ValueError as exc:
        # 如果 exclude_graphs 改变了可选基础图集合，WfCommons 可能报告比静态下限
        # 更大的基础图规模。这里改善错误信息，但不替用户改变请求规模。
        base_graph_size = _base_graph_size_from_error(str(exc))
        if base_graph_size is not None and base_graph_size > requested_size:
            raise ValueError(
                f"Requested size {requested_size} is below the selected WfCommons "
                f"base graph size: {base_graph_size} tasks"
            ) from exc
        raise


def seed_for_instance(seed_base: int, workflow_type: str, size: int, instance_id: int) -> int:
    """根据生成参数计算确定性随机种子。

    seed 由四部分组成：
    - seed_base: 用户可配置的基准种子。
    - workflow_type offset: 根据工作流名称计算的稳定偏移。
    - size * 1000: 不同请求规模之间拉开距离。
    - instance_id: 同一规模下的多个实例依次变化。
    """

    # 不使用 Python 内置 hash，因为它默认带进程随机化，不适合复现实验数据。
    stable_offset = sum((index + 1) * ord(char) for index, char in enumerate(workflow_type))
    return seed_base + stable_offset + size * 1000 + instance_id


def _base_graph_size_from_error(message: str) -> int | None:
    """从 WfCommons 错误信息中提取 recipe 基础图节点数。"""

    match = re.search(r"base graph with (\d+) nodes", message)
    if not match:
        return None
    return int(match.group(1))


def _validate_positive_factor(name: str, value: float) -> None:
    """校验 WfCommons 缩放因子，避免传入无意义的非正数。"""

    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")
