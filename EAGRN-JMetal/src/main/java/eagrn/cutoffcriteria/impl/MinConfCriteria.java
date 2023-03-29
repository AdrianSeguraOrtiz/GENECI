package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

public class MinConfCriteria implements CutOffCriteria {
    private final float min;
    private ArrayList<String> geneNames;

    public MinConfCriteria(float min, ArrayList<String> geneNames) {
        this.min = min;
        this.geneNames = geneNames;
    }

    public boolean[][] getNetwork(Map<String, Float> links) {
        int numberOfNodes = geneNames.size();
        boolean[][] network = new boolean[numberOfNodes][numberOfNodes];

        int g1, g2;

        for (Map.Entry<String, Float> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue();
            if (conf > min) {
                String[] parts = pair.split(";");
                if (parts.length > 1) {
                    g1 = geneNames.indexOf(parts[0]);
                    g2 = geneNames.indexOf(parts[1]);
                    if (g1 != -1 && g2 != -1) {
                        network[g1][g2] = true;
                    }
                }
            }
        }

        return network;
    }

    @Override
    public Map<String, Float> getCutMap(Map<String, Float> links) {
        Map<String, Float> res = new HashMap<>();

        for (Map.Entry<String, Float> entry : links.entrySet()) {
            String pair = entry.getKey();
            float conf = entry.getValue();
            if (conf > min) {
                res.put(pair, conf);
            }
        }

        return res;
    }
}