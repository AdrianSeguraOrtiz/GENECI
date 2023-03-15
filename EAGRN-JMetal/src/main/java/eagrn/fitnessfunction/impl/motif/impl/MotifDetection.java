package eagrn.fitnessfunction.impl.motif.impl;

import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.FitnessFunction;

public class MotifDetection implements FitnessFunction {
    private CutOffCriteria cutOffCriteria;
    private MotifFitnessInterface[] motifFunctions;

    public interface MotifFitnessInterface {
        int count(Graph<Integer, DefaultEdge> graph);
    }

    public MotifDetection(CutOffCriteria cutOffCriteria, String[] motifs) {
        this.cutOffCriteria = cutOffCriteria;
        this.motifFunctions = new MotifFitnessInterface[motifs.length];

        for (int i = 0; i < motifs.length; i++) {
            MotifFitnessInterface function;
            switch (motifs[i].toLowerCase()) {
                case "feedforwardloop":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectFeedforwardLoop(graph);
                    };
                    break;
                case "coregulation":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectCoRegulation(graph);
                    };
                    break;
                case "cascade":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectCascade(graph);
                    };
                    break;
                case "feedbackloopwithcoregulation":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectFeedbackLoopWithCoRegulation(graph);
                    };
                    break;
                case "feedforwardchain":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectFeedforwardChain(graph);
                    };
                    break;
                case "differentiation":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectDifferentiation(graph);
                    };
                    break;
                case "regulatoryroute":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectRegulatoryRoute(graph);
                    };
                    break;
                case "bifurcation":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectBifurcation(graph);
                    };
                    break;
                case "coupling":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectCoupling(graph);
                    };
                    break;
                case "biparallel":
                    function = (Graph<Integer, DefaultEdge> graph) -> {
                        return detectBiParallel(graph);
                    };
                    break;
                default:
                    throw new RuntimeException(motifs[i] + " motif is not available for detection");

            }
            this.motifFunctions[i] = function;
        }
    }

    public Graph<Integer, DefaultEdge> createGraphFromMatrix(int[][] adjMatrix) {

        Graph<Integer, DefaultEdge> graph = new SimpleDirectedGraph<>(DefaultEdge.class);

        // Agregamos los nodos al grafo
        for (int i = 0; i < adjMatrix.length; i++) {
            graph.addVertex(i);
        }
        // Agregamos las aristas al grafo
        for (int i = 0; i < adjMatrix.length; i++) {
            for (int j = 0; j < adjMatrix[i].length; j++) {
                if (adjMatrix[i][j] == 1) {
                    graph.addEdge(i, j);
                }
            }
        }

        return graph;
    }

    public int detectFeedforwardLoop(Graph<Integer, DefaultEdge> graph) {
        int count = 0;

        // Para cada borde del grafo
        for (DefaultEdge edge : graph.edgeSet()) {
            int source = graph.getEdgeSource(edge);
            int target = graph.getEdgeTarget(edge);

            // Busca patrones de feedforward loops en los sucesores del destino
            for (int successor : Graphs.successorListOf(graph, target)) {
                if (successor != source && graph.containsEdge(source, successor)) {
                    count++;
                }
            }
        }

        return count;
    }

    public int detectBifurcation(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            if (Graphs.successorListOf(graph, i).size() == 2) {
                count++;
            }
        }
        return count;
    }

    public int detectCoupling(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            for (int j = i + 1; j < graph.vertexSet().size(); j++) {
                if (graph.containsEdge(i, j) && graph.containsEdge(j, i)) {
                    count++;
                }
            }
        }
        return count;
    }

    public int detectCoRegulation(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        Map<Integer, Set<Integer>> successors = new HashMap<>();
        for (int vertex : graph.vertexSet()) {
            successors.put(vertex, new HashSet<>(Graphs.successorListOf(graph, vertex)));
        }
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            for (int j = i + 1; j < graph.vertexSet().size(); j++) {
                Set<Integer> iSuccessors = successors.get(i);
                Set<Integer> jSuccessors = successors.get(j);
                Set<Integer> commonSuccessors = new HashSet<>(iSuccessors);
                commonSuccessors.retainAll(jSuccessors);
                if (!commonSuccessors.isEmpty()) {
                    count++;
                }
            }
        }
        return count;
    }

    public int detectDifferentiation(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            if (Graphs.predecessorListOf(graph, i).isEmpty()) {
                Set<Integer> visited = new HashSet<>();
                visited.add(i);
                if (detectDifferentiationHelper(graph, i, visited)) {
                    count++;
                }
            }
        }
        return count;
    }

    private boolean detectDifferentiationHelper(Graph<Integer, DefaultEdge> graph, int vertex, Set<Integer> visited) {
        if (Graphs.successorListOf(graph, vertex).isEmpty()) {
            return true;
        } else {
            boolean result = false;
            for (int neighbor : Graphs.successorListOf(graph, vertex)) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    result |= detectDifferentiationHelper(graph, neighbor, visited);
                    visited.remove(neighbor);
                }
            }
            return result;
        }
    }

    public int detectFeedforwardChain(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        Set<Integer> visited = new HashSet<Integer>();
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            if (!visited.contains(i)) {
                ArrayList<Integer> chain = new ArrayList<>();
                ArrayList<Integer> uncheckedLoops = new ArrayList<>();
                int loops = 0;
                int lastChainScore = 0;
                int current = i;
                boolean init = Graphs.successorListOf(graph, current).size() == 1
                        && (Graphs.predecessorListOf(graph, current).size() == 0
                                || Graphs.predecessorListOf(graph, current).size() == 1);
                List<Integer> successors = Graphs.successorListOf(graph, current);
                List<Integer> predecessors = Graphs.predecessorListOf(graph, current);

                while ((current == i && init) ||
                        ((successors.size() == 1 || successors.size() == 2) &&
                                (predecessors.size() == 1 || predecessors.size() == 2))) {

                    chain.add(current);

                    if (current == i) {
                        if (predecessors.size() == 2)
                            break;
                        if (predecessors.size() == 1)
                            uncheckedLoops.add(predecessors.get(0));
                    } else if (predecessors.size() == 2) {
                        int unchecked;
                        if (chain.get(chain.size() - 2) == predecessors.get(0)) {
                            unchecked = predecessors.get(1);
                        } else if (chain.get(chain.size() - 2) == predecessors.get(1)) {
                            unchecked = predecessors.get(0);
                        } else {
                            break;
                        }
                        if (chain.contains(unchecked))
                            break;
                        uncheckedLoops.add(unchecked);
                    }

                    if (successors.size() == 1) {
                        if (chain.contains(successors.get(0))) {
                            loops++;
                            uncheckedLoops.remove(Integer.valueOf(current));
                            if (chain.size() >= 3 && loops > 0 && uncheckedLoops.size() == 0) {
                                lastChainScore = (int) (Math.pow(chain.size() - 1, 2) + Math.pow(loops, 3));
                            }
                            break;
                        }
                        current = successors.get(0);
                    } else if (successors.size() == 2) {
                        if ((chain.contains(successors.get(0)) && chain.contains(successors.get(1)) ||
                                !chain.contains(successors.get(0)) && !chain.contains(successors.get(1)))) {
                            break;
                        }
                        loops++;
                        uncheckedLoops.remove(Integer.valueOf(current));
                        current = chain.contains(successors.get(0)) ? successors.get(1) : successors.get(0);
                    }

                    if (chain.size() >= 3 && loops > 0 && uncheckedLoops.size() == 0) {
                        lastChainScore = (int) (Math.pow(chain.size() - 1, 2) + Math.pow(loops, 3));
                    }

                    successors = Graphs.successorListOf(graph, current);
                    predecessors = Graphs.predecessorListOf(graph, current);
                }

                if (successors.size() == 0) {
                    chain.add(current);
                    if (chain.size() >= 3 && loops > 0 && uncheckedLoops.size() == 0) {
                        lastChainScore = (int) (Math.pow(chain.size() - 1, 2) + Math.pow(loops, 3));
                    }
                }

                count += lastChainScore;
                visited.addAll(chain);
            }
        }
        return count;
    }

    public int detectRegulatoryRoute(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        boolean[] visited = new boolean[graph.vertexSet().size()];
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            if (!visited[i] && Graphs.successorListOf(graph, i).size() == 1) {
                visited[i] = true;
                int current = i;
                int next = -1;
                int size = 0;
                while (current == i || (Graphs.successorListOf(graph, current).size() == 1
                        && Graphs.predecessorListOf(graph, current).size() == 1)) {
                    next = Graphs.successorListOf(graph, current).get(0);
                    if (visited[next])
                        break;
                    current = next;
                    visited[current] = true;
                    size++;
                }
                if (graph.containsEdge(current, i)) {
                    count += Math.pow(size, 2);
                }
            }
        }
        return count;
    }

    public int detectBiParallel(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            List<Integer> successors = Graphs.successorListOf(graph, i);
            if (successors.size() == 2) {
                Set<Integer> s1 = new HashSet<>(Graphs.successorListOf(graph, successors.get(0)));
                Set<Integer> s2 = new HashSet<>(Graphs.successorListOf(graph, successors.get(1)));
                s1.retainAll(s2);
                if (!s1.isEmpty()) {
                    count += s1.size();
                }
            }
        }
        return count;
    }

    public int detectCascade(Graph<Integer, DefaultEdge> graph) {
        int count = 0;
        Set<Integer> visited = new HashSet<Integer>();
        for (int i = 0; i < graph.vertexSet().size(); i++) {
            if (!visited.contains(i) && Graphs.predecessorListOf(graph, i).size() == 1
                    && Graphs.successorListOf(graph, i).size() == 1) {
                int current = i;
                int size = 1;
                while (Graphs.successorListOf(graph, current).size() == 1
                        && Graphs.predecessorListOf(graph, Graphs.successorListOf(graph, current).get(0)).size() == 1) {
                    current = Graphs.successorListOf(graph, current).get(0);
                    size++;
                    visited.add(current);
                }
                if (size > 1) {
                    count += Math.pow(size, 2);
                }
            }
        }
        return count;
    }

    public int detectFeedbackLoopWithCoRegulation(Graph<Integer, DefaultEdge> graph) {
        int count = 0;

        for (DefaultEdge edge : graph.edgeSet()) {
            int source = graph.getEdgeSource(edge);
            int target = graph.getEdgeTarget(edge);

            for (int successor : Graphs.successorListOf(graph, target)) {
                if (successor != source && graph.containsEdge(successor, source)
                        && graph.containsEdge(source, successor)) {
                    count++;
                }
            }
        }

        return count;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        int[][] adjacencyMatrix = cutOffCriteria.getNetwork(consensus);
        Graph<Integer, DefaultEdge> graph = createGraphFromMatrix(adjacencyMatrix);

        double score = 0.0;
        for (int i = 0; i < this.motifFunctions.length; i++) {
            score += (this.motifFunctions.length - i) * motifFunctions[i].count(graph);
        }
        return -score;
    }

}
