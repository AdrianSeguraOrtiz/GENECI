package eagrn.operator.mutationwithrepair.impl;

import eagrn.operator.repairer.WeightRepairer;
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
        DoubleSolution initialSolution = (DoubleSolution) solution.copy();
        super.execute(solution);
        if (solution.variables().equals(initialSolution.variables())) {
            repairer.repairSolutionOnly(solution);
            System.out.println("No Memetico");
        } else {
            repairer.repairSolutionWithKnownInteractions(solution);
            System.out.println("Memetico");
        }
        return solution;
    }
}
