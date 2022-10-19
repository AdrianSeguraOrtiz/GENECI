package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

public class NumLinksWithBestConfCriteria implements CutOffCriteria {
    private final int max;
    private ArrayList<String> geneNames;

    public NumLinksWithBestConfCriteria(int max, ArrayList<String> geneNames) {
        this.max = max;
        this.geneNames = geneNames;
    }

    /**
     * TODO.
     *
     * @param links TODO.
     * @param geneNames TODO.
     * @return TODO.
     */
    public int[][] getNetwork (Map<String, Double> links) {
        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Double>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Double>> iterator = list.iterator();

        int g1, g2, cnt = 0;
        while (cnt < max) {
            String pair = iterator.next().getKey();
            String [] parts = pair.split(";");
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
