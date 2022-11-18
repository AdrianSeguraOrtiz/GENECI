package eagrn.fitnessfunction.impl.topology.impl;

import java.util.Map;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.impl.topology.Topology;

public class BinarizedDegreeDistribution extends Topology {
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
