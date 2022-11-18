package eagrn.old.repairer.impl;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.old.repairer.WeightRepairer;

public class StandardizationRepairer implements WeightRepairer {

    /** RepairSolution() method */
    @Override
    public void repairSolution(DoubleSolution solution) {
        double v, sum = 0;

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            sum += v;
        }

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            v = Math.round(v/sum * 10000.0) / 10000.0;
            solution.variables().set(i, v);
        }
    }
}
