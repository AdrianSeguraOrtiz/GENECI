"""Resource estimation and wave planning helpers."""

from __future__ import annotations

import math
import multiprocessing
from pathlib import Path
from typing import Any, Optional

from .shared import DatasetContext, PlanWave, ToolPlanItem, _load_json_object


def _load_tool_cost_profile(
    *,
    tools_root: Path,
    tool_id: str,
) -> tuple[Optional[dict[str, Any]], list[str]]:
    """Load optional per-tool cost profile from cost.json used for planning."""
    warnings: list[str] = []
    cost_path = tools_root / tool_id / "cost.json"
    if not cost_path.exists():
        warnings.append(
            f"[{tool_id}] no cost.json found in catalog; cost is unknown and fallback estimation will be used."
        )
        return None, warnings
    if not cost_path.is_file():
        warnings.append(
            f"[{tool_id}] cost.json path is not a file and will be ignored: {cost_path}; "
            "fallback estimation will be used."
        )
        return None, warnings

    try:
        return _load_json_object(cost_path, f"cost[{tool_id}]"), warnings
    except ValueError as exc:
        warnings.append(
            f"[{tool_id}] invalid cost.json ignored ({exc}); fallback estimation will be used."
        )
        return None, warnings


def _nearest_runtime_point(
    *,
    points: list[dict[str, Any]],
    genes: int,
    columns: int,
    threads: int,
    ram_gb: float,
) -> Optional[dict[str, Any]]:
    same_resource = [
        p
        for p in points
        if int(p.get("threads", -1)) == int(threads)
        and float(p.get("ram_gb", -1.0)) == float(ram_gb)
    ]
    if not same_resource:
        same_resource = points
    if not same_resource:
        return None

    def score(point: dict[str, Any]) -> float:
        pg = max(1, int(point.get("genes", 1)))
        pc = max(1, int(point.get("columns", 1)))
        # Log-distance is more stable across scale differences.
        return abs(math.log(genes / pg)) + abs(math.log(columns / pc))

    return min(same_resource, key=score)


def _fallback_plan_item(
    *,
    tool_id: str,
    run_id: str,
    image: str,
    dataset: DatasetContext,
    max_cores: int,
    max_ram_gb: float,
    eta_source: str,
    output_dir: str,
    group_label: Optional[str] = None,
) -> ToolPlanItem:
    fallback_eta = max(10.0, 0.02 * dataset.genes * dataset.columns)
    return ToolPlanItem(
        tool_id=tool_id,
        run_id=run_id,
        image=image,
        threads=max(1, min(max_cores, 1)),
        ram_gb=max(1.0, min(max_ram_gb, 4.0)),
        eta_seconds=round(fallback_eta, 3),
        eta_source=eta_source,
        output_dir=output_dir,
        group_label=group_label,
    )


def _mode_risk_penalty(point: dict[str, Any]) -> float:
    repeats_total = int(point.get("repeats_total", 0))
    if repeats_total <= 0:
        return 2.0

    ok_rate_raw = point.get("ok_rate")
    if isinstance(ok_rate_raw, (int, float)):
        ok_rate = min(1.0, max(0.0, float(ok_rate_raw)))
    else:
        repeats_ok = int(point.get("repeats_ok", 0))
        ok_rate = min(1.0, max(0.0, repeats_ok / repeats_total))

    failure_breakdown = point.get("failure_breakdown", {})
    oom = timeout = error = 0
    if isinstance(failure_breakdown, dict):
        oom = int(failure_breakdown.get("oom", 0) or 0)
        timeout = int(failure_breakdown.get("timeout", 0) or 0)
        error = int(failure_breakdown.get("error", 0) or 0)

    fail_rate = 1.0 - ok_rate
    oom_rate = max(0.0, float(oom) / repeats_total)
    timeout_rate = max(0.0, float(timeout) / repeats_total)
    error_rate = max(0.0, float(error) / repeats_total)

    # Conservative risk model: unstable points are penalized to reduce planner optimism.
    penalty = (
        1.0
        + (0.50 * fail_rate)
        + (0.90 * oom_rate)
        + (0.70 * timeout_rate)
        + (0.40 * error_rate)
    )
    return max(1.0, penalty)


def _prune_modes_by_pareto(modes: list[ToolPlanItem]) -> list[ToolPlanItem]:
    if not modes:
        return []
    kept: list[ToolPlanItem] = []
    for mode in sorted(modes, key=lambda x: (x.eta_seconds, x.threads, x.ram_gb)):
        dominated = False
        for other in kept:
            better_or_equal = (
                other.eta_seconds <= mode.eta_seconds
                and other.threads <= mode.threads
                and other.ram_gb <= mode.ram_gb
            )
            strictly_better = (
                other.eta_seconds < mode.eta_seconds
                or other.threads < mode.threads
                or other.ram_gb < mode.ram_gb
            )
            if better_or_equal and strictly_better:
                dominated = True
                break
        if not dominated:
            kept.append(mode)
    return kept


def _estimate_tool_mode_options(
    *,
    tool_id: str,
    run_id: str,
    toolspec: dict[str, Any],
    cost_profile: Optional[dict[str, Any]],
    dataset: DatasetContext,
    max_cores: int,
    max_ram_gb: float,
    output_dir: str,
    group_label: Optional[str] = None,
) -> tuple[list[ToolPlanItem], list[str]]:
    warnings: list[str] = []
    modes: list[ToolPlanItem] = []
    image = str(toolspec.get("docker_image", "")).strip()
    if not image:
        raise ValueError(f"[{tool_id}] toolspec.docker_image is missing")

    cost = cost_profile
    if not isinstance(cost, dict):
        return (
            [
                _fallback_plan_item(
                    tool_id=tool_id,
                    run_id=run_id,
                    image=image,
                    dataset=dataset,
                    max_cores=max_cores,
                    max_ram_gb=max_ram_gb,
                    eta_source="fallback_no_cost",
                    output_dir=output_dir,
                    group_label=group_label,
                )
            ],
            warnings,
        )

    runtime_points = cost.get("runtime_points", [])
    if not isinstance(runtime_points, list):
        runtime_points = []
    valid_points = [
        p
        for p in runtime_points
        if isinstance(p, dict)
        and p.get("status") in {"ok", "partial"}
        and isinstance(p.get("seconds_p50"), (int, float))
        and isinstance(p.get("seconds_p90"), (int, float))
        and isinstance(p.get("threads"), int)
        and isinstance(p.get("ram_gb"), (int, float))
        and int(p.get("threads")) >= 1
        and float(p.get("ram_gb")) > 0
    ]

    candidate_resources = sorted(
        {
            (int(p["threads"]), round(float(p["ram_gb"]), 3))
            for p in valid_points
            if int(p["threads"]) <= max_cores and float(p["ram_gb"]) <= max_ram_gb
        }
    )

    for threads, ram in candidate_resources:
        nearest = _nearest_runtime_point(
            points=valid_points,
            genes=dataset.genes,
            columns=dataset.columns,
            threads=threads,
            ram_gb=ram,
        )
        if nearest is None:
            continue

        p50 = float(nearest["seconds_p50"])
        p90 = float(nearest["seconds_p90"])
        pg = max(1, int(nearest.get("genes", dataset.genes)))
        pc = max(1, int(nearest.get("columns", dataset.columns)))
        size_scale = math.sqrt((dataset.genes / pg) * (dataset.columns / pc))
        robust_base = max(p90, (0.70 * p90 + 0.30 * p50))
        eta = max(0.1, robust_base * size_scale * _mode_risk_penalty(nearest))

        modes.append(
            ToolPlanItem(
                tool_id=tool_id,
                run_id=run_id,
                image=image,
                threads=int(threads),
                ram_gb=round(float(ram), 3),
                eta_seconds=round(float(eta), 3),
                eta_source="cost_runtime_points_robust",
                output_dir=output_dir,
                group_label=group_label,
            )
        )

    if modes:
        pruned = _prune_modes_by_pareto(modes)
        # Keep search tractable while preserving best alternatives.
        return (
            sorted(pruned, key=lambda x: (x.eta_seconds, x.threads, x.ram_gb))[:8],
            warnings,
        )

    warnings.append(
        f"[{tool_id}] cost.json exists but has no usable runtime_points; using fallback estimation."
    )
    return (
        [
            _fallback_plan_item(
                tool_id=tool_id,
                run_id=run_id,
                image=image,
                dataset=dataset,
                max_cores=max_cores,
                max_ram_gb=max_ram_gb,
                eta_source="fallback_invalid_cost",
                output_dir=output_dir,
                group_label=group_label,
            )
        ],
        warnings,
    )


def _build_parallel_waves(
    *,
    items: list[ToolPlanItem],
    max_cores: int,
    max_ram_gb: float,
) -> tuple[list[PlanWave], float]:
    waves: list[PlanWave] = []

    # Longest tasks first + best-fit placement to minimize ETA increase and resource waste.
    sorted_items = sorted(items, key=lambda x: x.eta_seconds, reverse=True)

    for item in sorted_items:
        best_idx: Optional[int] = None
        best_score: Optional[tuple[float, float]] = None
        for idx, wave in enumerate(waves):
            next_cores = wave.threads_used + item.threads
            next_ram = wave.ram_gb_used + item.ram_gb
            if next_cores <= max_cores and next_ram <= max_ram_gb:
                eta_increase = max(0.0, item.eta_seconds - wave.eta_seconds)
                residual_cores = float(max_cores - next_cores)
                residual_ram = float(max_ram_gb - next_ram)
                residual_score = residual_cores + residual_ram
                score = (eta_increase, residual_score)
                if best_score is None or score < best_score:
                    best_score = score
                    best_idx = idx

        if best_idx is not None:
            wave = waves[best_idx]
            next_tasks = wave.tasks + [item]
            waves[best_idx] = PlanWave(
                index=wave.index,
                threads_used=wave.threads_used + item.threads,
                ram_gb_used=round(wave.ram_gb_used + item.ram_gb, 3),
                eta_seconds=max(wave.eta_seconds, item.eta_seconds),
                tasks=next_tasks,
            )
            continue

        waves.append(
            PlanWave(
                index=len(waves) + 1,
                threads_used=item.threads,
                ram_gb_used=round(item.ram_gb, 3),
                eta_seconds=item.eta_seconds,
                tasks=[item],
            )
        )

    total_eta = round(sum(w.eta_seconds for w in waves), 3)
    return waves, total_eta


def _optimize_mode_selection(
    *,
    mode_options_by_tool: dict[str, list[ToolPlanItem]],
    max_cores: int,
    max_ram_gb: float,
) -> tuple[list[ToolPlanItem], list[PlanWave], float]:
    tool_ids = sorted(mode_options_by_tool.keys())
    if not tool_ids:
        return [], [], 0.0

    selected_index: dict[str, int] = {}
    for tool_id in tool_ids:
        options = mode_options_by_tool.get(tool_id, [])
        if not options:
            raise ValueError(f"[{tool_id}] no executable mode available for planning")
        selected_index[tool_id] = 0

    def build_items(idx_map: dict[str, int]) -> list[ToolPlanItem]:
        return [mode_options_by_tool[t][idx_map[t]] for t in tool_ids]

    current_items = build_items(selected_index)
    current_waves, current_total = _build_parallel_waves(
        items=current_items,
        max_cores=max_cores,
        max_ram_gb=max_ram_gb,
    )

    # Iterative single-tool mode swaps (steepest descent) for global ETA minimization.
    max_iters = max(2, len(tool_ids) * 2)
    for _ in range(max_iters):
        best_move: Optional[tuple[str, int, list[PlanWave], float]] = None
        for tool_id in tool_ids:
            current_idx = selected_index[tool_id]
            options = mode_options_by_tool[tool_id]
            for candidate_idx, _candidate in enumerate(options):
                if candidate_idx == current_idx:
                    continue
                trial_index = dict(selected_index)
                trial_index[tool_id] = candidate_idx
                trial_items = build_items(trial_index)
                trial_waves, trial_total = _build_parallel_waves(
                    items=trial_items,
                    max_cores=max_cores,
                    max_ram_gb=max_ram_gb,
                )
                better = (trial_total + 1e-9) < current_total or (
                    abs(trial_total - current_total) <= 1e-9
                    and len(trial_waves) < len(current_waves)
                )
                if not better:
                    continue
                if best_move is None or (trial_total, len(trial_waves)) < (
                    best_move[3],
                    len(best_move[2]),
                ):
                    best_move = (tool_id, candidate_idx, trial_waves, trial_total)

        if best_move is None:
            break

        tool_id, candidate_idx, best_waves, best_total = best_move
        selected_index[tool_id] = candidate_idx
        current_waves = best_waves
        current_total = best_total

    selected_items = build_items(selected_index)
    return selected_items, current_waves, round(current_total, 3)


def _optimize_mode_selection_cp_sat(
    *,
    mode_options_by_tool: dict[str, list[ToolPlanItem]],
    max_cores: int,
    max_ram_gb: float,
    time_limit_seconds: float,
    warnings: list[str],
) -> Optional[tuple[list[ToolPlanItem], list[PlanWave], float]]:
    from ortools.sat.python import cp_model  # type: ignore

    tool_ids = sorted(mode_options_by_tool.keys())
    if not tool_ids:
        return [], [], 0.0

    for tool_id in tool_ids:
        if not mode_options_by_tool.get(tool_id):
            warnings.append(
                f"[planner=cp_sat] tool '{tool_id}' has no candidate modes; falling back to heuristic planner."
            )
            return None

    num_tools = len(tool_ids)
    max_waves = num_tools
    ram_scale = 1000
    eta_scale = 1000
    max_ram_units = max(1, int(round(max_ram_gb * ram_scale)))

    horizon = 0
    for tool_id in tool_ids:
        max_eta_tool = max(mode.eta_seconds for mode in mode_options_by_tool[tool_id])
        horizon += int(round(max_eta_tool * eta_scale))
    horizon = max(1, horizon)

    model = cp_model.CpModel()

    x: dict[tuple[int, int, int], Any] = {}
    wave_eta: list[Any] = [
        model.NewIntVar(0, horizon, f"wave_eta_{w}") for w in range(max_waves)
    ]
    wave_used: list[Any] = [
        model.NewBoolVar(f"wave_used_{w}") for w in range(max_waves)
    ]

    # x[i,m,w] == 1 iff tool i uses mode m and is assigned to wave w.
    for i, tool_id in enumerate(tool_ids):
        modes = mode_options_by_tool[tool_id]
        for m, _mode in enumerate(modes):
            for w in range(max_waves):
                x[(i, m, w)] = model.NewBoolVar(f"x_{i}_{m}_{w}")

    # Every tool must select exactly one (mode, wave) assignment.
    for i, tool_id in enumerate(tool_ids):
        modes = mode_options_by_tool[tool_id]
        model.Add(
            sum(x[(i, m, w)] for m in range(len(modes)) for w in range(max_waves)) == 1
        )

    for w in range(max_waves):
        cores_terms = []
        ram_terms = []
        assignment_terms = []
        for i, tool_id in enumerate(tool_ids):
            modes = mode_options_by_tool[tool_id]
            for m, mode in enumerate(modes):
                var = x[(i, m, w)]
                cores_terms.append(var * int(mode.threads))
                ram_terms.append(var * int(round(mode.ram_gb * ram_scale)))
                assignment_terms.append(var)

                eta_units = int(round(mode.eta_seconds * eta_scale))
                model.Add(wave_eta[w] >= eta_units).OnlyEnforceIf(var)
                model.Add(var <= wave_used[w])

        model.Add(sum(cores_terms) <= int(max_cores))
        model.Add(sum(ram_terms) <= max_ram_units)
        model.Add(wave_eta[w] <= horizon * wave_used[w])
        # Prevent empty "used" waves: wave_used[w] == 1 implies at least one task in wave w.
        model.Add(sum(assignment_terms) >= wave_used[w])

    # Force contiguous usage of waves to reduce symmetry.
    for w in range(max_waves - 1):
        model.Add(wave_used[w] >= wave_used[w + 1])

    # Primary objective: total sequential wave ETA. Secondary: sum of selected ETA.
    total_wave_eta = sum(wave_eta)
    total_selected_eta = []
    for i, tool_id in enumerate(tool_ids):
        modes = mode_options_by_tool[tool_id]
        for m, mode in enumerate(modes):
            eta_units = int(round(mode.eta_seconds * eta_scale))
            for w in range(max_waves):
                total_selected_eta.append(x[(i, m, w)] * eta_units)
    model.Minimize(total_wave_eta * 1000 + sum(total_selected_eta))

    solver = cp_model.CpSolver()
    if time_limit_seconds > 0:
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = max(1, min(8, multiprocessing.cpu_count()))

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        warnings.append(
            f"[planner=cp_sat] solver failed with status={solver.StatusName(status)}; "
            "falling back to heuristic planner."
        )
        return None

    waves: list[PlanWave] = []
    selected_items: list[ToolPlanItem] = []

    for w in range(max_waves):
        if solver.Value(wave_used[w]) != 1:
            continue

        tasks: list[ToolPlanItem] = []
        threads_used = 0
        ram_used = 0.0
        for i, tool_id in enumerate(tool_ids):
            modes = mode_options_by_tool[tool_id]
            chosen_mode: Optional[ToolPlanItem] = None
            for m, mode in enumerate(modes):
                if solver.Value(x[(i, m, w)]) == 1:
                    chosen_mode = mode
                    break
            if chosen_mode is None:
                continue
            tasks.append(chosen_mode)
            selected_items.append(chosen_mode)
            threads_used += chosen_mode.threads
            ram_used += chosen_mode.ram_gb

        # Defensive guard: should be unreachable with model constraints above.
        if not tasks:
            continue

        wave_eta_seconds = round(float(solver.Value(wave_eta[w])) / eta_scale, 3)
        waves.append(
            PlanWave(
                index=len(waves) + 1,
                threads_used=int(threads_used),
                ram_gb_used=round(float(ram_used), 3),
                eta_seconds=wave_eta_seconds,
                tasks=tasks,
            )
        )

    total_eta = round(sum(w.eta_seconds for w in waves), 3)
    return selected_items, waves, total_eta
