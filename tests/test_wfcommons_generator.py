"""wfcommons-generator 核心行为测试。

测试重点放在生成器对外承诺的稳定行为上：随机种子可复现、
非法参数会被拒绝、最小生成流程可成功落盘，以及支持的 workflow
类型列表保持显式可控。
"""

from pathlib import Path

import pytest

from wfcommons_generator import (
    WORKFLOW_MIN_TASKS,
    WORKFLOW_RECIPES,
    generate_wfcommons_instances,
    seed_for_instance,
)


def test_seed_for_instance_is_stable() -> None:
    """相同输入参数必须得到稳定 seed，避免实验结果不可复现。"""

    assert seed_for_instance(20260516, "montage", 100, 0) == 20363451
    assert seed_for_instance(20260516, "montage", 100, 1) == 20363452


def test_rejects_unsupported_workflow_type(tmp_path: Path) -> None:
    """不支持的 workflow type 应该在进入 WfCommons 前被明确拒绝。"""

    with pytest.raises(ValueError, match="Unsupported workflow type"):
        list(
            generate_wfcommons_instances(
                output_dir=tmp_path,
                workflow_types=["unknown"],
                sizes=[100],
                instances_per_size=1,
            )
        )


def test_generate_one_wfcommons_json(tmp_path: Path) -> None:
    """验证最小生成流程：生成一个 JSON 文件并返回正确元数据。"""

    generated = list(
        generate_wfcommons_instances(
            output_dir=tmp_path,
            workflow_types=["montage"],
            sizes=[100],
            instances_per_size=1,
            seed_base=20260516,
        )
    )

    assert len(generated) == 1
    item = generated[0]
    assert item.workflow_type == "montage"
    assert item.requested_tasks == 100
    assert item.actual_tasks > 0
    assert item.path == tmp_path / "montage" / "100" / "montage_100_000.json"
    assert item.path.exists()
    assert item.path.read_text(encoding="utf-8").startswith("{")


def test_rejects_size_below_recipe_minimum(tmp_path: Path) -> None:
    """低于 recipe 基础图下限的规模应被拒绝，而不是自动放大生成。"""

    with pytest.raises(ValueError, match="below the minimum for seismology"):
        list(
            generate_wfcommons_instances(
                output_dir=tmp_path,
                workflow_types=["seismology"],
                sizes=[100],
                instances_per_size=1,
            )
        )


def test_supports_wfcommons_scaling_parameters(tmp_path: Path) -> None:
    """官方 runtime 和文件大小缩放参数应能透传给 WfCommons。"""

    generated = list(
        generate_wfcommons_instances(
            output_dir=tmp_path,
            workflow_types=["srasearch"],
            sizes=[50],
            instances_per_size=1,
            runtime_factor=1.2,
            input_file_size_factor=1.1,
            output_file_size_factor=0.9,
        )
    )

    assert len(generated) == 1
    assert generated[0].path.exists()


def test_supported_workflow_types_are_explicit() -> None:
    """支持类型列表应该显式维护，避免依赖 WfCommons 内部默认行为。"""

    assert set(WORKFLOW_RECIPES) == {
        "cycles",
        "epigenomics",
        "genome",
        "montage",
        "seismology",
        "soykb",
        "srasearch",
    }


def test_supported_workflow_minimums_are_explicit() -> None:
    """每个支持的 workflow type 都应该有对应的最低规模配置。"""

    assert WORKFLOW_MIN_TASKS == {
        "cycles": 69,
        "epigenomics": 43,
        "genome": 54,
        "montage": 60,
        "seismology": 103,
        "soykb": 98,
        "srasearch": 24,
    }
