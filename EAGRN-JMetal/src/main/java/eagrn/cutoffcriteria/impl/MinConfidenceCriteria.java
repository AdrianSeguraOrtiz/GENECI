package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.ArrayList;
import java.util.Map;

public class MinConfidenceCriteria implements CutOffCriteria {
    private double minConfidence;

    public MinConfidenceCriteria (double minConfidence) {
        this.minConfidence = minConfidence;
    }

    @Override
    public int[][] getNetworkFromConsensusList (Map<String, ConsensusTuple> consensus, ArrayList<String> geneNames) {
        /**
         * Construct the Boolean matrix by setting a minimum confidence value as a cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        int row, col;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            if (pair.getValue().getConf() > minConfidence) {
                String [] vKeySplit = pair.getKey().split("-");
                row = geneNames.indexOf(vKeySplit[0]);
                col = geneNames.indexOf(vKeySplit[1]);
                network[row][col] = 1;
                network[col][row] = 1;
            }
        }

        return network;
    }

    @Override
    public int[][] getNetworkFromList (Map<String, Double> map, ArrayList<String> geneNames) {
        /**
         * Construct the Boolean matrix by setting a minimum confidence value as a cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        int row, col;
        for (Map.Entry<String, Double> pair : map.entrySet()) {
            if (pair.getValue() > minConfidence) {
                String [] vKeySplit = pair.getKey().split("-");
                row = geneNames.indexOf(vKeySplit[0]);
                col = geneNames.indexOf(vKeySplit[1]);
                network[row][col] = 1;
                network[col][row] = 1;
            }
        }

        return network;
    }
}
