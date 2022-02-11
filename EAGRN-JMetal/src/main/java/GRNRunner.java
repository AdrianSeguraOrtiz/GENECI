import operator.mutationwithrepair.impl.*;
import operator.repairer.WeightRepairer;
import operator.repairer.impl.*;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.example.AlgorithmRunner;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.crossover.impl.*;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.operator.selection.SelectionOperator;
import org.uma.jmetal.operator.selection.impl.BinaryTournamentSelection;
import org.uma.jmetal.qualityindicator.QualityIndicatorUtils;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.*;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;

import java.io.File;
import java.io.FileFilter;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class GRNRunner extends AbstractAlgorithmRunner {
    /**
     * @param args Command line arguments.
     * @throws JMetalException
     * @throws FileNotFoundException Invoking command: java
     *     org.uma.jmetal.runner.multiobjective.nsgaii.NSGAIIRunner problemName [referenceFront]
     */
    public static void main(String[] args) throws JMetalException, IOException {
        GRNProblem problem;
        Algorithm<List<DoubleSolution>> algorithm;
        CrossoverOperator<DoubleSolution> crossover;
        MutationOperator<DoubleSolution> mutation;
        WeightRepairer repairer;
        SelectionOperator<List<DoubleSolution>, DoubleSolution> selection;
        String referenceParetoFront = "";

        String networkFolder;
        String strCrossover;
        String strMutation;
        String strRepairer;
        if (args.length == 3) {
            networkFolder = args[0];
            strCrossover = args[1];
            strMutation = args[2];
            strRepairer = args[3];
        } else {
            networkFolder = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/";
            strCrossover = "SBXCrossover";
            strMutation = "PolynomialMutation";
            strRepairer = "StandardizationRepairer";
        }

        switch (strRepairer) {
            case "StandardizationRepairer": repairer = new StandardizationRepairer();
                break;
            default: throw new RuntimeException("The repairer operator entered is not available");
        }

        File dir = new File(networkFolder);
        FileFilter fileFilter = new WildcardFileFilter("*.csv");
        File[] files = dir.listFiles(fileFilter);
        problem = new GRNProblem(files, repairer);

        double crossoverProbability = 0.9;
        double crossoverDistributionIndex = 20.0;
        int numPointsCrossover = 2;
        switch (strCrossover) {
            case "SBXCrossover":  crossover = new SBXCrossover(crossoverProbability, crossoverDistributionIndex);;
                break;
            case "BLXAlphaCrossover":  crossover = new BLXAlphaCrossover(crossoverProbability);
                break;
            case "DifferentialEvolutionCrossover":  crossover = new DifferentialEvolutionCrossover();
                break;
            case "NPointCrossover":  crossover = new NPointCrossover(crossoverProbability, numPointsCrossover);
                break;
            case "NullCrossover":  crossover = new NullCrossover();
                break;
            case "WholeArithmeticCrossover":  crossover = new WholeArithmeticCrossover(crossoverProbability);
                break;
            default: throw new RuntimeException("The crossover operator entered is not available");
        }

        double mutationProbability = 1.0 / problem.getNumberOfVariables();
        double mutationDistributionIndex = 20.0;
        switch (strMutation) {
            case "PolynomialMutation": mutation = new PolynomialMutationWithRepair(mutationProbability, mutationDistributionIndex, repairer);
                break;
            default: throw new RuntimeException("The mutation operator entered is not available");
        }

        selection = new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>());

        int populationSize = 100;
        algorithm = new NSGAIIBuilder<>(problem, crossover, mutation, populationSize)
                        .setSelectionOperator(selection)
                        .setMaxEvaluations(10000)
                        .build();

        AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

        List<DoubleSolution> population = algorithm.getResult();
        long computingTime = algorithmRunner.getComputingTime();

        JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");

        printFinalSolutionSet(population);
        if (!referenceParetoFront.equals("")) {
            QualityIndicatorUtils.printQualityIndicators(
                    SolutionListUtils.getMatrixWithObjectiveValues(population),
                    VectorUtils.readVectors(referenceParetoFront, ","));
        }

        double[] winner = new double[problem.getNumberOfVariables()];
        for (int i = 0; i < problem.getNumberOfVariables(); i++) {
            winner[i] = population.get(0).variables().get(i);
        }
        Map<String, Double> consensus = problem.makeConsensus(winner);

        consensus.entrySet().forEach(entry -> {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        });
    }
}


