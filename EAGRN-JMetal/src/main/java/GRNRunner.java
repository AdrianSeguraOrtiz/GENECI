import operator.mutationwithrepair.impl.*;
import operator.repairer.WeightRepairer;
import operator.repairer.impl.*;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.uma.jmetal.experimental.componentbasedalgorithm.algorithm.singleobjective.geneticalgorithm.GeneticAlgorithm;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.crossover.impl.*;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.operator.selection.impl.BinaryTournamentSelection;
import org.uma.jmetal.operator.selection.impl.NaryTournamentSelection;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.JMetalLogger;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;
import org.uma.jmetal.util.grouping.CollectionGrouping;
import org.uma.jmetal.util.grouping.impl.ListLinearGrouping;
import org.uma.jmetal.util.termination.Termination;
import org.uma.jmetal.util.termination.impl.TerminationByEvaluations;

import java.io.*;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

public class GRNRunner extends AbstractAlgorithmRunner {
    /**
     * @param args Command line arguments.
     * @throws JMetalException
     * @throws FileNotFoundException Invoking command: java
     *     org.uma.jmetal.runner.multiobjective.nsgaii.NSGAIIRunner problemName [referenceFront]
     */
    public static void main(String[] args) throws JMetalException, IOException {
        /** Declare the main execution variables */
        GRNProblem problem;
        GeneticAlgorithm<DoubleSolution> algorithm;
        CrossoverOperator<DoubleSolution> crossover;
        MutationOperator<DoubleSolution> mutation;
        WeightRepairer repairer;
        NaryTournamentSelection<DoubleSolution> selection;

        /** Read input parameters */
        String networkFolder;
        String strCrossover;
        String strMutation;
        String strRepairer;
        int populationSize;
        int numEvaluations;
        if (args.length == 6) {
            networkFolder = args[0];
            strCrossover = args[1];
            strMutation = args[2];
            strRepairer = args[3];
            populationSize = Integer.parseInt(args[4]);
            numEvaluations = Integer.parseInt(args[5]);
        } else {
            networkFolder = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/";
            strCrossover = "SBXCrossover";
            strMutation = "PolynomialMutation";
            strRepairer = "GreedyRepair";
            populationSize = 1000;
            numEvaluations = 10000;
        }

        /** Establish the chromosome repairer */
        switch (strRepairer) {
            case "StandardizationRepairer":
                repairer = new StandardizationRepairer();
                break;
            case "GreedyRepair":
                repairer = new GreedyRepairer();
                break;
            default:
                throw new RuntimeException("The repairer operator entered is not available");
        }

        /** List CSV files stored in the input folder with inferred lists of links */
        File dir = new File(networkFolder + "/lists/");
        FileFilter fileFilter = new WildcardFileFilter("*.csv");
        File[] files = dir.listFiles(fileFilter);

        /** Extracting gene names */
        File geneNamesFile = new File(networkFolder + "/gene_names.txt");
        String[] geneNames;
        try {
            Scanner sc = new Scanner(geneNamesFile);
            String line = sc.nextLine();
            geneNames = line.split(" ");
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        /** Initialize our problem with the extracted data */
        problem = new GRNProblem(files, geneNames, repairer);

        /** Set the crossover operator */
        double crossoverProbability = 0.9;
        double crossoverDistributionIndex = 20.0;
        int numPointsCrossover = 2;

        switch (strCrossover) {
            case "SBXCrossover":
                crossover = new SBXCrossover(crossoverProbability, crossoverDistributionIndex);
                break;
            case "BLXAlphaCrossover":
                crossover = new BLXAlphaCrossover(crossoverProbability);
                break;
            case "DifferentialEvolutionCrossover":
                crossover = new DifferentialEvolutionCrossover();
                break;
            case "NPointCrossover":
                crossover = new NPointCrossover(crossoverProbability, numPointsCrossover);
                break;
            case "NullCrossover":
                crossover = new NullCrossover();
                break;
            case "WholeArithmeticCrossover":
                crossover = new WholeArithmeticCrossover(crossoverProbability);
                break;
            default:
                throw new RuntimeException("The crossover operator entered is not available");
        }

        /** Set the mutation operator */
        double mutationProbability = 1.0 / problem.getNumberOfVariables();
        double mutationDistributionIndex = 20.0;
        double delta = 0.5;
        int numberOfGroups = 4;
        CollectionGrouping<List<Double>> grouping = new ListLinearGrouping<>(numberOfGroups);
        double perturbation = 0.5;
        int maxMutIterations = 10;

        switch (strMutation) {
            case "PolynomialMutation":
                mutation = new PolynomialMutationWithRepair(mutationProbability, mutationDistributionIndex, repairer);
                break;
            case "CDGMutation":
                mutation = new CDGMutationWithRepair(mutationProbability, delta, repairer);
                break;
            case "GroupedAndLinkedPolynomialMutation":
                mutation = new GroupedAndLinkedPolynomialMutationWithRepair(mutationDistributionIndex, grouping, repairer);
                break;
            case "GroupedPolynomialMutation":
                mutation = new GroupedPolynomialMutationWithRepair(mutationDistributionIndex, grouping, repairer);
                break;
            case "LinkedPolynomialMutation":
                mutation = new LinkedPolynomialMutationWithRepair(mutationProbability, mutationDistributionIndex, repairer);
                break;
            case "NonUniformMutation":
                mutation = new NonUniformMutationWithRepair(mutationProbability, perturbation, maxMutIterations, repairer);
                break;
            case "NullMutation":
                mutation = new NullMutationWithRepair(repairer);
                break;
            case "SimpleRandomMutation":
                mutation = new SimpleRandomMutationWithRepair(mutationProbability, repairer);
                break;
            case "UniformMutation":
                mutation = new UniformMutationWithRepair(mutationProbability, perturbation, repairer);
                break;
            default:
                throw new RuntimeException("The mutation operator entered is not available");
        }

        /** Start selection operator */
        selection = new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>());

        /** Instantiate the evolutionary algorithm indicating the size of the population and the maximum number of evaluations */
        int offspringPopulationSize = populationSize;
        Termination termination = new TerminationByEvaluations(numEvaluations);
        algorithm = new GeneticAlgorithm <>(
                        problem,
                        populationSize,
                        offspringPopulationSize,
                        selection,
                        crossover,
                        mutation,
                        termination);

        /** Add observable to report the evolution of fitness values. */
        algorithm.getObservable().register(new FitnessObserver(100));

        /** Execute the designed evolutionary algorithm */
        algorithm.run();

        /** Extract the population of the last iteration and the total execution time. */
        List<DoubleSolution> population = algorithm.getResult();
        long computingTime = algorithm.getTotalComputingTime();

        /** Transform the solution into a simple vector of weights. */
        double[] winner = new double[problem.getNumberOfVariables()];
        for (int i = 0; i < problem.getNumberOfVariables(); i++) {
            winner[i] = population.get(0).variables().get(i);
        }

        /** Calculate the consensus list corresponding to the solution vector. */
        Map<String, ConsensusTuple> consensus = problem.makeConsensus(winner);

        /** Calculate the binary matrix from the list above */
        double percMaxConf = 0.15;
        int[][] binaryNetwork = problem.getNetworkFromListWithConf(consensus, percMaxConf);

        /** Write the resulting binary matrix to an output csv file */
        try {
            File outputFile = new File(networkFolder + "ea_consensus/final_network.csv");
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            bw.write("," + String.join(",", geneNames));
            bw.newLine();
            for (int i = 0; i < binaryNetwork.length; i++) {
                bw.write(geneNames[i] + ",");
                for (int j = 0; j < binaryNetwork[i].length; j++) {
                    bw.write(binaryNetwork[i][j] + ((j == binaryNetwork[i].length - 1) ? "" : ","));
                }
                bw.newLine();
            }
            bw.flush();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Report the execution time and return the best solution found by the algorithm. */
        JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
        JMetalLogger.logger.info("The resulting binary matrix has been stored in" + networkFolder + "ea_consensus/final_network.csv");
        printFinalSolutionSet(population);
    }
}


