package eagrn.algorithm;

import java.util.List;
import org.uma.jmetal.util.termination.Termination;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.parallel.asynchronous.task.ParallelTask;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.archive.Archive;
import org.uma.jmetal.util.archive.impl.NonDominatedSolutionListArchive;

public class AsynchronousMultiThreadedNSGAIIGoodParentsExternalFile<S extends Solution<?>>
    extends AsynchronousMultiThreadedNSGAIIGoodParents<S> {

  protected Archive<S> externalArchive;

  public AsynchronousMultiThreadedNSGAIIGoodParentsExternalFile(
      int numberOfCores,
      Problem<S> problem,
      int populationSize,
      CrossoverOperator<S> crossover,
      MutationOperator<S> mutation,
      Termination termination) {
    super(numberOfCores, problem, populationSize, crossover, mutation, termination);

    externalArchive = new BestSolutionsArchive<>(new NonDominatedSolutionListArchive<>(),
        populationSize);
  }

  @Override
  public void processComputedTask(ParallelTask<S> task) {
    externalArchive.add(task.getContents());
    super.processComputedTask(task);
  }

  @Override
  public List<S> getResult() {
    return externalArchive.getSolutionList();
  }
}
