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
import org.uma.jmetal.util.grouping.CollectionGrouping;
import org.uma.jmetal.util.grouping.impl.ListLinearGrouping;

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
        String[] geneNames;
        String strCrossover;
        String strMutation;
        String strRepairer;
        if (args.length == 5) {
            networkFolder = args[0];
            geneNames = args[1].split(",");
            strCrossover = args[2];
            strMutation = args[3];
            strRepairer = args[4];
        } else {
            networkFolder = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/";
            geneNames = new String[]{"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10"};
            strCrossover = "SBXCrossover";
            strMutation = "PolynomialMutation";
            strRepairer = "StandardizationRepairer";
        }

        switch (strRepairer) {
            case "StandardizationRepairer": repairer = new StandardizationRepairer();
                break;
            case "GreedyRepair": repairer = new GreedyRepairer();
                break;
            default: throw new RuntimeException("The repairer operator entered is not available");
        }

        File dir = new File(networkFolder);
        FileFilter fileFilter = new WildcardFileFilter("*.csv");
        File[] files = dir.listFiles(fileFilter);
        problem = new GRNProblem(files, geneNames, repairer);

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
        double delta = 0.5;
        int numberOfGroups = 4;
        CollectionGrouping<List<Double>> grouping = new ListLinearGrouping<>(numberOfGroups);
        double perturbation = 0.5;
        int maxMutIterations = 10;

        switch (strMutation) {
            case "PolynomialMutation": mutation = new PolynomialMutationWithRepair(mutationProbability, mutationDistributionIndex, repairer);
                break;
            case "CDGMutation": mutation = new CDGMutationWithRepair(mutationProbability, delta, repairer);
                break;
            case "GroupedAndLinkedPolynomialMutation": mutation = new GroupedAndLinkedPolynomialMutationWithRepair(mutationDistributionIndex, grouping, repairer);
                break;
            case "GroupedPolynomialMutation": mutation = new GroupedPolynomialMutationWithRepair(mutationDistributionIndex, grouping, repairer);
                break;
            case "LinkedPolynomialMutation": mutation = new LinkedPolynomialMutationWithRepair(mutationProbability, mutationDistributionIndex, repairer);
                break;
            case "NonUniformMutation": mutation = new NonUniformMutationWithRepair(mutationProbability, perturbation, maxMutIterations, repairer);
                break;
            case "NullMutation": mutation = new NullMutationWithRepair(repairer);
                break;
            case "SimpleRandomMutation": mutation = new SimpleRandomMutationWithRepair(mutationProbability, repairer);
                break;
            case "UniformMutation": mutation = new UniformMutationWithRepair(mutationProbability, perturbation, repairer);
                break;
            default: throw new RuntimeException("The mutation operator entered is not available");
        }

        selection = new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>());

        int populationSize = 6;
        algorithm = new NSGAIIBuilder<>(problem, crossover, mutation, populationSize)
                        .setSelectionOperator(selection)
                        .setMaxEvaluations(12)
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
        Map<String, ConsensusTuple> consensus = problem.makeConsensus(winner);

        consensus.entrySet().forEach(entry -> {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        });
    }
}


