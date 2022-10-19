package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunctions.FitnessFunction;
import eagrn.fitnessfunctions.impl.Loyalty;
import eagrn.fitnessfunctions.impl.Quality;
import eagrn.fitnessfunctions.impl.Topology;
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
    private String strTimeSeriesFile;

    /** Constructor creates a default instance of the GRN problem */
    public GRNProblem(Map<String, Double[]> inferredNetworks, ArrayList<String> geneNames, WeightRepairer initialPopulationRepairer, CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile) {
        
        this.inferredNetworks = inferredNetworks;
        this.geneNames = geneNames;
        this.initialPopulationRepairer = initialPopulationRepairer;
        this.cutOffCriteria = cutOffCriteria;
        this.strTimeSeriesFile = strTimeSeriesFile;

        /** Parse fitness functions */
        String[] formulas = strFitnessFormulas.split(";");
        this.fitnessFunctions = new FitnessFunction[formulas.length];

        for (int i = 0; i < formulas.length; i++) {
            String[] subformulas = formulas[i].split("\\+");
            FitnessFunction function;
            if (subformulas.length == 1) {
                String[] tuple = subformulas[0].split("\\*");
                switch (tuple.length) {
                    case 1:
                        function = getFitnessFunction(tuple[0]);
                        break;
                    case 2:
                        double weight;
                        try {
                            weight = Double.parseDouble(tuple[0]);
                        } catch (Exception e) {
                            throw new RuntimeException("The weight " + tuple[0] + " assigned to term " + tuple[1] + " is invalid.");
                        }
                        if (weight != 1) {
                            throw new RuntimeException("If the fitness function consists of a single term, its weight must be 1. However, " + tuple[0] + " has been provided.");
                        }
                        function = getFitnessFunction(tuple[1]);
                        break;
                    default:
                        throw new RuntimeException("Function specified with improper formatting. Remember to separate the name of the terms by the symbol +, and assign their weight by preceding them with a decimal followed by the symbol *.");
                }
                
            } else {
                FitnessFunction[] functions = new FitnessFunction[subformulas.length];
                Double[] weights = new Double[subformulas.length];
                double totalWeight = 0;

                for (int j = 0; j < subformulas.length; j++) {
                    String[] tuple = subformulas[j].split("\\*");
                    if (tuple.length != 2) {
                        throw new RuntimeException("Function specified with improper formatting. Remember to separate the name of the terms by the symbol +, and assign their weight by preceding them with a decimal followed by the symbol *.");
                    }

                    functions[j] = getFitnessFunction(tuple[1]);
                    try {
                        weights[j] = Double.parseDouble(tuple[0]);
                        totalWeight += weights[j];
                    } catch (Exception e) {
                        throw new RuntimeException("The weight " + tuple[0] + " assigned to term " + tuple[1] + " is invalid.");
                    }
                }

                if (totalWeight != 1) {
                    throw new RuntimeException("The weights of all the terms in the formula must add up to 1.");
                }

                function = (Map<String, Double> consensus, Double[] x) -> {
                    double res = 0;
                    for (int j = 0; j < functions.length; j++) {
                        res += weights[j] * functions[j].run(consensus, x);
                    }
                    return res;
                };
            }
            this.fitnessFunctions[i] = function;
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

        Map<String, Double> consensus = makeConsensus(x);
        for (int i = 0; i < fitnessFunctions.length; i++){
            solution.objectives()[i] = fitnessFunctions[i].run(consensus, x);
        }

        return solution;
    }

    /** GetFitnessFunction() method */
    private FitnessFunction getFitnessFunction(String str) {
        /** 
         * Function to return FitnessFunction object based on a string 
         */
        
        FitnessFunction res;
        switch (str.toLowerCase()) {
            case "topology":
                res = new Topology(this.geneNames.size(), this.cutOffCriteria);
                break;
            case "quality":
                res = new Quality(this.geneNames.size(), this.inferredNetworks);
                break;
            case "loyalty":
                res = new Loyalty(this.strTimeSeriesFile);
                break;
            default:
                throw new RuntimeException("The evaluation term " + str + " is not implemented.");
        }
        return res;
    }

    /** MakeConsensus() method */
    public Map<String, Double> makeConsensus(Double[] x) {
        /**
         * Elaborate the list of consensus links from the vector of weights
         * and the results provided by each technique.
         */

        Map<String, Double> consensus = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : inferredNetworks.entrySet()) {
            double confidence = 0.0;

            for (int i = 0; i < x.length; i++) {
                confidence += x[i] * pair.getValue()[i];
            }

            consensus.put(pair.getKey(), confidence);
        }

        return consensus;
    }

    @Override
    public void setName(String name) {
        super.setName(name);
    }
 
}
