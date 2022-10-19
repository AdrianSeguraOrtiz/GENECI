package eagrn;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import com.google.common.util.concurrent.AtomicDoubleArray;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.operator.repairer.WeightRepairer;

public class GRNProblemFitnessEvolution extends GRNProblem {
    private AtomicDoubleArray cumulativeFitness;
    private ArrayList<Double>[] meanFitness;
    private static AtomicInteger parallelCount;
    private int populationSize;

    /** Constructor creates a default instance of the GRN problem fitness evolution */
    public GRNProblemFitnessEvolution(Map<String, Double[]> inferredNetworks, ArrayList<String> geneNames, WeightRepairer initialPopulationRepairer, CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        super(inferredNetworks, geneNames, initialPopulationRepairer, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);

        GRNProblemFitnessEvolution.parallelCount = new AtomicInteger();
        this.populationSize = 0;
        int numOfObjetives = this.fitnessFunctions.length;
        this.cumulativeFitness = new AtomicDoubleArray(numOfObjetives);
        this.meanFitness = new ArrayList[numOfObjetives];
        for (int i = 0; i < numOfObjetives; i++) {
            this.cumulativeFitness.set(i, 0.0);
            this.meanFitness[i] = new ArrayList<>();
        }
    }

    /** CreateSolution() method */
    @Override
    public DoubleSolution createSolution() {
        DoubleSolution solution = super.createSolution();
        this.populationSize += 1;
        return solution;
    }
    
    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {

        DoubleSolution result = super.evaluate(solution);

        int cnt = parallelCount.incrementAndGet();
        for (int i = 0; i < fitnessFunctions.length; i++){
            this.cumulativeFitness.addAndGet(i, result.objectives()[i]);
            if (cnt % this.populationSize == 0){
                this.meanFitness[i].add(this.cumulativeFitness.get(i)/this.populationSize);
                this.cumulativeFitness.set(i, 0.0);
            }
        }

        return result;
    }

    /** GetFitnessEvolution() method */
    public Map<String, Double[]> getFitnessEvolution() {
        Map<String, Double[]> fitnessEvolution = new HashMap<String, Double[]>();
        for (int i = 0; i < fitnessFunctions.length; i++) {
            fitnessEvolution.put("F" + i, this.meanFitness[i].toArray(new Double[this.meanFitness[i].size()]));
        }
        return fitnessEvolution;
    }

}
