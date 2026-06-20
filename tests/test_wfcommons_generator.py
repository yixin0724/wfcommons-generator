from pathlib import Path

import pytest

from wfcommons_generator import (
    WORKFLOW_RECIPES,
    generate_wfcommons_instances,
    seed_for_instance,
)


def test_seed_for_instance_is_stable() -> None:
    assert seed_for_instance(20260516, "montage", 100, 0) == 20363451
    assert seed_for_instance(20260516, "montage", 100, 1) == 20363452


def test_rejects_unsupported_workflow_type(tmp_path: Path) -> None:
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


def test_supported_workflow_types_are_explicit() -> None:
    assert set(WORKFLOW_RECIPES) == {"montage", "epigenomics", "seismology", "genome"}
