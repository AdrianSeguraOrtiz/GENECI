package eagrn.fitnessfunction.impl.topology.impl;

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
    private Map<Integer, Double> cache;

    public GlobalClusteringMeasure(CutOffCriteria cutOffCriteria){
        this.cutOffCriteria = cutOffCriteria;
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
            Graph<Integer, DefaultEdge> graph = super.getGraphFromNetwork(adjacencyMatrix, false);
            adjacencyMatrix = null;
            ClusteringCoefficient<Integer, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
            score = -evaluator.getGlobalClusteringCoefficient();
            this.cache.put(key, score);
        }
        
        return score;
    }
}
