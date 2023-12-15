package eagrn.cutoffcriteria.impl;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.util.*;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleGraph;

public class MinConfCriteria implements CutOffCriteria {
    private final float min;
    private Map<String, Integer> geneIndexMap;

    public MinConfCriteria(float min, ArrayList<String> geneNames) {
        this.min = min;
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    @Override
    public boolean[][] getBooleanMatrix(Map<String, Float> links) {
        int numberOfNodes = geneIndexMap.size();
        boolean[][] network = new boolean[numberOfNodes][numberOfNodes];

        int g1, g2;
        for (Map.Entry<String, Float> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue();
            if (conf > min) {
                String[] parts = pair.split(";");
                if (parts.length > 1) {
                    g1 = geneIndexMap.get(parts[0]);
                    g2 = geneIndexMap.get(parts[1]);
                    if (g1 != -1 && g2 != -1) {
                        network[g1][g2] = true;
                    }
                }
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

        int g1, g2;
        for (Map.Entry<String, Float> entry : links.entrySet()) {
            String pair = entry.getKey();
            double conf = entry.getValue();
            if (conf > min) {
                String[] parts = pair.split(";");
                if (parts.length > 1) {
                    g1 = geneIndexMap.get(parts[0]);
                    g2 = geneIndexMap.get(parts[1]);
                    if (g1 != g2) {
                        graph.addEdge(g1, g2);
                    }
                }
            }
        }

        return graph;
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