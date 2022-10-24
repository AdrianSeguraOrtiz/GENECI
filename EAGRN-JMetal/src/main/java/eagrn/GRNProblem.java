package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.FitnessFunction;
import eagrn.operator.repairer.WeightRepairer;
import java.util.*;

import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;


public class GRNProblem extends AbstractDoubleProblem {
    private Map<String, Double[]> inferredNetworks;
    private ArrayList<String> geneNames;
    private WeightRepairer initialPopulationRepairer;
    private CutOffCriteria cutOffCriteria;
    protected FitnessFunction[] fitnessFunctions;
    private Map<String, Double[]> timeSeriesMap;

    /** Constructor creates a default instance of the GRN problem */
    public GRNProblem(Map<String, Double[]> inferredNetworks, ArrayList<String> geneNames, WeightRepairer initialPopulationRepairer, CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        
        this.inferredNetworks = inferredNetworks;
        this.geneNames = geneNames;
        this.initialPopulationRepairer = initialPopulationRepairer;
        this.cutOffCriteria = cutOffCriteria;
        if (strTimeSeriesFile != null) {
            this.timeSeriesMap = StaticUtils.readTimeSeries(strTimeSeriesFile);
        } else {
            this.timeSeriesMap = null;
        }

        /** Parse fitness functions */
        String[] formulas = strFitnessFormulas.split(";");
        this.fitnessFunctions = new FitnessFunction[formulas.length];
        for (int i = 0; i < formulas.length; i++) {
            this.fitnessFunctions[i] = StaticUtils.getCompositeFitnessFunction(formulas[i], this.geneNames, this.inferredNetworks, this.cutOffCriteria, this.timeSeriesMap);
        }

        setNumberOfVariables(inferredNetworks.values().iterator().next().length);
        setNumberOfObjectives(this.fitnessFunctions.length);
        setName("GRNProblem");

        List<Double> lowerLimit = new ArrayList<>(getNumberOfVariables());
        List<Double> upperLimit = new ArrayList<>(getNumberOfVariables());

        for (int i = 0; i < getNumberOfVariables(); i++) {
            lowerLimit.add(0.0);
            upperLimit.add(1.0);
        }

        setVariableBounds(lowerLimit, upperLimit);
    }

    /** CreateSolution() method */
    @Override
    public DoubleSolution createSolution() {
        DefaultDoubleSolution solution = new DefaultDoubleSolution(this.getNumberOfObjectives(), this.getNumberOfConstraints(), this.getBoundsForVariables());
        initialPopulationRepairer.repairSolution(solution);
        return solution;
    }

    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {
        Double[] x = new Double[getNumberOfVariables()];
        for (int i = 0; i < getNumberOfVariables(); i++) {
            x[i] = solution.variables().get(i);
        }

        Map<String, Double> consensus = StaticUtils.makeConsensus(x, this.inferredNetworks);
        for (int i = 0; i < fitnessFunctions.length; i++){
            solution.objectives()[i] = fitnessFunctions[i].run(consensus, x);
        }

        return solution;
    }

    @Override
    public void setName(String name) {
        super.setName(name);
    }
 
}
