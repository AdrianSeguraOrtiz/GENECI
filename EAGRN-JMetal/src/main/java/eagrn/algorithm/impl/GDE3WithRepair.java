package eagrn.algorithm.impl;

import java.util.ArrayList;
import java.util.List;

import org.uma.jmetal.algorithm.multiobjective.gde3.GDE3;
import org.uma.jmetal.operator.crossover.impl.DifferentialEvolutionCrossover;
import org.uma.jmetal.operator.selection.impl.DifferentialEvolutionSelection;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;

import eagrn.operator.mutationwithrepair.MutationWithRepair;

public class GDE3WithRepair extends GDE3 {
    private MutationWithRepair<DoubleSolution> mutation;

    public GDE3WithRepair(DoubleProblem problem, int populationSize, int maxEvaluations,
            DifferentialEvolutionSelection selection, DifferentialEvolutionCrossover crossover,
            SolutionListEvaluator<DoubleSolution> evaluator, MutationWithRepair<DoubleSolution> mutation) {
        super(problem, populationSize, maxEvaluations, selection, crossover, evaluator);
        this.mutation = mutation;
    }

    @Override
    protected List<DoubleSolution> reproduction(List<DoubleSolution> matingPopulation) {
        List<DoubleSolution> offspringPopulation = super.reproduction(matingPopulation);
        List<DoubleSolution> repairedPopulation = new ArrayList<>();

        for (int i = 0; i < offspringPopulation.size(); i++) {
            repairedPopulation.add(mutation.execute(offspringPopulation.get(i)));
        }

        return repairedPopulation;
    }
}
