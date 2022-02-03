import org.uma.jmetal.operator.mutation.impl.PolynomialMutation;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class PolynomialMutationWithRepair extends PolynomialMutation {

    public PolynomialMutationWithRepair (double mutationProbability, double distributionIndex) {
        super(mutationProbability, distributionIndex);
    }

    @Override
    public DoubleSolution execute(DoubleSolution solution) throws JMetalException {
        DoubleSolution mutated_sol = super.execute(solution);
        repairSolution(mutated_sol);
        return mutated_sol;
    }

    private void repairSolution(DoubleSolution solution) {
        double v, sum = 0;

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            sum += v;
        }

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            v /= sum;
            solution.variables().set(i, v);
        }
    }
}
