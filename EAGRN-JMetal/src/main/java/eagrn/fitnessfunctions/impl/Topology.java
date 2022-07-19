package eagrn.fitnessfunctions.impl;

import java.util.ArrayList;
import java.util.Map;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.FitnessFunction;

/**
 * The aim is to minimize the number of nodes whose degree is higher than the 
 * average while trying to maximize the degree of these nodes.
 */

public class Topology implements FitnessFunction {
    private ArrayList<String> geneNames;
    private CutOffCriteria cutOffCriteria;
    private int numberOfNodes;

    public Topology (ArrayList<String> geneNames, CutOffCriteria cutOffCriteria) {
        this.geneNames = geneNames;
        this.cutOffCriteria = cutOffCriteria;
        this.numberOfNodes = geneNames.size();
    }

    public double run(Map<String, ConsensusTuple> consensus) {
        
        int[][] binaryNetwork = cutOffCriteria.getNetworkFromConsensus(consensus, this.geneNames);
        int[] degrees = new int[this.numberOfNodes];

        for (int i = 0; i < this.numberOfNodes; i++) {
            for (int j = 0; j < this.numberOfNodes; j++) {
                degrees[i] += binaryNetwork[i][j];
            }
        }

        int sum = 0;
        for (int i = 0; i < this.numberOfNodes; i++) {
            sum += degrees[i];
        }
        double mean = (double) sum/this.numberOfNodes;

        int hubs = 0;
        int hubsDegreesSum = 0;
        for (int i = 0; i < this.numberOfNodes; i++) {
            if (degrees[i] > mean) {
                hubs += 1;
                hubsDegreesSum += degrees[i];
            } 
        }

        double f1 = Math.abs(hubs - 0.1 * this.numberOfNodes)/((1 - 0.1) * this.numberOfNodes);
        double f2 = 1.0;
        if (hubs > 0) f2 = 1.0 - (double) (hubsDegreesSum/hubs)/(this.numberOfNodes - 1);
        double fitness = (f1 + f2)/2;

        return fitness;
    }
}
