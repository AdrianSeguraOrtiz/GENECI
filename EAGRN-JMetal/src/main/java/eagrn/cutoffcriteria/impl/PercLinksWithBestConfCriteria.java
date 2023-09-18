package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

public class PercLinksWithBestConfCriteria implements CutOffCriteria {
    private final int max;
    private ArrayList<String> geneNames;

    public PercLinksWithBestConfCriteria(float perc, ArrayList<String> geneNames) {
        int numberOfNodes = geneNames.size();
        int maxPossibleLinks = numberOfNodes * (numberOfNodes - 1);
        this.max = (int)Math.round(perc * Double.valueOf(maxPossibleLinks));
        this.geneNames = geneNames;
    }

    public boolean[][] getNetwork (Map<String, Float> links) {
        int numberOfNodes = geneNames.size();
        boolean[][] network = new boolean[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Float>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Float>> iterator = list.iterator();

        int g1, g2, cnt = 0;
        while (cnt < max) {
            String pair = iterator.next().getKey();
            String [] parts = pair.split(";");
            if (parts.length > 1) {
                g1 = geneNames.indexOf(parts[0]);
                g2 = geneNames.indexOf(parts[1]);
                if (g1 != -1 && g2 != -1) {
                    network[g1][g2] = true;
                }
                cnt += 1;
            }
        }

        return network;
    }

    @Override
    public Map<String, Float> getCutMap(Map<String, Float> links) {
        Map<String, Float> res = new HashMap<>();

        List<Map.Entry<String, Float>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Float>> iterator = list.iterator();

        int cnt = 0;
        while (cnt < max) {
            Map.Entry<String, Float> entry = iterator.next();
            res.put(entry.getKey(), entry.getValue());
            cnt += 1;
        }

        return res;
    }
}
