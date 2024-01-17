package eagrn.operator.repairer.impl;

import eagrn.operator.repairer.WeightRepairer;

import java.util.Map;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

public class StandardizationRepairer extends WeightRepairer {

    public StandardizationRepairer(String strKnownInteractionsFile, Map<String, Double[]> inferredNetworks, String distanceType, double memeticPropability) {
        super(strKnownInteractionsFile, inferredNetworks, distanceType, memeticPropability);
    }

    /** RepairSolution() method */
    @Override
    public void repairSolutionOnly(DoubleSolution solution) {
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

    @Override
    public void repairSolutionWithKnownInteractions(DoubleSolution solution) {
        if (knownInteractionsMap == null) {
            throw new IllegalArgumentException("Known interactions file is not provided");
        }
        int numTecs = solution.variables().size();
        double[] x = new double[numTecs];
        double sum = 0;
        for (int i = 0; i < numTecs; i++) {
            x[i] = solution.variables().get(i);
            sum += x[i];
        }
        DoubleSolution resSolution = (DoubleSolution) solution.copy();
        double minDistance = Double.MAX_VALUE;
        for (int i = -1; i < numTecs; i++) {
            DoubleSolution tmpSolution = (DoubleSolution) solution.copy();
            if (i != -1) tmpSolution.variables().set(i, x[i] + (1.0/numTecs * sum));
            
            repairSolutionOnly(tmpSolution);
            double[] y = new double[numTecs];
            for (int j = 0; j < numTecs; j++) {
                y[j] = tmpSolution.variables().get(j);
            }

            double tmpDistance = distance(getConfConsensusMap(y));
            if (tmpDistance < minDistance) {
                minDistance = tmpDistance;
                resSolution = tmpSolution;
            }
        }
        solution.variables().clear();
        solution.variables().addAll(resSolution.variables());
    }
}
