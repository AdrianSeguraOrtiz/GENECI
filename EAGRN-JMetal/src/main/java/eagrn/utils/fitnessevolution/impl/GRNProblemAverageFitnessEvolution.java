package eagrn.utils.fitnessevolution.impl;

import java.util.ArrayList;
import java.util.Map;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.utils.fitnessevolution.GRNProblemFitnessEvolution;

public class GRNProblemAverageFitnessEvolution extends GRNProblemFitnessEvolution {
    
    public GRNProblemAverageFitnessEvolution(Map<String, Double[]> inferredNetworks, ArrayList<String> geneNames,
            CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        super(inferredNetworks, geneNames, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
    }

    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {

        DoubleSolution result = super.evaluate(solution);

        int cnt = parallelCount.incrementAndGet();
        for (int i = 0; i < fitnessFunctions.length; i++){
            progressiveValues.addAndGet(i, result.objectives()[i]);
            if (cnt % populationSize == 0){
                generationFitness[i].add(progressiveValues.get(i)/populationSize);
                progressiveValues.set(i, 0.0);
            }
        }

        return result;
    }
}
