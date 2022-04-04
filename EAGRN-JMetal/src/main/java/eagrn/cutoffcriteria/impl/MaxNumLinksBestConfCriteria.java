package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteriaOnlyConf;

import java.util.*;
import java.util.stream.Collectors;

public class MaxNumLinksBestConfCriteria implements CutOffCriteriaOnlyConf {
    private final int max;

    public MaxNumLinksBestConfCriteria(int max) {
        this.max = max;
    }

    /**
     * TODO.
     *
     * @param links TODO.
     * @param geneNames TODO.
     * @return TODO.
     */
    public int[][] getNetworkFromConsensus (Map<String, ConsensusTuple> links, ArrayList<String> geneNames) {
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
    public int[][] getNetwork (Map<String, Double> links, ArrayList<String> geneNames) {
        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Double>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Double>> iterator = list.iterator();

        int g1, g2, cnt = 0;
        while (cnt < max) {
            String pair = iterator.next().getKey();
            String [] parts = pair.split("-");
            if (parts.length > 1) {
                g1 = geneNames.indexOf(parts[0]);
                g2 = geneNames.indexOf(parts[1]);
                if (g1 != -1 && g2 != -1) {
                    network[g1][g2] = 1;
                }
                cnt += 1;
            }
        }

        return network;
    }
}
