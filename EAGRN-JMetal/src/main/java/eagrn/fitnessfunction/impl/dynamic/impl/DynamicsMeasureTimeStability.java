package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.Map;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.FitnessFunction;

public class DynamicsMeasureTimeStability implements FitnessFunction {
    private ArrayList<String> geneNames;

    public DynamicsMeasureTimeStability(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {
        double[][] adjacencyMatrix = StaticUtils.getMatrixFromEdgeList(consensus, geneNames, 4);
        return dynamicsMeasureTimeStability(adjacencyMatrix, 0.03);
    }

    /**
     * En términos generales, un valor intermedio para el parámetro threshold en
     * este tipo de algoritmos suele ser alrededor del 0.01 o 0.05.
     */
    public double dynamicsMeasureTimeStability(double[][] adjacencyMatrix, double threshold) {
        int numNodes = adjacencyMatrix.length;
        double[] nodeActivities = new double[numNodes];
        double[] previousActivities = new double[numNodes];
        int time = 0;
        double delta = Double.MAX_VALUE;

        // Inicializamos la actividad de los nodos con valores aleatorios
        for (int i = 0; i < numNodes; i++) {
            nodeActivities[i] = Math.random();
        }

        // Iteramos hasta que la diferencia entre la actividad de los nodos en dos
        // tiempos consecutivos sea menor que el umbral establecido
        while (delta >= threshold) {
            // Actualizamos la actividad de los nodos
            for (int i = 0; i < numNodes; i++) {
                previousActivities[i] = nodeActivities[i];
                nodeActivities[i] = 0;
                for (int j = 0; j < numNodes; j++) {
                    nodeActivities[i] += adjacencyMatrix[i][j] * previousActivities[j];
                }
            }

            // Actualizamos la delta
            delta = 0;
            for (int i = 0; i < numNodes; i++) {
                delta += Math.abs(nodeActivities[i] - previousActivities[i]);
            }

            time++;
        }

        return time;
    }

}