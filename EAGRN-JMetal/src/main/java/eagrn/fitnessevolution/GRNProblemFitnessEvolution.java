package eagrn.fitnessevolution;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import com.google.common.util.concurrent.AtomicDoubleArray;

import eagrn.GRNProblem;
import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.operator.repairer.WeightRepairer;

public abstract class GRNProblemFitnessEvolution extends GRNProblem {
    protected AtomicDoubleArray progressiveValues;
    protected ArrayList<Double>[] generationFitness;
    protected AtomicInteger parallelCount;
    protected int populationSize;

    /** Constructor creates a default instance of the GRN problem fitness evolution */
    public GRNProblemFitnessEvolution(Map<String, Double[]> inferredNetworks, ArrayList<String> geneNames, WeightRepairer initialPopulationRepairer, CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        super(inferredNetworks, geneNames, initialPopulationRepairer, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);

        this.parallelCount = new AtomicInteger();
        this.populationSize = 0;
        int numOfObjetives = this.fitnessFunctions.length;
        this.progressiveValues = new AtomicDoubleArray(numOfObjetives);
        this.generationFitness = new ArrayList[numOfObjetives];
        for (int i = 0; i < numOfObjetives; i++) {
            this.progressiveValues.set(i, 0.0);
            this.generationFitness[i] = new ArrayList<>();
        }
    }

    /** CreateSolution() method */
    @Override
    public DoubleSolution createSolution() {
        DoubleSolution solution = super.createSolution();
        this.populationSize += 1;
        return solution;
    }

    /** GetFitnessEvolution() method */
    public Map<String, Double[]> getFitnessEvolution() {
        Map<String, Double[]> fitnessEvolution = new HashMap<String, Double[]>();
        for (int i = 0; i < fitnessFunctions.length; i++) {
            fitnessEvolution.put("F" + i, this.generationFitness[i].toArray(new Double[this.generationFitness[i].size()]));
        }
        return fitnessEvolution;
    }

}
