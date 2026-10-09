# Preference Diversity, Mobility, and Movement Behaviour in a Schelling Model

This CITS4403 project asks: **How do preference diversity, mobility, and movement
behaviour interact to affect segregation and stabilisation?** Agents respond to
their local neighbourhoods, and their repeated decisions produce population-level
spatial patterns. The project investigates the interaction of three extensions to
the classic model, with an optional social-influence comparison. Its contribution
is this implemented combination and controlled experimental comparison; it does
not claim that these extensions are individually new to the research literature.

## Current project status

The repository contains the model, experiment runner, tests, and analysis notebook.
The supplied CSV files are **exploratory pilot and smoke data**. The pilot uses a
150-iteration cap, whereas the current runner defaults to 500. Final `main` and
`social` datasets have not yet been generated. The notebook identifies the selected
dataset and its limitations; exploratory observations must not be presented as
completed final-experiment conclusions.

## Setup

Use **Python 3.10 or newer**. The project has been run locally with **Python 3.14.4
on Windows**; older supported versions and other operating systems should be
checked in their own environments. Run all commands below from the repository
root, the directory containing this README and `requirements.txt`.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

macOS/Linux shell:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

These commands use the environment's interpreter directly; activation is optional.
`requirements.txt` declares NumPy, Matplotlib, and Jupyter with minimum versions.
It is **not an exact dependency lock file**. Record the Python version, installed
package versions, and Git commit alongside final results when archiving an
experiment. `.venv/`, Python bytecode, and notebook checkpoint folders are ignored
by Git.

## Quick checks and a small demonstration

The demonstration runs one simulation and prints its iteration count, stopping
status, final segregation index, and satisfaction rate. It does not write a CSV:

```powershell
.\.venv\Scripts\python.exe -B -m src.main
```

Run the automated tests:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Check the experiment-to-CSV workflow using eight short runs in a separate output
directory, preserving the supplied data:

```powershell
.\.venv\Scripts\python.exe -B -m utils.experiment_runner --design smoke --output-dir tmp/smoke-check
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`
in these commands. `-B` only prevents Python bytecode files from being written;
it is optional and does not change the experiment parameters.

The smoke command prints `Runs: 8`, both output paths, and a `Completed` message
for each run. If either destination already exists, it stops before running.
Choose a new output directory to keep earlier results. The optional `--overwrite`
flag explicitly replaces both output files; use it only when replacement is
intended. A smoke run checks execution and file structure, not the research
hypotheses.

## Implemented model

The default population occupies a finite **40 x 40** grid with **10% vacancy** and
an equal split between groups A and B. Boundaries are fixed, with no wraparound.
An agent considers occupied cells in its Moore neighbourhood: at most eight
adjacent cells, fewer along an edge or corner.

For agent $i$, let $N_i$ be its occupied neighbours and $g_i$ its group. Local
similarity is

$$
s_i = \begin{cases}
\dfrac{|\{j \in N_i : g_j = g_i\}|}{|N_i|}, & |N_i| > 0, \\
0, & |N_i| = 0.
\end{cases}
$$

An agent is satisfied when $s_i \ge q_i$, where $q_i$ is its preference threshold.
The zero-neighbour convention matters: an isolated agent with a positive
threshold is dissatisfied. The reported segregation index is the agent-weighted
mean $S = \frac{1}{n}\sum_i s_i$. Satisfaction rate is the proportion of agents
meeting their individual thresholds. Higher $S$ indicates greater local
same-group similarity under this definition; it is not a direct measure of a
real-world population.

### Preferences, mobility, and relocation

The experiment runner crosses the following factors:

| Factor | Values | Meaning |
| --- | --- | --- |
| Preference diversity | `homogeneous`, `low`, `high` | All 0.5; symmetric samples in [0.4, 0.6]; symmetric samples in [0.2, 0.8] |
| Mobility | **1, 3, 5** | Maximum Chebyshev distance to an accessible vacant cell |
| Behaviour | `random`, `improving`, `best_fit` | Destination selection rules below |

Diverse preferences are sampled in symmetric pairs around 0.5, with an additional
0.5 value for an odd population size, then shuffled. This holds the **initial
population mean** at 0.5, up to floating-point precision. Individual groups need
not have identical sample means. Mobility is the square-region distance
$\max(|\Delta r|, |\Delta c|)$, not Euclidean distance.

Only dissatisfied agents attempt to move, and occupied destinations are excluded:

- `random`: choose uniformly from accessible vacant cells.
- `improving`: choose uniformly from accessible vacant cells with strictly higher
  similarity than the current location; stay if none improve it.
- `best_fit`: choose a vacant location with the highest accessible similarity,
  breaking ties randomly. The current location is not a candidate, so this rule
  can move to a destination that does not improve the current similarity.

Destination similarity is evaluated with the moving agent's original cell
treated as empty. Within each iteration, agents move **sequentially in shuffled
order**, so later agents observe earlier moves.

### Optional social influence and stopping

Social influence is disabled by default. When enabled, it runs after the movement
phase using the agents' resulting neighbourhoods:

$$
q_i^{\mathrm{new}} = q_i^{\mathrm{old}} +
\alpha\left(\frac{1}{|N_i|}\sum_{j\in N_i}q_j^{\mathrm{old}}
- q_i^{\mathrm{old}}\right),
\qquad \alpha=0.10.
$$

All new thresholds are calculated from the same pre-update preference snapshot,
then applied together. An isolated agent keeps its threshold. Values are bounded
to [0, 1], and changes of at most `1e-12` are not applied. Identical initial
thresholds do not drift. With heterogeneous thresholds, this neighbour-averaging
rule does **not generally preserve the population mean**; both final preference
mean and standard deviation are recorded.

A run is marked `stabilised=True` when an iteration contains **no moves and no
preference updates**. It also stops at the configured iteration cap.
Stabilisation does not imply that every agent is satisfied: some may have no
eligible move. CSV `iterations` records how long a run was observed;
`stabilisation_time` is populated only for stabilised runs and is empty otherwise.
The analysis reports capped-run counts and stabilisation proportions alongside
time among stabilised runs, rather than treating a capped observation as a known
time to stabilisation.

Each simulation has its own `random.Random(seed)` instance for placement,
agent order, and destination choices. Preference sampling uses a separate seeded
generator. At a fixed grid size and population, equal simulation seeds give
matched initial spatial layouts. Preference vectors follow the selected diversity
condition, and random-number consumption can diverge as behaviours differ.

## Experiment designs and CSV files

Current runner settings are:

| Design | Seeds | Grid | Iteration cap | Runs | Output stem |
| --- | --- | --- | --- | --- | --- |
| `smoke` | 0-1 | 10 x 10 | 10 | 8 | `smoke` |
| `pilot` | 0-9 | 40 x 40 | 500 | 270 | `pilot` |
| `main` | 0-9 | 40 x 40 | 500 | 270 | `main_experiment` |
| `social` | 0-9 | 40 x 40 | 500 | 540 | `social_influence` |

`pilot` and `main` currently have the same 27 factor combinations and ten seeds;
their different names do not create independent evidence. `social` crosses those
combinations with influence disabled/enabled. `smoke` uses homogeneous/high
diversity, mobility 1, random behaviour, and both influence settings. All designs
use vacancy 0.10 and group split 0.50.

When ready to generate the longer experiments, run `social` once for both the
main analysis and the influence comparison. Its 270 influence-off runs are the
same configurations required by `main`; the notebook uses that subset directly.
This is separate from the quick checks above; **final runs are still pending**:

```powershell
.\.venv\Scripts\python.exe -B -m utils.experiment_runner --design social --output-dir data
```

If only the influence-off study is needed, use `--design main` instead (270
runs). Do not run both designs and count their repeated control configurations
as independent replicates.

To run a new pilot without replacing the legacy pilot:

```powershell
.\.venv\Scripts\python.exe -B -m utils.experiment_runner --design pilot --output-dir tmp/pilot-current
```

Each design writes `<stem>_results.csv` with one row per run and
`<stem>_history.csv` with one row per observed iteration. They share `run_id`.
Summary rows record parameters, initial and final preference summaries,
segregation, satisfaction, stopping status, and move/update counts. History starts
at iteration 1, after the first update. `run_id` is derived from the configuration;
it does not identify the source-code revision or dependency versions.

The runner flushes completed runs progressively. An interrupted command can leave
partial files; their existence is not proof that an experiment completed. Use the
analysis validation below before interpreting them. There is no automatic resume
of a partially completed file.

### Provenance of the supplied data

The checked-in `data/pilot_results.csv` and `data/pilot_history.csv` contain a
**legacy exploratory pilot: 270 runs, seeds 0-9, 40 x 40 grid, 150-iteration cap**.
The shorter cap differs from the current runner's 500-iteration design. The
checked-in smoke files are workflow examples. Keep these datasets labelled by
their actual configurations; do not relabel the 150-cap pilot as a completed
500-cap experiment or combine repeated conditions across them as independent
replicates. No `main_experiment_*` or `social_influence_*` final CSVs are supplied
at this stage.

## Open and run the analysis notebook

Windows:

```powershell
.\.venv\Scripts\python.exe -m jupyter notebook notebooks/experiment_analysis.ipynb
```

macOS/Linux:

```bash
.venv/bin/python -m jupyter notebook notebooks/experiment_analysis.ipynb
```

Choose the project's environment as the kernel if prompted. The notebook starts
with explicit dataset settings: `DATASET = 'pilot'` and `MAX_ITERATIONS = 150` for
the supplied exploratory pilot. Run the cells in order. Once the corresponding
formal data exists, select `DATASET = 'main'` or `'social'` and
`MAX_ITERATIONS = 500`. If results were written elsewhere, set the notebook's data
directory to that location.

With `SAVE_FIGURES = True` (the default), plot PNGs are exported to
`notebooks/figures/<dataset>_<cap>/`. Re-running that selection replaces its
same-named figures, but never changes the source CSVs. The saved notebook also
contains inline plots for viewing without executing it.

The notebook uses
`utils.analysis_validation.load_dataset(directory, design, max_iterations=None)`
to check the selected summary and history against the intended design. It rejects
incomplete or mismatched datasets instead of automatically substituting smoke or
pilot results for a missing formal experiment. Select the legacy 150 cap
explicitly; a current 500-cap validation must not accept it as the same design.

Analyses retain seed blocks: marginal summaries first average the crossed
conditions within each seed, and social comparisons use matched on-minus-off
differences. Bootstrap confidence intervals resample seed blocks rather than
treating every crossed condition as a new independent replicate. There are ten
seed blocks in the current full designs, so uncertainty and sensitivity to seeds
remain relevant when interpreting the plots. Per-condition summaries, observed
stopping time, stabilisation proportions, and time conditional on stabilising
answer different questions and are labelled separately.

For the final hand-in, generate and validate the agreed formal datasets, rerun the
notebook, save its outputs, and write conclusions supported by those results.
The current exploratory discussion does not establish final hypothesis outcomes.

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/agent.py` | Satisfaction, destination evaluation, and movement rules |
| `src/grid.py` | Occupancy, neighbourhoods, placement, and movement |
| `src/simulation.py` | Initialisation, iteration order, influence, metrics, and stopping |
| `src/main.py` | Small console demonstration |
| `utils/experiment_runner.py` | Factorial designs, seeded runs, and CSV export |
| `utils/analysis_validation.py` | Dataset and history validation |
| `utils/analysis_statistics.py` | Seed-aware summaries and uncertainty |
| `notebooks/experiment_analysis.ipynb` | Model explanation, selected-data analysis, and figures |
| `tests/` | Model, runner, and analysis checks |
| `data/` | Supplied exploratory data and, when generated, labelled formal outputs |

Review the test output for the current checkout rather than relying on an old test
count. For collaboration, use focused pull requests with explanations of the
model decisions, meaningful review comments, and evidence that each contributor
can explain their implementation and results.
