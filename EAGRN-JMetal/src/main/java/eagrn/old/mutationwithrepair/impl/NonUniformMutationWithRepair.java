package eagrn.old.mutationwithrepair.impl;

import eagrn.old.mutationwithrepair.MutationWithRepair;
import eagrn.old.repairer.WeightRepairer;

import org.uma.jmetal.operator.mutation.impl.NonUniformMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class NonUniformMutationWithRepair extends NonUniformMutation implements MutationWithRepair<DoubleSolution> {
    private WeightRepairer repairer;

    public NonUniformMutationWithRepair(double mutationProbability, double perturbation, int maxIterations, WeightRepairer repairer) {
        super(mutationProbability, perturbation, maxIterations);
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
