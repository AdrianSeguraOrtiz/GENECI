package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.Map;

import Jama.EigenvalueDecomposition;
import Jama.Matrix;
import eagrn.fitnessfunction.FitnessFunction;

public class DynamicsMeasureAutovectorsStability implements FitnessFunction{
    private ArrayList<String> geneNames;

    public DynamicsMeasureAutovectorsStability(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double[][] adjacencyMatrix = getDoubleMatrixFromEdgeList(consensus, geneNames, 4);
        return dynamicsMeasureAutovectorsStability(adjacencyMatrix, 0.5);
    }

    // un valor intermedio para el threshold podría ser 0.5.
    public double dynamicsMeasureAutovectorsStability(double[][] adjacencyMatrix, double threshold) {
        Matrix matrix = new Matrix(adjacencyMatrix);
        EigenvalueDecomposition eigen = matrix.eig();

        double[] realEigenvalues = eigen.getRealEigenvalues();

        double score = 0;
        for (int i = 0; i < realEigenvalues.length; i++) {
            double eigenvalue = realEigenvalues[i];
            if (Math.abs(eigenvalue) > threshold) {
                score += 1;
            }
        }

        return 1.0 / score;
    }

    public static double[][] getDoubleMatrixFromEdgeList(Map<String, Float> links, ArrayList<String> geneNames, int decimals) {
        int numberOfNodes = geneNames.size();
        double[][] network = new double[numberOfNodes][numberOfNodes];

        double factor = Math.pow(10, decimals);
        for (Map.Entry<String, Float> pair : links.entrySet()) {
            String [] parts = pair.getKey().split(";");
            int g1 = geneNames.indexOf(parts[0]);
            int g2 = geneNames.indexOf(parts[1]);
            if (g1 != -1 && g2 != -1) {
                network[g1][g2] = (double) Math.round(pair.getValue() * factor) / factor;
            }
        }
        
        return network;
    }
}
