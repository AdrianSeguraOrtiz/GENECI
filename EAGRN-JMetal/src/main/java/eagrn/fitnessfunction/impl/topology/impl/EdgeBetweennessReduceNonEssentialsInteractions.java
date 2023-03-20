package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.EdgeBetweennessCentrality;
import org.jgrapht.graph.DefaultEdge;

import eagrn.fitnessfunction.impl.topology.Topology;

public class EdgeBetweennessReduceNonEssentialsInteractions extends Topology {
    private ArrayList<String> geneNames;

    public EdgeBetweennessReduceNonEssentialsInteractions(ArrayList<String> geneNames){
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(consensus, geneNames, true, true);
        EdgeBetweennessCentrality<String, DefaultEdge> evaluator = new EdgeBetweennessCentrality<>(graph);
        Double[] scores = evaluator.getScores().values().toArray(new Double[0]);

        Arrays.sort(scores);
        int n = (int) Math.round(scores.length * 0.2);
        double sum = 0;
        for (int i = 0; i < n ; i++) {
            sum += scores[i];
        }
        double mean = sum / (double)n;

        return 1.0 / mean;
    }
    
}
