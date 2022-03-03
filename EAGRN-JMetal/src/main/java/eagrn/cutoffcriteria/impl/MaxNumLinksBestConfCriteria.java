package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class MaxNumLinksBestConfCriteria implements CutOffCriteria {
    private int maxNumLinks;

    public MaxNumLinksBestConfCriteria (int maxNumLinks) {
        this.maxNumLinks = maxNumLinks;
    }

    @Override
    public int[][] getNetworkFromConsensusList (Map<String, ConsensusTuple> consensus, ArrayList<String> geneNames) {
        /**
         * Constructs the Boolean matrix by setting a maximum number of links as the cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, ConsensusTuple>> list = new ArrayList<>(consensus.entrySet());
        list.sort(Map.Entry.comparingByValue());

        Iterator<Map.Entry<String, ConsensusTuple>> iterator = list.iterator();
        int row, col, cnt = 0;
        while (cnt < maxNumLinks) {
            String [] vKeySplit = iterator.next().getKey().split("-");
            row = geneNames.indexOf(vKeySplit[0]);
            col = geneNames.indexOf(vKeySplit[1]);
            network[row][col] = 1;
            network[col][row] = 1;
            cnt += 1;
        }

        return network;
    }

    @Override
    public int[][] getNetworkFromList (Map<String, Double> map, ArrayList<String> geneNames) {
        /**
         * Constructs the Boolean matrix by setting a maximum number of links as the cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Double>> list = new ArrayList<>(map.entrySet());

        Iterator<Map.Entry<String, Double>> iterator = list.iterator();
        int row, col, cnt = 0;
        while (cnt < maxNumLinks) {
            String [] vKeySplit = iterator.next().getKey().split("-");
            row = geneNames.indexOf(vKeySplit[0]);
            col = geneNames.indexOf(vKeySplit[1]);
            network[row][col] = 1;
            network[col][row] = 1;
            cnt += 1;
        }

        return network;
    }
}
