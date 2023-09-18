package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.ClusteringCoefficient;
import org.jgrapht.graph.DefaultEdge;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.impl.topology.Topology;

public class GlobalClusteringMeasure extends Topology {
    private CutOffCriteria cutOffCriteria;
    private ArrayList<String> geneNames;
    private Map<Integer, Double> cache;

    public GlobalClusteringMeasure(ArrayList<String> geneNames, CutOffCriteria cutOffCriteria){
        this.cutOffCriteria = cutOffCriteria;
        this.geneNames = geneNames;
        this.cache = new HashMap<>();
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) { 
        double score = 0.0;
        boolean[][] adjacencyMatrix = cutOffCriteria.getNetwork(consensus);
        int key = Arrays.deepHashCode(adjacencyMatrix);

        if (this.cache.containsKey(key)){
            score = this.cache.get(key);
        } else {
            Graph<String, DefaultEdge> graph = super.getGraphFromNetwork(adjacencyMatrix, geneNames, false);
            adjacencyMatrix = null;
            ClusteringCoefficient<String, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
            score = -evaluator.getGlobalClusteringCoefficient();
            this.cache.put(key, score);
        }
        
        return score;
    }
}