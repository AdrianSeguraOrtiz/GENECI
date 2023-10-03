package eagrn.fitnessfunction.impl.topology;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jheaps.AddressableHeap;
import org.jheaps.tree.PairingHeap;

public class EdgeBetweennessCalculatorDijkstra {
    private final Graph<Integer, DefaultWeightedEdge> graph;
    protected Deque<Integer> stack = new ArrayDeque<>();
    protected Map<DefaultWeightedEdge, Double> scores = new HashMap<>();

    public EdgeBetweennessCalculatorDijkstra(Graph<Integer, DefaultWeightedEdge> graph) {
        this.graph = graph;
    }

    /**
     * Updates a single vertex in the graph using Dijkstra's algorithm.
     *
     * @param source The source vertex to start the update from.
     */
    private void singleVertexUpdate(Integer source) {
        // Maintain a map of predecessors for each vertex
        Map<Integer, List<DefaultWeightedEdge>> predecessors = new HashMap<>();
        // Maintain a map of distances for each vertex
        Map<Integer, AddressableHeap.Handle<Double, Integer>> distances = new HashMap<>();
        // Maintain a map of sigma values for each vertex
        Map<Integer, Long> sigma = new HashMap<>();
        // Create a heap to store the distances
        AddressableHeap<Double, Integer> heap = new PairingHeap<>();

        // Initialize sigma values for all vertices to 0
        for (Integer vertex : graph.vertexSet()) {
            sigma.put(vertex, 0L);
        }
        // Set the sigma value for the source vertex to 1
        sigma.put(source, 1L);
        // Insert the source vertex into the heap with distance 0
        distances.put(source, heap.insert(0D, source));

        // Run Dijkstra's algorithm until the heap is empty
        while (!heap.isEmpty()) {
            // Extract the vertex with the minimum distance from the heap
            AddressableHeap.Handle<Double, Integer> vHandle = heap.deleteMin();
            Integer v = vHandle.getValue();
            double vDistance = vHandle.getKey();
            stack.push(v);

            // Iterate over the outgoing edges of the current vertex
            for (DefaultWeightedEdge edge : graph.outgoingEdgesOf(v)) {
                Integer w = Graphs.getOppositeVertex(graph, edge, v);

                // Ignore self-loops
                if (w.equals(v)) {
                    continue;
                }

                // Calculate the new distance to vertex w
                double edgeWeight = graph.getEdgeWeight(edge);
                double newDistance = vDistance + edgeWeight;

                // Get the handle for vertex w from the distances map
                AddressableHeap.Handle<Double, Integer> wHandle = distances.get(w);

                // If the handle is null, insert vertex w into the heap and update the maps
                if (wHandle == null) {
                    wHandle = heap.insert(newDistance, w);
                    distances.put(w, wHandle);
                    sigma.put(w, 0L);
                    predecessors.put(w, new ArrayList<>());
                }
                // If the new distance is smaller than the current distance, update the handle
                // and maps
                else if (Double.compare(wHandle.getKey(), newDistance) > 0) {
                    wHandle.decreaseKey(newDistance);
                    sigma.put(w, 0L);
                    predecessors.put(w, new ArrayList<>());
                }

                // If the new distance is equal to the current distance, update the sigma value
                // and predecessors map
                if (Double.compare(wHandle.getKey(), newDistance) == 0) {
                    long wCounter = sigma.get(w);
                    long vCounter = sigma.get(v);
                    long sum = wCounter + vCounter;
                    sigma.put(w, sum);
                    predecessors.computeIfAbsent(w, k -> new ArrayList<>()).add(edge);
                }
            }
        }

        // Perform the accumulate step with the predecessors and sigma values
        accumulate(predecessors, sigma);
    }

    /**
     * Accumulates scores for each edge in the graph based on the predecessors and
     * sigma values.
     *
     * @param predecessors a map of vertices to their predecessors
     * @param sigma        a map of vertices to their sigma values
     */
    private void accumulate(Map<Integer, List<DefaultWeightedEdge>> predecessors, Map<Integer, Long> sigma) {
        // Initialize a map to store the delta values for each vertex
        Map<Integer, Double> delta = new HashMap<>();

        // Initialize delta values for each vertex as 0
        for (Integer vertex : graph.iterables().vertices()) {
            delta.put(vertex, 0d);
        }

        // Process each vertex in the stack
        while (!stack.isEmpty()) {
            Integer w = stack.pop();
            List<DefaultWeightedEdge> wPredecessors = predecessors.get(w);

            // If there are predecessors for the current vertex
            if (wPredecessors != null) {
                // Process each predecessor edge
                for (DefaultWeightedEdge edge : wPredecessors) {
                    Integer v = Graphs.getOppositeVertex(graph, edge, w);

                    // Calculate the coefficient based on sigma and delta values
                    double coefficient = (sigma.get(v).doubleValue() / sigma.get(w).doubleValue()) * (1 + delta.get(w));

                    // Update the score for the edge
                    scores.put(edge, scores.get(edge) + coefficient);

                    // Update the delta value for the vertex
                    delta.put(v, delta.get(v) + coefficient);
                }
            }
        }
    }

    /**
     * Retrieves the scores of the graph vertices.
     *
     * @return an array of scores
     */
    public double[] getScores() {
        // Initialize scores for each edge in the graph
        for (DefaultWeightedEdge edge : graph.iterables().edges()) {
            scores.put(edge, 0d);
        }

        // Update scores for each vertex in the graph
        for (Integer vertex : graph.iterables().vertices()) {
            singleVertexUpdate(vertex);
        }

        // Convert scores to double array and return
        return scores.values().stream().mapToDouble(Double::doubleValue).toArray();
    }
}
