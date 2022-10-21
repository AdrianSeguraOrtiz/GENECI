package eagrn.fitnessfunctions.impl.ClusteringMeasure;

import java.util.ArrayList;
import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleGraph;

import eagrn.fitnessfunctions.FitnessFunction;

public abstract class ClusteringMeasure implements FitnessFunction {
    private ArrayList<String> geneNames;

    public ClusteringMeasure(ArrayList<String> geneNames){
        this.geneNames = geneNames;
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