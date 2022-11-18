package eagrn.old.algorithm.impl;

import java.util.List;

import org.uma.jmetal.algorithm.multiobjective.smpso.SMPSO;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.archive.BoundedArchive;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;

import eagrn.old.mutationwithrepair.MutationWithRepair;
import eagrn.old.mutationwithrepair.impl.NullMutationWithRepair;

public class SMPSOCorrectMutation extends SMPSO {
    private MutationWithRepair<DoubleSolution> mutation;
    private MutationWithRepair<DoubleSolution> nullMutation;

    public SMPSOCorrectMutation(DoubleProblem problem, int swarmSize, BoundedArchive<DoubleSolution> leaders,
            MutationOperator<DoubleSolution> mutationOperator, int maxIterations, double r1Min, double r1Max,
            double r2Min, double r2Max, double c1Min, double c1Max, double c2Min, double c2Max, double weightMin,
            double weightMax, double changeVelocity1, double changeVelocity2,
            SolutionListEvaluator<DoubleSolution> evaluator) {
        super(problem, swarmSize, leaders, mutationOperator, maxIterations, r1Min, r1Max, r2Min, r2Max, c1Min, c1Max, c2Min,
                c2Max, weightMin, weightMax, changeVelocity1, changeVelocity2, evaluator);
        this.mutation = (MutationWithRepair<DoubleSolution>) mutationOperator;
        this.nullMutation = new NullMutationWithRepair(mutation.getRepairer());
    }

    @Override
    protected void perturbation(List<DoubleSolution> swarm) {
        for (int i = 0; i < swarm.size(); i++) {
          if ((i % 6) == 0) {
            mutation.execute(swarm.get(i));
          } else {
            nullMutation.execute(swarm.get(i));
          }
        }
      }
}
