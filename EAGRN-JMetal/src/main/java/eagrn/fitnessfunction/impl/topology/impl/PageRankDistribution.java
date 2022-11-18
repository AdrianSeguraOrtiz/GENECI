package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.Map;

import org.apache.commons.lang.ArrayUtils;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.PageRank;
import org.jgrapht.graph.DefaultEdge;

import eagrn.fitnessfunction.impl.topology.Topology;

public class PageRankDistribution extends Topology {
    private ArrayList<String> geneNames;

    public PageRankDistribution(ArrayList<String> geneNames){
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        Graph<String, DefaultEdge> graph = super.getGraphFromConsensus(consensus, geneNames, true, true);
        PageRank<String, DefaultEdge> evaluator = new PageRank<>(graph);
        Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
        return -super.paretoTest(ArrayUtils.toPrimitive(scores));
    }
    
}
