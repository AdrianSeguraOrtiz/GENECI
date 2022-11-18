package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Map;

import org.apache.commons.lang.ArrayUtils;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.EdgeBetweennessCentrality;
import org.jgrapht.graph.DefaultEdge;

import eagrn.fitnessfunction.impl.topology.Topology;

public class EdgeBetweennessDistribution extends Topology {
    private ArrayList<String> geneNames;

    public EdgeBetweennessDistribution(ArrayList<String> geneNames){
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(consensus, geneNames, true, true);
        EdgeBetweennessCentrality<String, DefaultEdge> evaluator = new EdgeBetweennessCentrality<>(graph);
        Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
        return -super.paretoTest(ArrayUtils.toPrimitive(scores));
    }
    
}
