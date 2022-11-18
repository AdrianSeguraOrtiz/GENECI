package eagrn.old.mutationwithrepair.impl;

import eagrn.old.mutationwithrepair.MutationWithRepair;
import eagrn.old.repairer.WeightRepairer;

import org.uma.jmetal.operator.mutation.impl.CDGMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class CDGMutationWithRepair extends CDGMutation implements MutationWithRepair<DoubleSolution> {
    private WeightRepairer repairer;

    public CDGMutationWithRepair(double mutationProbability, double delta, WeightRepairer repairer) {
        super(mutationProbability, delta);
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
