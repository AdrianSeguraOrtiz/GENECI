package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.EdgeBetweennessCentrality;
import org.jgrapht.graph.DefaultEdge;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.topology.Topology;

public class EdgeBetweennessReduceNonEssentialsInteractions extends Topology {
    private ArrayList<String> geneNames;
    private Map<Integer, Double> cache;
    private int decimals;

    public EdgeBetweennessReduceNonEssentialsInteractions(ArrayList<String> geneNames){
        this.geneNames = geneNames;
        this.cache = new HashMap<>();
        this.decimals = Math.max(1, 4 - (int) Math.log10(geneNames.size()));
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        double score = 0.0;
        double[][] adjacencyMatrix = StaticUtils.getMatrixFromEdgeList(consensus, geneNames, decimals);
        int key = Arrays.deepHashCode(adjacencyMatrix);

        if (this.cache.containsKey(key)){
            score = this.cache.get(key);
        } else {
            Graph<String, DefaultEdge> graph = super.getGraphFromWeightedNetwork(adjacencyMatrix, geneNames, true);
            EdgeBetweennessCentrality<String, DefaultEdge> evaluator = new EdgeBetweennessCentrality<>(graph);
            Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
            
            Arrays.sort(scores);
            int n = (int) Math.round(scores.length * 0.2);
            double sum = 0;
            for (int i = 0; i < n ; i++) {
                sum += scores[i];
            }
            double mean = sum / (double)n;

            score = 1.0 / mean;
            this.cache.put(key, score);
        }

        return score;
    }
    
}
