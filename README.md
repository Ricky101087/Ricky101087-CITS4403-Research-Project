CITS4403 Research Project
How Preference Diversity, Mobility, and Movement Behaviour Affect Emergent
Segregation
Research Question
How do preference diversity, mobility, and movement behaviour interact to affect the
final segregation level and stabilisation time of a Schelling model?
Why This Is a Complex System
Segregation in the Schelling model is an example of an emergent phenomenon. Individual
agents make decisions based only on the composition of their local neighbourhood, yet
repeated individual decisions can produce large-scale patterns of segregation across the entire
population.
The proposed model extends the standard Schelling model by introducing differences in how
individual agents make relocation decisions. Rather than assuming that all agents behave
identically, agents can differ in their preference for similar neighbours, their mobility, and
their movement behaviour.
Preference determines how tolerant an agent is of neighbours from another group. Mobility
determines the range of locations an agent can access when dissatisfied. Movement behaviour
determines how the agent selects a new location from those available to it.
These individual-level differences may interact in non-linear ways. For example, increasing
an agent's mobility may have little effect if the agent moves randomly, but may have a larger
effect if the agent actively searches for a more suitable location. Similarly, preference
diversity may produce different system-level outcomes depending on how easily agents can
relocate.
The project therefore investigates how relatively simple individual rules and characteristics
can interact to produce different global patterns of segregation.
Base Model
The project will use the Schelling segregation model as its foundation.
The environment will consist of a 40 × 40 grid containing two groups of agents, referred to
as Group A and Group B. Approximately 10% of the grid cells will initially be empty,
allowing agents to relocate.
Each agent will have a similarity preference threshold, represented by q. For an agent, the
proportion of occupied neighbouring cells containing members of the same group is
calculated as:
same-group neighbours
𝑠 =
total occupied neighbours
An agent is considered satisfied when:
𝑠 ≥ 𝑞
If an agent is dissatisfied, it is allowed to attempt to relocate to another empty location.
The model will use a Moore neighbourhood, meaning that each agent considers the eight
cells surrounding its current location.
The simulation will continue until the population reaches a stable state or a predefined
maximum number of iterations is reached.
Extended Model
The proposed model introduces three extensions to the basic Schelling model:
1. Preference diversity
2. Mobility
3. Movement behaviour
These variables will be investigated individually and in combination.
1. Preference Diversity
In the standard model, all agents can be given the same similarity preference threshold. The
extended model allows agents to have different thresholds.
For example, a population could have:
Agent 1: q = 0.30
Agent 2: q = 0.40
Agent 3: q = 0.50
Agent 4: q = 0.60
while another population could have:
Every agent: q = 0.45
To isolate the effect of diversity, experiments will control the mean preference threshold
while changing the amount of variation around that mean.
Possible conditions are:
• No diversity: all agents have the same threshold.
• Low diversity: agents have small differences in thresholds.
• High diversity: agents have larger differences in thresholds.
This allows the experiment to investigate whether populations with the same average
preference can produce different outcomes simply because individual preferences are
distributed differently.
2. Mobility
Mobility represents how far an agent can search when attempting to relocate.
Rather than assuming that every dissatisfied agent can access every empty cell in the grid, the
agent will only consider vacant locations within a specified movement range.
For example:
• Low mobility: movement radius = 2 cells
• Medium mobility: movement radius = 5 cells
• High mobility: movement radius = 10 cells
The mobility range therefore determines the set of possible locations available to an agent.
A highly mobile agent can potentially access a much larger part of the environment, while a
low-mobility agent is restricted to locations close to its current position.
3. Movement Behaviour
Agents will also differ in how they select a new location.
At least two movement behaviours will be investigated:
Random behaviour
A dissatisfied agent selects a random available location within its mobility range.
The agent does not compare all available locations before moving.
Improving behaviour
A dissatisfied agent evaluates available locations within its mobility range and selects a
location that provides a higher level of similarity than its current location.
An optional third behaviour can be introduced if computationally feasible:
Best-fit behaviour
The agent evaluates the available locations within its mobility range and selects the location
with the highest similarity.
This creates a distinction between simply having the ability to move and actively using that
ability to find a preferred location.
Agent Representation
Each agent can therefore be represented by several attributes:
Attribute Description
Group Group A or Group B
Preference q Minimum proportion of same-group neighbours required for satisfaction
Mobility m Maximum distance the agent can search when relocating
Behaviour b Rule used to select a new location
For example:
Agent 1
Group: A
Preference: 0.60
Mobility: 10
Behaviour: Improving
could behave very differently from:
Agent 2
Group: A
Preference: 0.30
Mobility: 2
Behaviour: Random
even though both agents belong to the same group.
Hypothesis
We hypothesise that preference diversity, mobility, and movement behaviour will influence
the emergent segregation patterns of the system.
In particular, the effect of one variable may depend on the values of the others. For example,
increased mobility may have a different effect when agents choose locations randomly
compared with when they actively search for improved locations.
We therefore expect that the interaction between these individual-level characteristics will
affect both the final level of segregation and the time required for the system to stabilise.
The experiment will not assume that increasing any particular variable must necessarily
increase or decrease segregation. Instead, simulation results will be used to determine the
direction and strength of these relationships.
Experimental Design
The experiment will use a factorial design so that the variables can be studied both
independently and in combination.
Independent Variables
Preference diversity
Three levels:
1. No diversity
2. Low diversity
3. High diversity
The mean preference threshold will remain constant between conditions where possible.
Mobility
Three levels:
1. Low
2. Medium
3. High
For example:
Mobility level Search radius
Low 2
Mobility level Search radius
Medium 5
High 10
Movement behaviour
Three possible levels:
1. Random
2. Improving
3. Best-fit
If the third behaviour proves unnecessarily complex

## Optional extension: social influence

The simulation can optionally allow an agent's preference threshold to move
toward the mean preference of its occupied Moore neighbours after each
iteration. It is disabled by default so that baseline experiments retain their
original behaviour.

For agent `i`, the update is:

`q_i(new) = q_i(old) + influence_strength * (neighbour_mean - q_i(old))`

All new preferences are calculated from the same pre-update snapshot and are
then applied together. This avoids an ordering effect in which an agent could
observe a neighbour that had already been updated during the same iteration.
Agents without occupied neighbours keep their existing preference, and all
preferences are constrained to the range `[0, 1]`.

Example configuration:

```python
sim = Simulation(
    social_influence=True,
    influence_strength=0.10,
    seed=42,
)
```

Social influence only changes outcomes when agents begin with different
preference thresholds. With identical starting preferences, the neighbour
mean is identical to each agent's current preference, so no drift occurs.
