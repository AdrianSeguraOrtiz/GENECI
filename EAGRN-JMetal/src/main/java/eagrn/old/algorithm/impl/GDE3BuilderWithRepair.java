package eagrn.old.algorithm.impl;

import org.uma.jmetal.algorithm.multiobjective.gde3.GDE3Builder;
import org.uma.jmetal.operator.crossover.impl.DifferentialEvolutionCrossover;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.operator.selection.impl.DifferentialEvolutionSelection;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;

import eagrn.old.mutationwithrepair.MutationWithRepair;

public class GDE3BuilderWithRepair extends GDE3Builder {
    private DoubleProblem problem;
    private MutationWithRepair<DoubleSolution> mutation;

    public GDE3BuilderWithRepair(DoubleProblem problem) {
        super(problem);
        this.problem = problem;
    }

    /* Setters */
    public GDE3BuilderWithRepair setPopulationSize(int populationSize) {
        this.populationSize = populationSize;

        return this;
    }

    public GDE3BuilderWithRepair setMaxEvaluations(int maxEvaluations) {
        this.maxEvaluations = maxEvaluations;

        return this;
    }

    public GDE3BuilderWithRepair setCrossover(DifferentialEvolutionCrossover crossover) {
        crossoverOperator = crossover;

        return this;
    }

    public GDE3BuilderWithRepair setSelection(DifferentialEvolutionSelection selection) {
        selectionOperator = selection;

        return this;
    }

    public GDE3BuilderWithRepair setSolutionSetEvaluator(SolutionListEvaluator<DoubleSolution> evaluator) {
        this.evaluator = evaluator ;

        return this ;
    }

    public GDE3BuilderWithRepair setMutation(MutationOperator<DoubleSolution> mutation) {
        this.mutation = (MutationWithRepair<DoubleSolution>)mutation;
        
        return this;
    }

    @Override
    public GDE3WithRepair build() {
        return new GDE3WithRepair(problem, populationSize, maxEvaluations, selectionOperator, crossoverOperator, evaluator, mutation);
    }
}
