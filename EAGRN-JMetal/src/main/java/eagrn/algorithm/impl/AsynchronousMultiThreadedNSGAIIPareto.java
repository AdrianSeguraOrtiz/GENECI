package eagrn.algorithm.impl;

import java.util.List;

import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.parallel.asynchronous.algorithm.impl.AsynchronousMultiThreadedNSGAII;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.SolutionListUtils;
import org.uma.jmetal.util.termination.Termination;

public class AsynchronousMultiThreadedNSGAIIPareto<S extends Solution<?>> extends AsynchronousMultiThreadedNSGAII<S> {

    public AsynchronousMultiThreadedNSGAIIPareto(int numberOfCores, Problem<S> problem, int populationSize,
            CrossoverOperator<S> crossover, MutationOperator<S> mutation, Termination termination) {
        super(numberOfCores, problem, populationSize, crossover, mutation, termination);
    }

    @Override
    public List<S> getResult() {
        return SolutionListUtils.getNonDominatedSolutions(super.getResult());
    }
    
}
