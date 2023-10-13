package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultWeightedEdge;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.topology.EdgeBetweennessCalculatorDijkstra;
import eagrn.fitnessfunction.impl.topology.Topology;

public class EdgeBetweennessReduceNonEssentialsInteractions extends Topology {
    private ArrayList<String> geneNames;
    private Map<Integer, Double> cache;
    private int decimals;

    public EdgeBetweennessReduceNonEssentialsInteractions(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
        this.cache = new HashMap<>();
        this.decimals = Math.max(1, 4 - (int) Math.log10(geneNames.size()));
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

        // Generate adjacency matrix from edge list
        float[][] adjacencyMatrix = StaticUtils.getFloatMatrixFromEdgeList(consensus, geneNames, decimals);

        // Generate hash code for the adjacency matrix
        int key = Arrays.deepHashCode(adjacencyMatrix);

        // Check if the score is already cached
        if (this.cache.containsKey(key)) {
            score = this.cache.get(key);
        } else {
            // Calculate edge betweenness centrality scores
            double[] scores = calculateEdgeBetweennessCentrality(adjacencyMatrix);

            // Sort the scores in ascending order
            Arrays.sort(scores);

            // Calculate the mean of the top 20% scores
            int n = (int) Math.round(scores.length * 0.2);
            double mean = calculateMean(scores, n);

            // Calculate the score as the reciprocal of the mean
            score = 1.0 / mean;

            // Cache the score
            this.cache.put(key, score);
        }

        return score;
    }

    /**
     * Calculates the edge betweenness centrality of a graph represented by an
     * adjacency matrix.
     * 
     * @param adjacencyMatrix The adjacency matrix representing the graph.
     * @return An array of edge betweenness centrality scores.
     */
    private double[] calculateEdgeBetweennessCentrality(float[][] adjacencyMatrix) {
        // Create the graph using the adjacency matrix
        Graph<Integer, DefaultWeightedEdge> graph = super.getGraphFromWeightedNetwork(adjacencyMatrix, true);

        // Calculate the edge betweenness centrality
        EdgeBetweennessCalculatorDijkstra edgeBetweennessCalculator = new EdgeBetweennessCalculatorDijkstra(graph);
        double[] scores = edgeBetweennessCalculator.getScores();

        return scores;
    }

    /**
     * Calculates the mean of the 'n' lowest values.
     * 
     * @param scores an array of scores
     * @param n      the number of lowest values to consider
     * @return the mean of the 'n' lowest values
     * @throws IllegalArgumentException if 'n' is not a valid value
     */
    public static double calculateMean(double[] scores, int n) {
        // Check if 'n' is a valid value
        if (n <= 0 || n > scores.length) {
            throw new IllegalArgumentException("The value of 'n' is not valid.");
        }

        // Create a min heap to store the 'n' lowest values
        PriorityQueue<Double> minHeap = new PriorityQueue<>();

        // Add the first 'n' values to the min heap
        for (int i = 0; i < n; i++) {
            minHeap.offer(scores[i]);
        }

        // Continue adding and removing values to maintain the 'n' lowest values in the
        // heap
        for (int i = n; i < scores.length; i++) {
            if (scores[i] < minHeap.peek()) {
                minHeap.poll();
                minHeap.offer(scores[i]);
            }
        }

        // Calculate the sum of the 'n' lowest values
        double sum = 0;
        for (double value : minHeap) {
            sum += value;
        }

        // Calculate the mean by dividing the sum by 'n'
        return sum / n;
    }

}
