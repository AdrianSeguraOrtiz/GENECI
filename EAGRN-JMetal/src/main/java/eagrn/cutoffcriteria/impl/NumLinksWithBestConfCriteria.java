package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleGraph;

public class NumLinksWithBestConfCriteria implements CutOffCriteria {
    private final int max;
    private Map<String, Integer> geneIndexMap;

    public NumLinksWithBestConfCriteria(int max, ArrayList<String> geneNames) {
        this.max = max;
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    @Override
    public boolean[][] getBooleanMatrix (Map<String, Float> links) {
        int numberOfNodes = geneIndexMap.size();
        boolean[][] network = new boolean[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Float>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Float>> iterator = list.iterator();

        int g1, g2, cnt = 0;
        while (cnt < max) {
            String pair = iterator.next().getKey();
            String [] parts = pair.split(";");
            if (parts.length > 1) {
                g1 = geneIndexMap.get(parts[0]);
                g2 = geneIndexMap.get(parts[1]);
                if (g1 != -1 && g2 != -1) {
                    network[g1][g2] = true;
                }
                cnt += 1;
            }
        }

        return network;
    }

    @Override
    public Graph<Integer, DefaultEdge> getBooleanGraph (Map<String, Float> links, boolean directed) {
        Graph<Integer, DefaultEdge> graph = directed ? new SimpleDirectedGraph<>(DefaultEdge.class) : new SimpleGraph<>(DefaultEdge.class);

        for (int i = 0; i < geneIndexMap.size(); i++) {
            graph.addVertex(i);
        }

        List<Map.Entry<String, Float>> list = new ArrayList<>(links.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        Iterator<Map.Entry<String, Float>> iterator = list.iterator();

        int g1, g2, cnt = 0;
        while (cnt < max) {
            String pair = iterator.next().getKey();
            String [] parts = pair.split(";");
            if (parts.length > 1) {
                g1 = geneIndexMap.get(parts[0]);
                g2 = geneIndexMap.get(parts[1]);
                if (g1 != g2) {
                    graph.addEdge(g1, g2);
                }
                cnt += 1;
            }
        }

        return graph;
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
