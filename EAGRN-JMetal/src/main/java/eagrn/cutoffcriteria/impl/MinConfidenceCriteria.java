package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteriaOnlyConf;

import java.util.ArrayList;
import java.util.Map;
import java.util.stream.Collectors;

public class MinConfidenceCriteria implements CutOffCriteriaOnlyConf {
    private final double min;

    public MinConfidenceCriteria(double min) {
        this.min = min;
    }

    /**
     * TODO.
     *
     * @param links TODO.
     * @param geneNames TODO.
     * @return TODO.
     */
    public int[][] getNetworkFromConsensus(Map<String, ConsensusTuple> links, ArrayList<String> geneNames) {
        Map<String, Double> result = links
                .entrySet()
                .stream()
                .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().getConf()));
        return getNetwork(result, geneNames);
    }

    /**
     * TODO.
     *
     * @param links TODO.
     * @param geneNames TODO.
     * @return TODO.
     */
    public int[][] getNetwork(Map<String, Double> links, ArrayList<String> geneNames) {
        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        int g1, g2;

        for (Map.Entry<String, Double> entry : links.entrySet()) {
            String pair = entry.getKey();
            Double conf = entry.getValue();
            if (conf > min) {
                String[] parts = pair.split("-");
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
}