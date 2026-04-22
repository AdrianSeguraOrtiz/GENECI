import json
import multiprocessing
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.markup import escape

from geneci.config import temp_folder_str
from geneci.core.commands.benchmarking.expression_data import (
    expression_data as core_expression_data,
)
from geneci.core.commands.benchmarking.generate_v2 import (
    execute_generate_v2 as core_execute_generate_v2,
)
from geneci.core.commands.benchmarking.generate_v2 import (
    plan_generate_v2_request as core_plan_generate_v2_request,
)
from geneci.core.commands.benchmarking.generate_v2 import (
    preflight_generate_v2_scenario as core_preflight_generate_v2_scenario,
)
from geneci.core.commands.benchmarking.generate_v2 import (
    run_generate_v2 as core_run_generate_v2,
)
from geneci.core.commands.benchmarking.expression_data import (
    generate_from_real_network as core_generate_from_real_network,
)
from geneci.core.commands.benchmarking.expression_data import (
    generate_from_scratch as core_generate_from_scratch,
)
from geneci.core.commands.benchmarking.gene_regulatory_networks import (
    download_real_network as core_download_real_network,
)
from geneci.core.commands.benchmarking.gene_regulatory_networks import (
    gold_standard as core_gold_standard,
)
from geneci.core.commands.benchmarking.validation import (
    dream_list_of_links as core_dream_list_of_links,
)
from geneci.core.commands.benchmarking.validation import (
    dream_pareto_front as core_dream_pareto_front,
)
from geneci.core.commands.benchmarking.validation import (
    dream_weight_distribution as core_dream_weight_distribution,
)
from geneci.core.commands.benchmarking.validation import (
    evaluation_data as core_evaluation_data,
)
from geneci.core.commands.benchmarking.validation import (
    generic_list_of_links as core_generic_list_of_links,
)
from geneci.core.commands.benchmarking.validation import (
    generic_pareto_front as core_generic_pareto_front,
)
from geneci.core.commands.benchmarking.validation import (
    generic_weight_distribution as core_generic_weight_distribution,
)
from geneci.core.commands.infer_network_v2 import (
    infer_network_new as core_infer_network_new,
)
from geneci.core.commands.infer_network_v2 import (
    plan_infer_network_new as core_plan_infer_network_new,
)
from geneci.core.commands.infer_network_v2 import (
    preflight_infer_network_new as core_preflight_infer_network_new,
)
from geneci.core.commands.infer_network_v2 import (
    run_infer_network_new_plan as core_run_infer_network_new_plan,
)
from geneci.core.commands.main import apply_consensus as core_apply_consensus
from geneci.core.commands.main import infer_network as core_infer_network
from geneci.core.commands.plotting import draw_network as core_draw_network
from geneci.core.commands.postprocessing import apply_cut as core_apply_cut
from geneci.enums import (
    Algorithm,
    Challenge,
    CutOffCriteria,
    Database,
    EvalDatabase,
    FromRealGenerateDatabase,
    MemeticDistanceType,
    Mode,
    NodesDistribution,
    Perturbation,
    Technique,
    Topology,
)


def _run_core(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        print(f"[bold red]Error:[/bold red] {escape(str(exc))}")
        raise typer.Exit(code=1)


app = typer.Typer(rich_markup_mode="rich")

# Benchmarking space
benchmarking_app = typer.Typer(help="Benchmarking-related workflows.")
app.add_typer(benchmarking_app, name="benchmarking", rich_help_panel="Benchmarking")

benchmarking_grn_app = typer.Typer(help="Gene regulatory network assets.")
benchmarking_app.add_typer(
    benchmarking_grn_app,
    name="gene-regulatory-networks",
)

benchmarking_expression_app = typer.Typer(help="Expression data assets and generation.")
benchmarking_app.add_typer(
    benchmarking_expression_app,
    name="expression-data",
)

benchmarking_generate_v2_app = typer.Typer(
    help="Scenario-first benchmark generation with normalized dataset packages."
)
benchmarking_app.add_typer(
    benchmarking_generate_v2_app,
    name="generate-v2",
)

generate_app = typer.Typer(help="Generate expression data with SysGenSIM.")
benchmarking_expression_app.add_typer(generate_app, name="generate")

benchmarking_validation_app = typer.Typer(help="Validation datasets and scoring.")
benchmarking_app.add_typer(benchmarking_validation_app, name="validation")

validate_app = typer.Typer(help="Validate inferred networks.")
benchmarking_validation_app.add_typer(validate_app, name="validate")

dream_prediction_app = typer.Typer(
    help="Validation for DREAM challenge networks.",
)
validate_app.add_typer(dream_prediction_app, name="dream-prediction")

generic_prediction_app = typer.Typer(
    help="Validation for generic problems with a gold standard.",
)
validate_app.add_typer(generic_prediction_app, name="generic-prediction")

# Plotting space
plotting_app = typer.Typer(help="Plotting and visualization commands.")
app.add_typer(plotting_app, name="plotting", rich_help_panel="Plotting")

# Postprocessing space
postprocessing_app = typer.Typer(help="Postprocessing commands.")
app.add_typer(
    postprocessing_app, name="postprocessing", rich_help_panel="Postprocessing"
)

# GUI space
gui_app = typer.Typer(help="Graphical interfaces for GENECI workflows.")
app.add_typer(gui_app, name="gui", rich_help_panel="GUI")

# infer-network-v2 space
infer_network_v2_app = typer.Typer(
    help="ToolSpec-driven infer-network-v2 pipeline commands.",
)
app.add_typer(
    infer_network_v2_app,
    name="infer-network-v2",
    rich_help_panel="Main commands",
)


@benchmarking_generate_v2_app.command("preflight")
def benchmarking_generate_v2_preflight(
    scenario: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to scenario-request.json.",
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        help="Optional output path to persist preflight report JSON.",
    ),
):
    """
    Classify simulators for a scenario-first generate-v2 request.
    """
    report = _run_core(core_preflight_generate_v2_scenario, scenario)
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        print(f"[bold green]preflight report written[/bold green]: {output_json}")
    summary = report["catalog_summary"]
    print("[bold green]generate-v2 scenario preflight[/bold green]")
    print(f"  scenario id: {report['scenario']['id']}")
    print(f"  profile: {report['scenario']['profile']}")
    print(
        f"  requested extras: {', '.join(report['scenario']['requested_extras']) or '(none)'}"
    )
    print(
        f"  effective extras: {', '.join(report['scenario']['effective_extras']) or '(none)'}"
    )
    print(f"  input files: {', '.join(report['scenario']['input_files']) or '(none)'}")
    print(
        f"  catalog summary: total={summary['total']} "
        f"eligible={summary['eligible']} warning={summary['warning']} blocked={summary['blocked']}"
    )
    for bucket in ("eligible", "warning", "blocked"):
        entries = report[bucket]
        if not entries:
            continue
        print(f"  {bucket}:")
        for entry in entries:
            suffix = ""
            reasons = (
                entry["blocking_reasons"] if bucket == "blocked" else entry["warnings"]
            )
            if reasons:
                suffix = " - " + "; ".join(reasons)
            print(f"    - {entry['simulator_id']}{suffix}")


@benchmarking_generate_v2_app.command("plan")
def benchmarking_generate_v2_plan(
    scenario: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to scenario-request.json.",
    ),
    simulator_runs: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to simulator-runs.json.",
    ),
    out: Path = typer.Option(
        ...,
        help="Path where the resolved simulation-plan.json will be written.",
    ),
    max_parallel_tasks: int = typer.Option(
        multiprocessing.cpu_count(),
        min=1,
        help="Maximum simulator tasks to run concurrently when this plan is executed.",
    ),
):
    """
    Resolve a scenario request into a runnable simulation-plan.json.
    """
    output_path = _run_core(
        core_plan_generate_v2_request,
        scenario_request_path=scenario,
        simulator_runs_path=simulator_runs,
        output_path=out,
        max_parallel_tasks=max_parallel_tasks,
    )
    print(f"[bold green]simulation plan written[/bold green]: {output_path}")


@benchmarking_generate_v2_app.command("run")
def benchmarking_generate_v2_run(
    plan: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to simulation-plan.json.",
    ),
    output_dir: Path = typer.Option(
        Path("./benchmarks_v2"),
        help="Root directory where the benchmark package will be created.",
    ),
    max_parallel_tasks: Optional[int] = typer.Option(
        None,
        min=1,
        help="Optional override for the plan's max_parallel_tasks.",
    ),
    progress_poll_seconds: float = typer.Option(
        0.5,
        help="Polling interval in seconds for reading per-simulator progress.json.",
    ),
):
    """
    Generate a benchmark package from a resolved simulation-plan.json.
    """
    benchmark_root = _run_core(
        core_run_generate_v2,
        plan_path=plan,
        output_dir=output_dir,
        max_parallel_tasks=max_parallel_tasks,
        progress_poll_seconds=progress_poll_seconds,
    )
    print(f"[bold green]benchmark written[/bold green]: {benchmark_root}")


@benchmarking_generate_v2_app.command("execute")
def benchmarking_generate_v2_execute(
    scenario: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to scenario-request.json.",
    ),
    simulator_runs: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to simulator-runs.json.",
    ),
    output_dir: Path = typer.Option(
        Path("./benchmarks_v2"),
        help="Root directory where the benchmark package will be created.",
    ),
    max_parallel_tasks: int = typer.Option(
        multiprocessing.cpu_count(),
        min=1,
        help="Maximum simulator tasks to run concurrently.",
    ),
    progress_poll_seconds: float = typer.Option(
        0.5,
        help="Polling interval in seconds for reading per-simulator progress.json.",
    ),
):
    """
    End-to-end generate-v2 wrapper (preflight + plan + run).
    """
    benchmark_root = _run_core(
        core_execute_generate_v2,
        scenario_request_path=scenario,
        simulator_runs_path=simulator_runs,
        output_dir=output_dir,
        max_parallel_tasks=max_parallel_tasks,
        progress_poll_seconds=progress_poll_seconds,
    )
    print(f"[bold green]benchmark written[/bold green]: {benchmark_root}")


@app.command(rich_help_panel="Main commands")
def infer_network(
    expression_data: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.",
    ),
    technique: Optional[List[Technique]] = typer.Option(
        ..., case_sensitive=False, help="Inference techniques to be performed."
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
    ),
    str_threads: str = typer.Option(
        None,
        help="Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.",
    ),
    temp_folder_str: str = typer.Option(
        temp_folder_str,
        help="Path to the temporary folder that will make volume for Docker containers. By default, the central temporary folder of execution is used. Useful parameter for parallel executions from Python",
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks"), help="Path to the output folder."
    ),
):
    """
    Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3_RF, GRNBOOST2, GENIE3_ET, MRNET, MRNETB, PCIT, TIGRESS, KBOOST, MEOMI, JUMP3, NARROMI, CMI2NI, RSNET, PCACMI, LOCPCACMI, PLSNET, PIDC, PUC, GRNVBEM, LEAP, NONLINEARODES and INFERELATOR.
    """
    _run_core(
        core_infer_network,
        expression_data=expression_data,
        technique=technique,
        threads=threads,
        str_threads=str_threads,
        temp_folder_str=temp_folder_str,
        output_dir=output_dir,
    )


@infer_network_v2_app.command("preflight")
def infer_network_v2_preflight(
    dataset_manifest: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to dataset-manifest.json (includes embedded dataset spec).",
    ),
    tools_params: Optional[Path] = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help=(
            "Optional tools_params.json to pre-validate requested runs "
            "({'runs': [{'run_id': ..., 'tool_id': ..., 'params': ..., "
            "'execution': {'group_mode': 'global|per_group'}}, ...]})."
        ),
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        help="Optional output path to persist preflight report JSON.",
    ),
    strict: bool = typer.Option(
        False,
        help="If true, incompatible tools/params raise an error during preflight.",
    ),
):
    """
    Validate dataset inputs and compute tool eligibility before planning.
    """
    report = _run_core(
        core_preflight_infer_network_new,
        dataset_manifest_path=dataset_manifest,
        tools_params_path=tools_params,
        strict=strict,
    )
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        print(f"[bold green]preflight report written[/bold green]: {output_json}")
    else:
        eligible = len(report.get("catalog", {}).get("eligible", []))
        warning = len(report.get("catalog", {}).get("warning", []))
        blocked = len(report.get("catalog", {}).get("blocked", []))
        selected = len(report.get("runs", {}).get("selected", []))
        skipped = len(report.get("runs", {}).get("skipped", {}))
        requirement_issues = report.get("runs", {}).get("requirement_issues", {})
        requirement_issue_runs = (
            len(requirement_issues) if isinstance(requirement_issues, dict) else 0
        )
        print("[bold green]infer-network-v2 preflight completed[/bold green]")
        print(f"  eligible tools: {eligible}")
        print(f"  warning tools: {warning}")
        print(f"  blocked tools: {blocked}")
        print(f"  selected runs: {selected}")
        print(f"  skipped runs: {skipped}")
        print(f"  runs with conditional input issues: {requirement_issue_runs}")
        if isinstance(requirement_issues, dict):
            for run_id in sorted(requirement_issues):
                messages = requirement_issues.get(run_id, [])
                if not isinstance(messages, list):
                    continue
                for message in messages:
                    print(f"    - {escape(f'[{run_id}] {message}')}")


@infer_network_v2_app.command("plan")
def infer_network_v2_plan(
    dataset_manifest: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to dataset-manifest.json (includes embedded dataset spec).",
    ),
    tools_params: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help=(
            "Path to tools_params.json in runs format: "
            "{'runs': [{'run_id': ..., 'tool_id': ..., 'params': ..., "
            "'execution': {'group_mode': 'global|per_group'}}, ...]}."
        ),
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks_v2"),
        help="Output root directory for this orchestration run.",
    ),
    max_cores: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Maximum number of CPU cores available to the execution planner.",
    ),
    max_ram_gb: Optional[float] = typer.Option(
        None,
        help="Maximum RAM (GB) available to the execution planner. If omitted, host RAM is used.",
    ),
    planner: str = typer.Option(
        "auto",
        help="Planning strategy: auto, cp_sat, heuristic.",
    ),
    planner_time_limit_seconds: float = typer.Option(
        10.0,
        help="Time limit in seconds for cp_sat planning attempts.",
    ),
    strict: bool = typer.Option(
        False,
        help="If true, incompatible tools/params raise an error.",
    ),
):
    """
    Generate a frozen run directory and plan.json without executing containers.
    """
    _run_core(
        core_plan_infer_network_new,
        dataset_manifest_path=dataset_manifest,
        tools_params_path=tools_params,
        output_dir=output_dir,
        max_cores=max_cores,
        max_ram_gb=max_ram_gb,
        planner=planner,
        planner_time_limit_seconds=planner_time_limit_seconds,
        strict=strict,
    )


@infer_network_v2_app.command("run")
def infer_network_v2_run(
    run_dir: Path = typer.Option(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Path to a frozen run directory produced by infer-network-v2 plan.",
    ),
    progress_poll_seconds: float = typer.Option(
        0.5,
        help="Polling interval in seconds for reading per-tool progress.json during execution.",
    ),
    strict: bool = typer.Option(
        False,
        help="If true, runtime tool failures raise an error.",
    ),
):
    """
    Execute a previously generated plan from run_dir.
    """
    _run_core(
        core_run_infer_network_new_plan,
        run_dir=run_dir,
        progress_poll_seconds=progress_poll_seconds,
        strict=strict,
    )


@infer_network_v2_app.command("execute")
def infer_network_v2_execute(
    dataset_manifest: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to dataset-manifest.json (includes embedded dataset spec).",
    ),
    tools_params: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help=(
            "Path to tools_params.json in runs format: "
            "{'runs': [{'run_id': ..., 'tool_id': ..., 'params': ..., "
            "'execution': {'group_mode': 'global|per_group'}}, ...]}."
        ),
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks_v2"),
        help="Output root directory for this orchestration run.",
    ),
    max_cores: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Maximum number of CPU cores available to the execution planner.",
    ),
    max_ram_gb: Optional[float] = typer.Option(
        None,
        help="Maximum RAM (GB) available to the execution planner. If omitted, host RAM is used.",
    ),
    planner: str = typer.Option(
        "auto",
        help="Planning strategy: auto, cp_sat, heuristic.",
    ),
    planner_time_limit_seconds: float = typer.Option(
        10.0,
        help="Time limit in seconds for cp_sat planning attempts.",
    ),
    progress_poll_seconds: float = typer.Option(
        0.5,
        help="Polling interval in seconds for reading per-tool progress.json during execution.",
    ),
    strict: bool = typer.Option(
        False,
        help="If true, incompatible tools/params and runtime tool failures raise an error.",
    ),
):
    """
    End-to-end execution wrapper (preflight + plan + run).
    """
    _run_core(
        core_infer_network_new,
        dataset_manifest_path=dataset_manifest,
        tools_params_path=tools_params,
        output_dir=output_dir,
        max_cores=max_cores,
        max_ram_gb=max_ram_gb,
        planner=planner,
        planner_time_limit_seconds=planner_time_limit_seconds,
        progress_poll_seconds=progress_poll_seconds,
        strict=strict,
    )


@gui_app.command("infer-network-v2")
def gui_infer_network_v2(
    host: str = typer.Option(
        "127.0.0.1",
        help="Host address for the local GUI server.",
    ),
    port: int = typer.Option(
        8765,
        min=1,
        max=65535,
        help="Port for the local GUI server.",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open-browser/--no-open-browser",
        help=(
            "Automatically open the GUI in your default browser. "
            "Disabled by default to avoid SSH/remote session confusion."
        ),
    ),
):
    """
    Launch the local graphical interface for infer-network-v2.
    """
    from geneci.gui.infer_network_v2.server import run_server

    run_server(host=host, port=port, open_browser=open_browser)


@app.command(rich_help_panel="Main commands")
def apply_consensus(
    confidence_list: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists to be agreed upon.",
        rich_help_panel="Input data",
    ),
    gene_names: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.",
        rich_help_panel="Input data",
    ),
    time_series: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.",
        rich_help_panel="Times series - Loyalty",
    ),
    known_interactions: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the known interactions between genes. If specified, a local search process will be performed before mutation.",
        rich_help_panel="Local search",
    ),
    crossover_probability: float = typer.Option(
        0.9, help="Crossover probability", rich_help_panel="Crossover"
    ),
    num_parents: int = typer.Option(
        3, help="Number of parents", rich_help_panel="Crossover"
    ),
    mutation_probability: float = typer.Option(
        -1,
        help="Mutation probability. [default: 1/len(files)]",
        show_default=False,
        rich_help_panel="Mutation",
    ),
    mutation_strength: float = typer.Option(
        0.1, help="Mutation strength", rich_help_panel="Mutation"
    ),
    memetic_distance_type: MemeticDistanceType = typer.Option(
        MemeticDistanceType.all,
        help="Memetic distance type",
        rich_help_panel="Local search",
    ),
    memetic_probability: float = typer.Option(
        0.55, help="Memetic probability", rich_help_panel="Local search"
    ),
    population_size: int = typer.Option(
        100, help="Population size", rich_help_panel="Diversity and depth"
    ),
    num_evaluations: int = typer.Option(
        25000, help="Number of evaluations", rich_help_panel="Diversity and depth"
    ),
    cut_off_criteria: CutOffCriteria = typer.Option(
        "PercLinksWithBestConf",
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
        rich_help_panel="Cut-Off",
    ),
    cut_off_value: float = typer.Option(
        0.4,
        help="Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4",
        rich_help_panel="Cut-Off",
    ),
    function: Optional[List[str]] = typer.Option(
        ...,
        help="""A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. \n
                Available terms: \n
                    \t - Quality \n
                    \t - DegreeDistribution \n
                    \t - Motifs \n
                    \t - Dynamicity \n
                    \t - ReduceNonEssentialsInteractions \n
                    \t - EigenVectorDistribution \n
                    \t - Loyalty \n
                    \t - Clustering \n
                Examples: \n
                    \t - Objective of one term: "Quality" \n
                    \t - Objective of two terms: "0.5*Quality+0.5*DegreeDistribution" \n""",
        rich_help_panel="Fitness",
    ),
    reference_point: str = typer.Option(
        "-",
        help="Reference point for the Pareto front. If specified, the search will be oriented towards this point. The format is 'f1;f2;f3'.",
        rich_help_panel="Fitness",
    ),
    algorithm: Algorithm = typer.Option(
        ...,
        help="Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).",
        rich_help_panel="Orchestration",
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
        rich_help_panel="Orchestration",
    ),
    plot_results: bool = typer.Option(
        True,
        help="Indicate if you want to represent results graphically.",
        rich_help_panel="Graphics",
    ),
    compare_performance: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Reference front with which to compare performance. Specifically, a graph will be returned to show for each generation the percentage of reference front solutions that have already been dominated by the current population. If a reference point is specified to carry out an articulated selection, the part of the reference front covered by that reference point will only be taken into account.",
        rich_help_panel="Graphics",
    ),
    output_dir: Path = typer.Option(
        "<<conf_list_path>>/../ea_consensus",
        help="Path to the output folder.",
        rich_help_panel="Output",
    ),
):
    """
    Analyze several trust lists and build a consensus network by applying an evolutionary algorithm.
    """
    _run_core(
        core_apply_consensus,
        confidence_list=confidence_list,
        gene_names=gene_names,
        time_series=time_series,
        known_interactions=known_interactions,
        crossover_probability=crossover_probability,
        num_parents=num_parents,
        mutation_probability=mutation_probability,
        mutation_strength=mutation_strength,
        memetic_distance_type=memetic_distance_type,
        memetic_probability=memetic_probability,
        population_size=population_size,
        num_evaluations=num_evaluations,
        cut_off_criteria=cut_off_criteria,
        cut_off_value=cut_off_value,
        function=function,
        reference_point=reference_point,
        algorithm=algorithm,
        threads=threads,
        plot_results=plot_results,
        compare_performance=compare_performance,
        output_dir=output_dir,
    )


@benchmarking_grn_app.command()
def download_real_network(
    database: FromRealGenerateDatabase = typer.Option(
        ...,
        case_sensitive=False,
        help="Database from which the real gene regulatory network is to be obtained.",
    ),
    id: str = typer.Option(
        ..., help="The identifier of the gene network within the selected database."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Download real gene regulatory networks in interaction-list format for simulation workflows.
    """
    _run_core(
        core_download_real_network,
        database=database,
        id=id,
        output_dir=output_dir,
    )


@benchmarking_grn_app.command()
def gold_standard(
    database: Optional[List[Database]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading gold standards."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(
        None,
        help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5.",
    ),
    password: str = typer.Option(
        None,
        help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5.",
    ),
):
    """
    Download benchmark gold-standard networks.
    """
    _run_core(
        core_gold_standard,
        database=database,
        output_dir=output_dir,
        username=username,
        password=password,
    )


@benchmarking_expression_app.command(name="download")
def expression_data(
    database: Optional[List[Database]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading expression data."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(
        None,
        help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5.",
    ),
    password: str = typer.Option(
        None,
        help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5.",
    ),
):
    """
    Download benchmark expression datasets.
    """
    _run_core(
        core_expression_data,
        database=database,
        output_dir=output_dir,
        username=username,
        password=password,
    )


@generate_app.command()
def generate_from_scratch(
    topology: Topology = typer.Option(
        ...,
        case_sensitive=False,
        help="The type of topology to be attributed to the simulated gene network.",
    ),
    network_size: int = typer.Option(
        ...,
        min=20,
        help="Number of genes that will make up the simulated gene network.",
    ),
    perturbation: Perturbation = typer.Option(
        ...,
        case_sensitive=False,
        help="Type of perturbation to apply on the network to simulate expression levels for genes.",
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Simulate expression data from scratch using SysGenSIM.
    """
    _run_core(
        core_generate_from_scratch,
        topology=topology,
        network_size=network_size,
        perturbation=perturbation,
        output_dir=output_dir,
    )


@generate_app.command()
def generate_from_real_network(
    real_list_of_links: Path = typer.Option(
        ...,
        help="Path to the csv file with the list of links. You can only specify either a value of 1 for an activation link or -1 to indicate inhibition.",
    ),
    perturbation: Perturbation = typer.Option(
        ...,
        case_sensitive=False,
        help="Type of perturbation to apply on the network to simulate expression levels for genes.",
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Simulate expression data from a real-world network using SysGenSIM.
    """
    _run_core(
        core_generate_from_real_network,
        real_list_of_links=real_list_of_links,
        perturbation=perturbation,
        output_dir=output_dir,
    )


@benchmarking_validation_app.command()
def evaluation_data(
    database: Optional[List[EvalDatabase]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading evaluation data."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(..., help="Synapse account username."),
    password: str = typer.Option(..., help="Synapse account password."),
):
    """
    Download evaluation data for DREAM challenges.
    """
    _run_core(
        core_evaluation_data,
        database=database,
        output_dir=output_dir,
        username=username,
        password=password,
    )


@dream_prediction_app.command()
def dream_list_of_links(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command benchmarking validation evaluation-data.",
    ),
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
):
    """
    Validate one confidence list against a DREAM challenge network.
    """
    _run_core(
        core_dream_list_of_links,
        challenge=challenge,
        network_id=network_id,
        synapse_file=synapse_file,
        confidence_list=confidence_list,
    )


@dream_prediction_app.command()
def dream_weight_distribution(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command benchmarking validation evaluation-data.",
    ),
    weight_file_summand: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv",
    ),
):
    """
    Validate one weighted confidence distribution against a DREAM challenge network.
    """
    _run_core(
        core_dream_weight_distribution,
        challenge=challenge,
        network_id=network_id,
        synapse_file=synapse_file,
        weight_file_summand=weight_file_summand,
    )


@dream_prediction_app.command()
def dream_pareto_front(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command benchmarking validation evaluation-data.",
    ),
    weights_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the weights corresponding to a pareto front.",
    ),
    fitness_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the fitness values corresponding to a pareto front.",
    ),
    confidence_folder: Path = typer.Option(
        ...,
        help="Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'",
    ),
    output_dir: Path = typer.Option("<<weights_file_dir>>", help="Output folder path"),
    plot_metrics: bool = typer.Option(
        True,
        help="Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.",
    ),
):
    """
    Validate a full Pareto front against a DREAM challenge network.
    """
    _run_core(
        core_dream_pareto_front,
        challenge=challenge,
        network_id=network_id,
        synapse_file=synapse_file,
        weights_file=weights_file,
        fitness_file=fitness_file,
        confidence_folder=confidence_folder,
        output_dir=output_dir,
        plot_metrics=plot_metrics,
    )


@generic_prediction_app.command()
def generic_list_of_links(
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
):
    """
    Validate one confidence list against a generic gold standard.
    """
    _run_core(
        core_generic_list_of_links,
        confidence_list=confidence_list,
        gs_binary_matrix=gs_binary_matrix,
    )


@generic_prediction_app.command()
def generic_weight_distribution(
    weight_file_summand: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
):
    """
    Validate one weighted confidence distribution against a generic gold standard.
    """
    _run_core(
        core_generic_weight_distribution,
        weight_file_summand=weight_file_summand,
        gs_binary_matrix=gs_binary_matrix,
    )


@generic_prediction_app.command()
def generic_pareto_front(
    weights_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the weights corresponding to a pareto front.",
    ),
    fitness_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the fitness values corresponding to a pareto front.",
    ),
    confidence_folder: Path = typer.Option(
        ...,
        help="Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
    output_dir: Path = typer.Option("<<weights_file_dir>>", help="Output folder path"),
    plot_metrics: bool = typer.Option(
        True,
        help="Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.",
    ),
):
    """
    Validate a full Pareto front against a generic gold standard.
    """
    _run_core(
        core_generic_pareto_front,
        weights_file=weights_file,
        fitness_file=fitness_file,
        confidence_folder=confidence_folder,
        gs_binary_matrix=gs_binary_matrix,
        output_dir=output_dir,
        plot_metrics=plot_metrics,
    )


@plotting_app.command()
def draw_network(
    confidence_list: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists to be represented"
    ),
    mode: Mode = typer.Option("Interactive2D", help="Mode of representation"),
    nodes_distribution: NodesDistribution = typer.Option(
        "Spring",
        help="Node distribution in graph. Note: Interactive2D mode has its own distribution of nodes, so in case of be selected this parameter will be ignored",
    ),
    confidence_cut_off: float = typer.Option(0.5, help="Cut off value for confidence"),
    output_folder: Path = typer.Option(
        "<<conf_list_path>>/../network_graphics", help="Path to output folder"
    ),
):
    """
    Draw gene regulatory networks from confidence lists.
    """
    _run_core(
        core_draw_network,
        confidence_list=confidence_list,
        mode=mode,
        nodes_distribution=nodes_distribution,
        confidence_cut_off=confidence_cut_off,
        output_folder=output_folder,
    )


@postprocessing_app.command()
def apply_cut(
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
    gene_names: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the list of trusts will be considered.",
    ),
    cut_off_criteria: CutOffCriteria = typer.Option(
        ...,
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
    ),
    cut_off_value: float = typer.Option(
        ...,
        help="Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4",
    ),
    output_file: Path = typer.Option(
        "<<conf_list_path>>/../networks/<<conf_list_name>>.csv",
        help="Path to the output CSV file that will contain the binary matrix resulting from the cutting operation.",
    ),
):
    """
    Convert a confidence list into a binary network matrix.
    """
    _run_core(
        core_apply_cut,
        confidence_list=confidence_list,
        gene_names=gene_names,
        cut_off_criteria=cut_off_criteria,
        cut_off_value=cut_off_value,
        output_file=output_file,
    )


if __name__ == "__main__":
    app()
