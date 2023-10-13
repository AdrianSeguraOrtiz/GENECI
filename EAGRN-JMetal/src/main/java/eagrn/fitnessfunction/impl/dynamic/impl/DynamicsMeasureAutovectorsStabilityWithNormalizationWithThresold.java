package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.Map;

import Jama.EigenvalueDecomposition;
import Jama.Matrix;
import eagrn.StaticUtils;
import eagrn.fitnessfunction.FitnessFunction;

public class DynamicsMeasureAutovectorsStabilityWithNormalizationWithThresold implements FitnessFunction { 

    private ArrayList<String> geneNames;

    public DynamicsMeasureAutovectorsStabilityWithNormalizationWithThresold(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double[][] adjacencyMatrix = StaticUtils.getDoubleMatrixFromEdgeList(consensus, geneNames, 4);
        return dynamicsMeasureAutovectorsStability(adjacencyMatrix, 0.5);
    }
    
    public double dynamicsMeasureAutovectorsStability(double[][] adjacencyMatrix, double threshold) {
 
        // Normalizar la matriz de adyacencia
        double[][] normalizedMatrix = new double[adjacencyMatrix.length][adjacencyMatrix[0].length];
        for (int i = 0; i < adjacencyMatrix.length; i++) {
            double sum = 0;
            for (int j = 0; j < adjacencyMatrix[i].length; j++) {
                sum += adjacencyMatrix[i][j];
            }
            if (sum > 0) {
                for (int j = 0; j < adjacencyMatrix[i].length; j++) {
                    normalizedMatrix[i][j] = adjacencyMatrix[i][j] / sum;
                }
            }
        }
    
        // Calcular los autovalores de la matriz de adyacencia
        Matrix matrix = new Matrix(normalizedMatrix);
        EigenvalueDecomposition eigen = matrix.eig();
    
        double[] realEigenvalues = eigen.getRealEigenvalues();
        double[] imagEigenvalues = eigen.getImagEigenvalues();
    
        double score = 0;
        for (int i = 0; i < realEigenvalues.length; i++) {
            double eigenvalue = Math.sqrt(realEigenvalues[i] * realEigenvalues[i] + imagEigenvalues[i] * imagEigenvalues[i]);
            if (eigenvalue > threshold) {
                score += 1;
            }
        }
    
        return 1.0 / score;
    }
    
}
