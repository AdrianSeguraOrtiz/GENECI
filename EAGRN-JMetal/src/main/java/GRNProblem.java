import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;

import java.util.ArrayList;
import java.util.List;

public class GRNProblem extends AbstractDoubleProblem {

    /** Constructor Creates a default instance of the GRN problem */
    public GRNProblem() {
        setNumberOfVariables(3);
        setNumberOfObjectives(2);
        setName("GRNProblem");

        List<Double> lowerLimit = new ArrayList<>(getNumberOfVariables()) ;
        List<Double> upperLimit = new ArrayList<>(getNumberOfVariables()) ;

        for (int i = 0; i < getNumberOfVariables(); i++) {
            lowerLimit.add(0.0);
            upperLimit.add(1.0);
        }

        setVariableBounds(lowerLimit, upperLimit);
    }

    /** CreateSolution() method */
    @Override
    public DoubleSolution createSolution() {
        DefaultDoubleSolution solution = new DefaultDoubleSolution(this.getNumberOfObjectives(), this.getNumberOfConstraints(), this.getBoundsForVariables());
        WeightRepairer repairer = new WeightRepairer();
        repairer.repairSolution(solution);
        return solution;
    }

    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {
        double[] fx = new double[solution.objectives().length];
        double[] x = new double[getNumberOfVariables()];
        for (int i = 0; i < getNumberOfVariables(); i++) {
            x[i] = solution.variables().get(i);
        }

        fx[0] = fitnessF1(x);
        fx[1] = fitnessF2(x);

        solution.objectives()[0] = fx[0];
        solution.objectives()[1] = fx[1];

        return solution;
    }

    /** FitnessF1() method */
    public double fitnessF1(double[] weights) {
        double max = Double.NEGATIVE_INFINITY;
        for(double cur: weights)
            max = Math.max(max, cur);

        return -1 * max;
    }

    /** FitnessF2() method */
    public double fitnessF2(double[] weights) {
        double min = Double.POSITIVE_INFINITY;
        for(double cur: weights)
            min = Math.min(min, cur);

        return min;
    }

}
