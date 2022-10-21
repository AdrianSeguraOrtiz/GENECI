package eagrn.fitnessfunctions.impl.ClusteringMeasure.impl;

import java.util.ArrayList;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.ClusteringCoefficient;
import org.jgrapht.graph.DefaultEdge;

import eagrn.fitnessfunctions.impl.ClusteringMeasure.ClusteringMeasure;

public class GlobalClusteringMeasure extends ClusteringMeasure {

    public GlobalClusteringMeasure(ArrayList<String> geneNames) {
        super(geneNames);
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(consensus, false);
        ClusteringCoefficient<String, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
        return -evaluator.getGlobalClusteringCoefficient();
    }
}
