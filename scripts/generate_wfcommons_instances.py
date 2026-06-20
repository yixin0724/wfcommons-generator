from __future__ import annotations

import argparse

from wfcommons_generator import (
    DEFAULT_INSTANCES_PER_SIZE,
    DEFAULT_SIZES,
    WORKFLOW_RECIPES,
    generate_wfcommons_instances,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate WfCommons WfFormat JSON instances.")
    parser.add_argument("--output-dir", default="data/wfcommons")
    parser.add_argument("--workflow-types", nargs="+", default=list(WORKFLOW_RECIPES))
    parser.add_argument("--sizes", nargs="+", type=int, default=DEFAULT_SIZES)
    parser.add_argument("--instances-per-size", type=int, default=DEFAULT_INSTANCES_PER_SIZE)
    parser.add_argument("--seed-base", type=int, default=20260516)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for generated in generate_wfcommons_instances(
        output_dir=args.output_dir,
        workflow_types=args.workflow_types,
        sizes=args.sizes,
        instances_per_size=args.instances_per_size,
        seed_base=args.seed_base,
    ):
        print(
            f"Generated {generated.path} "
            f"(type={generated.workflow_type}, "
            f"requested_tasks={generated.requested_tasks}, "
            f"actual_tasks={generated.actual_tasks}, "
            f"instance_id={generated.instance_id}, "
            f"seed={generated.seed})"
        )


if __name__ == "__main__":
    main()
