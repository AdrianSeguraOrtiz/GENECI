package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

public class MinConfCriteria implements CutOffCriteria {
    private final double min;
    private ArrayList<String> geneNames;

    public MinConfCriteria(double min, ArrayList<String> geneNames) {
        this.min = min;
        this.geneNames = geneNames;
    }

    public int[][] getNetwork(Map<String, Double> links) {
        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        int g1, g2;

        for (Map.Entry<String, Double> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue();
            if (conf > min) {
                String[] parts = pair.split(";");
                if (parts.length > 1) {
                    g1 = geneNames.indexOf(parts[0]);
                    g2 = geneNames.indexOf(parts[1]);
                    if (g1 != -1 && g2 != -1) {
                        network[g1][g2] = 1;
                    }
                }
            }
        }

        return network;
    }

    @Override
    public Map<String, Double> getCutMap(Map<String, Double> links) {
        Map<String, Double> res = new HashMap<>();

        for (Map.Entry<String, Double> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue();
            if (conf > min) {
                res.put(pair, conf);
            }
        }

        return res;
    }
}