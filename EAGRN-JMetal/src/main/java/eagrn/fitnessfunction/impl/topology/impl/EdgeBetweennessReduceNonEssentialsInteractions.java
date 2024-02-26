package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.topology.EdgeBetweennessCalculatorDijkstra;
import eagrn.fitnessfunction.impl.topology.Topology;

public class EdgeBetweennessReduceNonEssentialsInteractions extends Topology {
    private Map<Integer, Double> cache;
    private int decimals;
    private Map<String, Integer> geneIndexMap;

    public EdgeBetweennessReduceNonEssentialsInteractions(ArrayList<String> geneNames) {
        this.cache = new HashMap<>();
        this.decimals = Math.max(1, 4 - (int) Math.log10(geneNames.size()));
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    /**
     * Calculate the score of the given consensus and input array.
     *
     * @param consensus The consensus map.
     * @param x         The input array.
     * @return The calculated score.
     */
    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double score = 0.0;
        int key = StaticUtils.getRoundedHashCode(consensus, decimals);

        // Check if the score is already cached
        if (this.cache.containsKey(key)) {
            score = this.cache.get(key);
        } else {
            // Calculate the edge betweenness centrality
            Graph<Integer, DefaultWeightedEdge> graph = StaticUtils.getWeightedGraph(consensus, geneIndexMap, decimals, true);
            EdgeBetweennessCalculatorDijkstra edgeBetweennessCalculator = new EdgeBetweennessCalculatorDijkstra(graph);
            double[] scores = edgeBetweennessCalculator.getScores();

            // Sort the scores in ascending order
            Arrays.sort(scores);

            // Calculate the weighted mean of scores
            double mean = calculateWeightedMean(scores);

            // Calculate the score as the reciprocal of the mean
            score = 1.0 / mean;

            // Cache the score
            this.cache.put(key, score);
        }

        return score;
    }

    /**
     * Calculates the weighted mean of the given scores.
     *
     * @param scores an array of scores
     * @return the weighted mean of the scores
     */
    public static double calculateWeightedMean(double[] scores) {
        int n = scores.length;
        double weightedSum = 0;
        double sumOfWeights = 0;
        
        // Calculate the weighted sum and sum of weights
        for (int i = 0; i < n; i++) {
            double weight = (double) (n - i) / n;
            weightedSum += scores[i] * weight;
            sumOfWeights += weight;
        }

        // Calculate and return the weighted mean
        return weightedSum / sumOfWeights;
    }

}
