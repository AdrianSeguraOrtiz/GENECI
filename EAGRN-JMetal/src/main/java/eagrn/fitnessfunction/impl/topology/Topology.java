package eagrn.fitnessfunction.impl.topology;

import java.util.Arrays;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleDirectedWeightedGraph;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.graph.SimpleWeightedGraph;

import eagrn.fitnessfunction.FitnessFunction;

public abstract class Topology implements FitnessFunction {

    protected Graph<Integer, DefaultEdge> getGraphFromNetwork(boolean[][] adjacencyMatrix, boolean directed) {
        Graph<Integer, DefaultEdge> graph = directed ? new SimpleDirectedGraph<>(DefaultEdge.class) : new SimpleGraph<>(DefaultEdge.class);

        // Add vertices to the graph
        for (int i = 0; i < adjacencyMatrix.length; i++) {
            graph.addVertex(i);
        }

        // Add edges to the graph with their respective weights
        for (int i = 0; i < adjacencyMatrix.length; i++) {
            for (int j = 0; j < adjacencyMatrix.length; j++) {
                if (i != j && adjacencyMatrix[i][j]) graph.addEdge(i, j);
            }
        }

        return graph;
    }

    protected Graph<Integer, DefaultWeightedEdge> getGraphFromWeightedNetwork(float[][] adjacencyMatrix, boolean directed) {
        Graph<Integer, DefaultWeightedEdge> graph = directed ? new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class) : new SimpleWeightedGraph<>(DefaultWeightedEdge.class);

        // Add vertices to the graph
        for (int i = 0; i < adjacencyMatrix.length; i++) {
            graph.addVertex(i);
        }

        // Add edges to the graph with their respective weights
        for (int i = 0; i < adjacencyMatrix.length; i++) {
            for (int j = 0; j < adjacencyMatrix.length; j++) {
                if (i != j && adjacencyMatrix[i][j] != 0) {
                    DefaultWeightedEdge edge = graph.addEdge(i, j);
                    graph.setEdgeWeight(edge, adjacencyMatrix[i][j]);
                }
            }
        }

        return graph;
    }

    protected double paretoTest(double[] dat) {
        Arrays.sort(dat);
        int n = dat.length;

        double[] T = new double[n];
        for (int i = 0; i < n; i++) {
            T[i] = Math.log(dat[i] / dat[0]);
        }
        Arrays.sort(T);

        double[] Y = new double[n];
        double[] U = new double[n-1];
        double[] iU = new double[n-1];
        double Yn = 0.0;

        for (int i = 0; i < n; i++) {
            if (i == 0) {
                Y[i] = (n - i + 1) * (T[i]);
                U[i] = Y[i];
            } else if (i != (n - 1)) {
                Y[i] = (n - i + 1) * (T[i] - T[i - 1]);
                U[i] = U[i - 1] + Y[i];
            } else {
                Y[i] = (n - i + 1) * (T[i] - T[i - 1]);
                Yn = U[i - 1] + Y[i];
            }
        }

        double U_bar = 0.0;
        double iU_bar = 0.0;

        for (int i = 0; i < (n - 1); i++) {
            U[i] = U[i] / Yn;
            iU[i] = (Double.valueOf(i) + 1.0) * U[i];
            U_bar += U[i];
            iU_bar += iU[i];
        }

        U_bar = U_bar / (n - 1.0);
        iU_bar = iU_bar / (n - 1.0);

        double Z1 = Math.sqrt(12.0 * (n - 1.0)) * (U_bar - 0.5);
        double Z2 = Math.sqrt(5.0 * (n - 1.0) / ((n + 2.0) * (n - 2.0))) * (n - 2.0 + 6.0 * n * U_bar - (12.0 * iU_bar));

        double Z0 = Math.pow(Z1, 2) + Math.pow(Z2, 2);

        return Z0;
    }
}
