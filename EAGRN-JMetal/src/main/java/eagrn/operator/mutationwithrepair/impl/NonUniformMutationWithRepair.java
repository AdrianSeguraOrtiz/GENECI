package eagrn.operator.mutationwithrepair.impl;

import eagrn.operator.repairer.WeightRepairer;
import org.uma.jmetal.operator.mutation.impl.NonUniformMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class NonUniformMutationWithRepair extends NonUniformMutation {
    private WeightRepairer repairer;

    public NonUniformMutationWithRepair(double mutationProbability, double perturbation, int maxIterations, WeightRepairer repairer) {
        super(mutationProbability, perturbation, maxIterations);
        this.repairer = repairer;
    }

    @Override
    public DoubleSolution execute(DoubleSolution solution) throws JMetalException {
        DoubleSolution mutated_sol = super.execute(solution);
        if (mutated_sol.variables().equals(solution.variables())) {
            repairer.repairSolutionOnly(mutated_sol);
        } else {
            repairer.repairSolutionWithKnownInteractions(mutated_sol);
        }
        return mutated_sol;
    }
}
