package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.apache.commons.lang.ArrayUtils;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.PageRank;
import org.jgrapht.graph.DefaultWeightedEdge;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.topology.Topology;

public class PageRankDistribution extends Topology {
    private Map<Integer, Double> cache;
    private int decimals;
    private Map<String, Integer> geneIndexMap;

    public PageRankDistribution(ArrayList<String> geneNames){
        this.cache = new HashMap<>();
        this.decimals = Math.max(1, 4 - (int) Math.log10(geneNames.size()));
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double score = 0.0;
        Graph<Integer, DefaultWeightedEdge> graph = StaticUtils.getWeightedGraph(consensus, geneIndexMap, decimals, true);
        int key = graph.hashCode();

        if (this.cache.containsKey(key)){
            score = this.cache.get(key);
        } else {
            PageRank<Integer, DefaultWeightedEdge> evaluator = new PageRank<>(graph);
            Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
            for (int i = 0; i < scores.length; i++) {
                scores[i] += 1;
            }
            score = super.paretoTest(ArrayUtils.toPrimitive(scores));
            this.cache.put(key, score);
        }

        return score;
    }
    
}
