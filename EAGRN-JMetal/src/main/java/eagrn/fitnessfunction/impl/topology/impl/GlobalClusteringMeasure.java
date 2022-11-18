package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.ClusteringCoefficient;
import org.jgrapht.graph.DefaultEdge;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.impl.topology.Topology;

public class GlobalClusteringMeasure extends Topology {
    private CutOffCriteria cutOffCriteria;
    private ArrayList<String> geneNames;

    public GlobalClusteringMeasure(ArrayList<String> geneNames, CutOffCriteria cutOffCriteria){
        this.cutOffCriteria = cutOffCriteria;
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Map<String, Double> cutConsensus = cutOffCriteria.getCutMap(consensus);
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(cutConsensus, geneNames, false, false);
        ClusteringCoefficient<String, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
        return -evaluator.getGlobalClusteringCoefficient();
    }
}
