package operator.repairer.impl;

import operator.repairer.WeightRepairer;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

public class GreedyRepairer implements WeightRepairer {

    /** RepairSolution() method */
    @Override
    public void repairSolution(DoubleSolution solution) {
        double v, sum = 0;
        int pos = -1;
        int numVariables = solution.variables().size();
        int randInitialPos = (int) (Math.random() * (numVariables - 1));

        int cnt = 0;
        while (cnt < numVariables && sum <= 1) {
            pos = cnt + randInitialPos;
            if (pos >= numVariables) pos -= numVariables;

            v = solution.variables().get(pos);
            sum += v;
        }

        if (sum > 1) {
            for (int i = 0; i < numVariables; i++) {
                v = solution.variables().get(i);
                solution.variables().set(i, v);
            }
        } else {
            int lastPos;
            if (randInitialPos == 0) lastPos = numVariables - 1;
            else lastPos = randInitialPos - 1;

            v = solution.variables().get(lastPos);
            solution.variables().set(lastPos, v + 1 - sum);
        }
    }
}
