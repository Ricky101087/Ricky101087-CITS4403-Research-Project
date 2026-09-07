# CITS4403 Research Project

## Provisional Title

**How Individual Preference Diversity Changes Emergent Segregation**

**Compared with a population in which everyone has the same similarity preference, how does variation in individual preference thresholds affect the final segregation level and the time required for a Schelling model to stabilise?**

## Why This Is a Complex System

Each agent follows a simple local rule and sees only nearby neighbours. No agent controls the whole grid, but repeated local moves can produce large-scale clusters and segregation. The global pattern is therefore an emergent outcome of many interacting agents.

## Base Model

- A `40 × 40` grid represents a city.
- Each occupied cell contains a Group A or Group B agent; approximately 10% of cells are initially empty.
- An agent observes its eight surrounding cells (Moore neighbourhood).
- Let `s` be the fraction of occupied neighbours belonging to the same group.
- Each agent has a preference threshold `q`. It is satisfied when `s >= q`.
- An unsatisfied agent moves to a randomly selected empty cell.
- Updates continue until all agents are satisfied or a maximum number of steps is reached.

## Main Comparison

1. **Homogeneous population:** every agent has the same threshold `q`.
2. **Heterogeneous population:** agents have different thresholds drawn from a bounded distribution with the same mean `q`.

Using the same mean preference makes the comparison more controlled: the main difference is whether preferences are identical or diverse.

## Hypothesis

Preference heterogeneity will change the tipping behaviour of the model. In particular, more tolerant agents may remain in mixed areas while less tolerant agents form clusters, producing different final patterns and stabilisation times from a homogeneous population with the same average preference.

This hypothesis intentionally does not assume that heterogeneity always reduces segregation; the direction and size of the effect will be determined experimentally.

## Experimental Design

### Independent Variables

- Mean similarity-preference threshold: provisionally `0.20, 0.30, 0.40, 0.50, 0.60`.
- Threshold variation: `0` for the homogeneous baseline, then several non-zero standard deviations.
- Vacancy rate: begin with `10%`; test additional values only after the main experiment works.

### Controlled Variables

- Grid size.
- Group proportions.
- Initial vacancy rate in the main experiment.
- Neighbourhood definition.
- Movement rule.
- Maximum number of updates.

### Measurements

- **Segregation index:** average fraction of same-group neighbours among occupied neighbours.
- Fraction of satisfied agents over time.
- Number of moves or iterations required to stabilise.
- Number and size of same-group clusters as an optional extension.

### Replication

- Run at least 30 random initialisations for every condition.
- Report mean results, distributions, and confidence intervals.
- Show initial and final grids for qualitative comparison.
- Plot segregation and satisfaction over time.

## Independent Investigation

The classic model normally begins with one common preference rule. This project explicitly compares two modelling assumptions—identical versus diverse individual preferences—while holding the average preference constant. It investigates whether a simplifying assumption at the individual level changes the emergent system-level conclusion.

## Minimum Viable Project

If time is limited, complete only:

- one grid size;
- one vacancy rate;
- homogeneous versus heterogeneous thresholds;
- five mean-threshold values;
- 30 repetitions per condition;
- final segregation, stabilisation time, and initial/final visualisations.

No real-world dataset, network model, or advanced optimisation is required for this minimum version.

## Limitations

- The two groups and square grid are abstract representations.
- Decisions depend only on nearby group composition.
- Moving has no financial, geographic, or social cost.
- Agents do not learn or change preferences.
- The model demonstrates possible mechanisms rather than explaining a specific real city.

## Possible Extensions

Add only after the minimum experiment is complete:

- movement to a satisfying vacancy rather than a random vacancy;
- different vacancy rates;
- different neighbourhood radii;
- asymmetric preference distributions between the two groups.

## Initial References

- Schelling, T. C. (1971). *Dynamic models of segregation*. The Journal of Mathematical Sociology, 1(2), 143–186. https://doi.org/10.1080/0022250X.1971.9989794
- Goles Domic, N., Goles, E., & Rica, S. (2011). *Dynamics and complexity of the Schelling segregation model*. Physical Review E, 83, 056111. https://doi.org/10.1103/PhysRevE.83.056111
