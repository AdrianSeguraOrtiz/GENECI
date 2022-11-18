package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Map;

import org.apache.commons.lang.ArrayUtils;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.BetweennessCentrality;
import org.jgrapht.graph.DefaultEdge;

import eagrn.fitnessfunction.impl.topology.Topology;

public class BetweennessDistribution extends Topology {
    private ArrayList<String> geneNames;

    public BetweennessDistribution(ArrayList<String> geneNames){
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(consensus, geneNames, true, true);
        BetweennessCentrality<String, DefaultEdge> evaluator = new BetweennessCentrality<>(graph);
        Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
        for (int i = 0; i < scores.length; i++) {
            scores[i] += 1;
        }
        return -super.paretoTest(ArrayUtils.toPrimitive(scores));
    }
    
}
