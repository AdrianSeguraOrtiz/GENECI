package eagrn.operator.repairer.impl;

import eagrn.operator.repairer.WeightRepairer;

import java.util.Map;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

public class GreedyRepairer extends WeightRepairer {

    public GreedyRepairer(String strKnownInteractionsFile, Map<String, Double[]> inferredNetworks, String distanceType, double memeticPropability) {
        super(strKnownInteractionsFile, inferredNetworks, distanceType, memeticPropability);
    }

    /** RepairSolution() method */
    @Override
    public void repairSolutionOnly(DoubleSolution solution) {
        double v = 0, sum = 0;
        int pos = -1;
        int numVariables = solution.variables().size();
        int randInitialPos = getRandomPos(numVariables);

        int cnt = 0;
        while (cnt < numVariables && sum <= 1) {
            pos = cnt + randInitialPos;
            if (pos >= numVariables) pos -= numVariables;

            v = solution.variables().get(pos);
            v = Math.round(v * 10000.0) / 10000.0;
            solution.variables().set(pos, v);

            sum += v;
            cnt += 1;
        }

        int lastPos;
        if (randInitialPos == 0) lastPos = numVariables - 1;
        else lastPos = randInitialPos - 1;

        if (sum > 1) {
            v = Math.round((v - (sum - 1)) * 10000.0) / 10000.0;
            solution.variables().set(pos, v);

            while (pos != lastPos) {
                pos = cnt + randInitialPos;
                if (pos >= numVariables) pos -= numVariables;

                solution.variables().set(pos, 0.0);
                cnt += 1;
            }
        } else {
            v = solution.variables().get(lastPos);
            v = Math.round((v + 1 - sum) * 10000.0) / 10000.0;
            solution.variables().set(lastPos, v);
        }
    }

    public int getRandomPos(int numVariables) {
        return (int) (Math.random() * (numVariables - 1));
    }

    @Override
    public void repairSolutionWithKnownInteractions(DoubleSolution solution) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'repairSolutionWithKnownInteractions'");
    }
}
