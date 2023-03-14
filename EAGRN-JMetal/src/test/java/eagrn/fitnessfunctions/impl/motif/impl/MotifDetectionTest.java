package eagrn.fitnessfunctions.impl.motif.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.testng.annotations.Test;

import eagrn.cutoffcriteria.impl.MinConfCriteria;
import eagrn.fitnessfunction.impl.motif.impl.MotifDetection;

public class MotifDetectionTest {

    private Map<String, Double> getMapFromGraph(Graph<String, DefaultEdge> graph) {
        Map<String, Double> map = new HashMap<>();
        for (DefaultEdge edge : graph.edgeSet()) {
            String[] strEdge = edge.toString().split("[ ():]");
            map.put(strEdge[1] + ";" + strEdge[4], 1.0);
        }
        return map;
    }

    @Test
    void checkFeedforwardLoop() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("A", "C");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedforwardLoop" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkCoRegulation() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "C");
        graph.addEdge("B", "C");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "CoRegulation" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkCascade1Of4() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Cascade" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -16);
    }

    @Test
    void checkCascade2Of2() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("D", "E");
        graph.addEdge("E", "F");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Cascade" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -8);
    }

    @Test
    void checkFeedbackLoopWithCoRegulation() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "A");
        graph.addEdge("A", "C");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedbackLoopWithCoRegulation" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkFeedbackLoopWithBifurcation() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("A", "D");
        graph.addEdge("B", "C");
        graph.addEdge("D", "C");
        graph.addEdge("C", "E");
        graph.addEdge("E", "A");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedbackLoopWithBifurcation" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkFeedforwardChainA() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");

        graph.addEdge("E", "B");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedforwardChain" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -17);
    }

    @Test
    void checkFeedforwardChainB() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");

        graph.addEdge("D", "A");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedforwardChain" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -17);
    }

    @Test
    void checkFeedforwardChainC() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");

        graph.addEdge("D", "A");
        graph.addEdge("E", "B");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedforwardChain" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -24);
    }

    @Test
    void checkFeedforwardChainD() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");
        graph.addEdge("E", "F");

        graph.addEdge("D", "A");
        graph.addEdge("E", "B");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "FeedforwardChain" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -33);
    }

    @Test
    void checkDifferentiation() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("A", "C");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Differentiation" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkRegulatoryRoute() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E", "F"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");
        graph.addEdge("E", "F");
        graph.addEdge("F", "A");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "RegulatoryRoute" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -25);
    }

    @Test
    void checkBifurcation() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("A", "C");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Bifurcation" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkCoupling() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "A");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Coupling" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

    @Test
    void checkTransduction() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D", "E"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");
        graph.addEdge("D", "E");
        graph.addEdge("E", "B");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "Transduction" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -4);
    }

    @Test
    void checkBiParallel() {
        Graph<String, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

        ArrayList<String> geneNames = new ArrayList<>(Arrays.asList("A", "B", "C", "D"));
        for (String gene : geneNames) {
            graph.addVertex(gene);
        }

        graph.addEdge("A", "B");
        graph.addEdge("A", "C");
        graph.addEdge("C", "D");
        graph.addEdge("B", "D");

        Map<String, Double> motifMap = getMapFromGraph(graph);

        Double[] x = new Double[] {};

        MotifDetection motifDetection = new MotifDetection(new MinConfCriteria(0.0, geneNames),
                new String[] { "BiParallel" });
        double fitnessValue = motifDetection.run(motifMap, x);

        assert (fitnessValue == -1);
    }

}
