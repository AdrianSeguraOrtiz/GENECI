package eagrn.fitnessfunctions.impl.topology.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

import org.jgrapht.Graph;
import org.jgrapht.generate.*;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.util.SupplierUtil;
import org.testng.annotations.Test;

import eagrn.cutoffcriteria.impl.MinConfCriteria;
import eagrn.fitnessfunction.impl.topology.impl.GlobalClusteringMeasure;

public class GlobalClusteringMeasureTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        genericTest(50);
    }

    @Test
    void shouldReturnFitnessValueCaseB() {
        genericTest(100);
    }

    @Test
    void shouldReturnFitnessValueCaseC() {
        genericTest(250);
    }

    @Test
    void shouldReturnFitnessValueCaseD() {
        genericTest(500);
    }

    private Supplier<String> getVertexSupplier() {
        return new Supplier<String>() {
            private int id = 0;

            @Override
            public String get() {
                return "G" + id++;
            }
        };
    }

    private Map<String, Float> getMapFromGraph(Graph<String, DefaultEdge> graph){
        Map<String, Float> map = new HashMap<>();
        for (DefaultEdge edge : graph.edgeSet()) {
            String[] strEdge = edge.toString().split("[ ():]");
            map.put(strEdge[1] + ";" + strEdge[4], 1.0f);
        }
        return map;
    }


    private void genericTest(int size) {
        Graph<String, DefaultEdge> randomGraph = new SimpleDirectedGraph<>(getVertexSupplier(), SupplierUtil.createDefaultEdgeSupplier(), false);
        GnpRandomGraphGenerator<String, DefaultEdge> randomGenerator = new GnpRandomGraphGenerator<>(size, 0.5);
        randomGenerator.generateGraph(randomGraph);
        Map<String, Float> badTopologyConsensus = getMapFromGraph(randomGraph);

        Graph<String, DefaultEdge> completeGraph = new SimpleDirectedGraph<>(getVertexSupplier(), SupplierUtil.createDefaultEdgeSupplier(), false);
        CompleteGraphGenerator<String, DefaultEdge> completeGenerator = new CompleteGraphGenerator<>(size);
        completeGenerator.generateGraph(completeGraph);
        Map<String, Float> goodTopologyConsensus = getMapFromGraph(completeGraph);

        Supplier<String> vSupplier = getVertexSupplier();
        ArrayList<String> geneNames = new ArrayList<>();
        for (int i = 0; i < size; i++){
            geneNames.add(vSupplier.get());
        }

        Double[] x = new Double[]{};

        GlobalClusteringMeasure topology = new GlobalClusteringMeasure(new MinConfCriteria(0.0f, geneNames));
        double fitnessGoodTopologyConsensus = topology.run(goodTopologyConsensus, x);
        double fitnessBadTopologyConsensus = topology.run(badTopologyConsensus, x);

        System.out.println();
        System.out.println("Test case for network size: " + size);
        System.out.println("Good Topology: " + fitnessGoodTopologyConsensus);
        System.out.println("Bad Topology: " + fitnessBadTopologyConsensus);

        assert(fitnessGoodTopologyConsensus < fitnessBadTopologyConsensus);
    }
}
