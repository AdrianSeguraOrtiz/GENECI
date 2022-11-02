package eagrn.fitnessfunctions.impl.clusteringmeasure;

import java.util.ArrayList;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleGraph;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.FitnessFunction;

public abstract class ClusteringMeasure implements FitnessFunction {
    private ArrayList<String> geneNames;
    protected CutOffCriteria cutOffCriteria;

    public ClusteringMeasure(ArrayList<String> geneNames, CutOffCriteria cutOffCriteria){
        this.geneNames = geneNames;
        this.cutOffCriteria = cutOffCriteria;
    }

    protected Graph<String, DefaultEdge> getGraphFromConsensus(Map<String, Double> consensus, boolean directed) {
        Graph<String, DefaultEdge> graph = directed ? new SimpleDirectedGraph<>(DefaultEdge.class) : new SimpleGraph<>(DefaultEdge.class);

        for (String gene : this.geneNames) {
            graph.addVertex(gene);
        }

        for (Map.Entry<String, Double> pair : consensus.entrySet()) {
            String[] genes = pair.getKey().split(";");
            graph.addEdge(genes[0], genes[1]);
        }

        return graph;
    }

}