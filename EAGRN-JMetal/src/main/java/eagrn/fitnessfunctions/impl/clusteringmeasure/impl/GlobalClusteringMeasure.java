package eagrn.fitnessfunctions.impl.clusteringmeasure.impl;

import java.util.ArrayList;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.ClusteringCoefficient;
import org.jgrapht.graph.DefaultEdge;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.impl.clusteringmeasure.ClusteringMeasure;

public class GlobalClusteringMeasure extends ClusteringMeasure {

    public GlobalClusteringMeasure(ArrayList<String> geneNames, CutOffCriteria cutOffCriteria) {
        super(geneNames, cutOffCriteria);
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Map<String, Double> cutConsensus = cutOffCriteria.getCutMap(consensus);
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(cutConsensus, false);
        ClusteringCoefficient<String, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
        return -evaluator.getGlobalClusteringCoefficient();
    }
}
