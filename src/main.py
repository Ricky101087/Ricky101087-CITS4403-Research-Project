from simulation import Simulation

sim = Simulation(preference=0.5, mobility=5, behaviour="random", seed=42)
sim.run()

print(f"Iterations: {sim.iterations}")
print(f"Stabilised: {sim.stabilised}")
print(f"Final segregation index: {sim.history[-1]['segregation_index']:.3f}")
print(f"Final satisfaction rate: {sim.history[-1]['satisfaction_rate']:.3f}")