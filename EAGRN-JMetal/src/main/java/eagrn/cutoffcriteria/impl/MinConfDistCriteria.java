package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.ArrayList;
import java.util.Map;

public class MinConfDistCriteria implements CutOffCriteria {
    private final double min;

    public MinConfDistCriteria(double min) {
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
        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        int g1, g2;

        for (Map.Entry<String, ConsensusTuple> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue().getConf();
            double dist = entry.getValue().getDist();
            double confDist = (conf + (1 - dist)) / 2.0;
            if (confDist > min) {
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

}
