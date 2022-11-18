package eagrn.old.mutationwithrepair;

import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.solution.Solution;

import eagrn.old.repairer.WeightRepairer;

public interface MutationWithRepair<S extends Solution<?>> extends MutationOperator<S> {
    WeightRepairer getRepairer();
}
