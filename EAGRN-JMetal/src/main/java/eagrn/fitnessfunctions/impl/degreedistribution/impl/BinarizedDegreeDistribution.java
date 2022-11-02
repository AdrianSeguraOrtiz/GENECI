package eagrn.fitnessfunctions.impl.degreedistribution.impl;

import java.util.Map;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.impl.degreedistribution.DegreeDistribution;

public class BinarizedDegreeDistribution extends DegreeDistribution {
    private CutOffCriteria cutOffCriteria;
    private int numberOfNodes;

    public BinarizedDegreeDistribution(int numberOfNodes, CutOffCriteria cutOffCriteria) {
        this.cutOffCriteria = cutOffCriteria;
        this.numberOfNodes = numberOfNodes;
    }

    public double run(Map<String, Double> consensus, Double[] x) {
        
        int[][] binaryNetwork = cutOffCriteria.getNetwork(consensus);
        double[] undirectedDegreesPlusOne = new double[this.numberOfNodes];

        for (int i = 0; i < this.numberOfNodes; i++) {
            undirectedDegreesPlusOne[i] = 1;
            for (int j = 0; j < this.numberOfNodes; j++) {
                undirectedDegreesPlusOne[i] += binaryNetwork[i][j] + binaryNetwork[j][i];
            }
        }

        return -super.paretoTest(undirectedDegreesPlusOne);
    }
}
