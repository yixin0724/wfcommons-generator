"""wfcommons-generator 的公共 Python API。

该包入口集中导出外部最常用的常量、数据结构和生成函数。
调用方通常只需要从 `wfcommons_generator` 导入，而不必关心内部模块拆分。
"""

from .core import (
    DEFAULT_INSTANCES_PER_SIZE,
    DEFAULT_SIZES,
    WORKFLOW_MIN_TASKS,
    WORKFLOW_RECIPES,
    GeneratedWorkflow,
    generate_wfcommons_instances,
    seed_for_instance,
)

__all__ = [
    "DEFAULT_INSTANCES_PER_SIZE",
    "DEFAULT_SIZES",
    "WORKFLOW_MIN_TASKS",
    "WORKFLOW_RECIPES",
    "GeneratedWorkflow",
    "generate_wfcommons_instances",
    "seed_for_instance",
]
