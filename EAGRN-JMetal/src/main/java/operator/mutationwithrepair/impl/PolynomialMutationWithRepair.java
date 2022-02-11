package operator.mutationwithrepair.impl;

import operator.repairer.WeightRepairer;
import org.uma.jmetal.operator.mutation.impl.PolynomialMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class PolynomialMutationWithRepair extends PolynomialMutation {
    private WeightRepairer repairer;

    public PolynomialMutationWithRepair (double mutationProbability, double distributionIndex, WeightRepairer repairer) {
        super(mutationProbability, distributionIndex);
        this.repairer = repairer;
    }

    @Override
    public DoubleSolution execute(DoubleSolution solution) throws JMetalException {
        DoubleSolution mutated_sol = super.execute(solution);
        repairer.repairSolution(mutated_sol);
        return mutated_sol;
    }
}
