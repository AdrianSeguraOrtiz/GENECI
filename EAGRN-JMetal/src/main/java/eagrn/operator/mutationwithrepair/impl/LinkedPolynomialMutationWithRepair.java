package eagrn.operator.mutationwithrepair.impl;

import eagrn.operator.mutationwithrepair.MutationWithRepair;
import eagrn.operator.repairer.WeightRepairer;
import org.uma.jmetal.operator.mutation.impl.LinkedPolynomialMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class LinkedPolynomialMutationWithRepair extends LinkedPolynomialMutation implements MutationWithRepair<DoubleSolution> {
    private WeightRepairer repairer;

    public LinkedPolynomialMutationWithRepair(double mutationProbability, double distributionIndex, WeightRepairer repairer) {
        super(mutationProbability, distributionIndex);
        this.repairer = repairer;
    }

    @Override
    public DoubleSolution execute(DoubleSolution solution) throws JMetalException {
        DoubleSolution mutated_sol = super.execute(solution);
        repairer.repairSolution(mutated_sol);
        return mutated_sol;
    }
    
    @Override
    public WeightRepairer getRepairer() {
        return repairer;
    }
}
