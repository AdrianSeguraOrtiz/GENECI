package operator.mutationwithrepair.impl;

import operator.repairer.WeightRepairer;
import org.uma.jmetal.operator.mutation.impl.UniformMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class UniformMutationWithRepair extends UniformMutation {
    private WeightRepairer repairer;

    public UniformMutationWithRepair(double mutationProbability, double perturbation, WeightRepairer repairer) {
        super(mutationProbability, perturbation);
        this.repairer = repairer;
    }

    @Override
    public DoubleSolution execute(DoubleSolution solution) throws JMetalException {
        DoubleSolution mutated_sol = super.execute(solution);
        repairer.repairSolution(mutated_sol);
        return mutated_sol;
    }
}
