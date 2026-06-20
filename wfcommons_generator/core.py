from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import re
from typing import Iterator

import numpy as np
from wfcommons import (
    EpigenomicsRecipe,
    GenomeRecipe,
    MontageRecipe,
    SeismologyRecipe,
    WorkflowGenerator,
)


WORKFLOW_RECIPES = {
    "montage": MontageRecipe,
    "epigenomics": EpigenomicsRecipe,
    "seismology": SeismologyRecipe,
    "genome": GenomeRecipe,
}
DEFAULT_SIZES = [100, 300, 500, 1000]
DEFAULT_INSTANCES_PER_SIZE = 5


@dataclass(frozen=True)
class GeneratedWorkflow:
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
) -> Iterator[GeneratedWorkflow]:
    """Generate WfCommons WfFormat JSON files and yield their metadata."""

    if instances_per_size <= 0:
        raise ValueError("instances_per_size must be greater than 0")

    workflow_types = list(workflow_types or WORKFLOW_RECIPES)
    sizes = list(sizes or DEFAULT_SIZES)
    output_root = Path(output_dir)

    for workflow_type in workflow_types:
        if workflow_type not in WORKFLOW_RECIPES:
            supported = ", ".join(sorted(WORKFLOW_RECIPES))
            raise ValueError(f"Unsupported workflow type: {workflow_type}. Supported: {supported}")

        recipe_class = WORKFLOW_RECIPES[workflow_type]
        for size in sizes:
            if size <= 0:
                raise ValueError("sizes must contain positive integers")

            for instance_id in range(instances_per_size):
                seed = seed_for_instance(seed_base, workflow_type, size, instance_id)
                random.seed(seed)
                np.random.seed(seed % (2**32 - 1))

                workflow_name = f"{workflow_type}_{size}_{instance_id:03d}"
                workflow = build_wfcommons_workflow(recipe_class, size, workflow_name)

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


def build_wfcommons_workflow(recipe_class, requested_size: int, workflow_name: str):
    """Build one WfCommons workflow, retrying when a recipe has a larger base graph."""

    try:
        recipe = recipe_class.from_num_tasks(requested_size)
        return WorkflowGenerator(recipe).build_workflow(workflow_name)
    except ValueError as exc:
        fallback_size = _base_graph_size_from_error(str(exc))
        if fallback_size is None or fallback_size <= requested_size:
            raise
        recipe = recipe_class.from_num_tasks(fallback_size)
        return WorkflowGenerator(recipe).build_workflow(workflow_name)


def seed_for_instance(seed_base: int, workflow_type: str, size: int, instance_id: int) -> int:
    stable_offset = sum((index + 1) * ord(char) for index, char in enumerate(workflow_type))
    return seed_base + stable_offset + size * 1000 + instance_id


def _base_graph_size_from_error(message: str) -> int | None:
    match = re.search(r"base graph with (\d+) nodes", message)
    if not match:
        return None
    return int(match.group(1))
