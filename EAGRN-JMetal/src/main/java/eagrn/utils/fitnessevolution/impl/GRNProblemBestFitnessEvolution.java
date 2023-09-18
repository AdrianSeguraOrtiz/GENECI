package eagrn.utils.fitnessevolution.impl;

import java.util.ArrayList;
import java.util.Map;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.utils.fitnessevolution.GRNProblemFitnessEvolution;

public class GRNProblemBestFitnessEvolution extends GRNProblemFitnessEvolution {
    
    public GRNProblemBestFitnessEvolution(Map<String, Float[]> inferredNetworks, ArrayList<String> geneNames,
            CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        super(inferredNetworks, geneNames, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
        for (int i = 0; i < fitnessFunctions.length; i++){
            this.progressiveValues.set(i, Double.MAX_VALUE);
        }
    }

    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {

        DoubleSolution result = super.evaluate(solution);

        int cnt = parallelCount.incrementAndGet();
        for (int i = 0; i < fitnessFunctions.length; i++){
            double currentMin = progressiveValues.get(i);
            if (result.objectives()[i] < currentMin) {
                progressiveValues.compareAndSet(i, currentMin, result.objectives()[i]);
            }
            if (cnt % populationSize == 0){
                System.out.println(cnt);
                generationFitness[i].add(progressiveValues.get(i));
            }
        }

        return result;
    }
}
