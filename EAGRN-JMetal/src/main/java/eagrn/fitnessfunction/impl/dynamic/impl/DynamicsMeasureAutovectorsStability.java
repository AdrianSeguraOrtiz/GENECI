package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import Jama.EigenvalueDecomposition;
import Jama.Matrix;
import eagrn.StaticUtils;
import eagrn.fitnessfunction.FitnessFunction;

public class DynamicsMeasureAutovectorsStability implements FitnessFunction{
    private Map<String, Integer> geneIndexMap;

    public DynamicsMeasureAutovectorsStability(ArrayList<String> geneNames) {
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double[][] adjacencyMatrix = StaticUtils.getDoubleMatrix(consensus, geneIndexMap, 4);
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

    
}
