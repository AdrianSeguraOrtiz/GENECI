package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.cutoffcriteria.impl.MaxNumLinksBestConfCriteria;
import eagrn.cutoffcriteria.impl.MinConfFreqCriteria;
import eagrn.cutoffcriteria.impl.MinConfidenceCriteria;
import eagrn.operator.mutationwithrepair.impl.*;
import eagrn.operator.repairer.impl.GreedyRepairer;
import eagrn.operator.repairer.impl.StandardizationRepairer;
import eagrn.operator.repairer.WeightRepairer;
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
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.stream.Collectors;

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
        CutOffCriteria cutOffCriteria;

        /** Read input parameters */
        String networkFolder;
        String strCrossover;
        String strMutation;
        String strRepairer;
        int populationSize;
        int numEvaluations;
        String strCutOffCriteria;
        double cutOffValue;
        double f1Weight;
        double f2Weight;
        if (args.length == 10) {
            networkFolder = args[0];
            strCrossover = args[1];
            strMutation = args[2];
            strRepairer = args[3];
            populationSize = Integer.parseInt(args[4]);
            numEvaluations = Integer.parseInt(args[5]);
            strCutOffCriteria = args[6];
            cutOffValue = Double.parseDouble(args[7]);
            f1Weight = Double.parseDouble(args[8]);
            f2Weight = Double.parseDouble(args[9]);
        } else {
            networkFolder = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/";
            strCrossover = "SBXCrossover";
            strMutation = "PolynomialMutation";
            strRepairer = "GreedyRepair";
            populationSize = 100;
            numEvaluations = 10000;
            strCutOffCriteria = "MinConfFreq";
            cutOffValue = 0.2;
            f1Weight = 0.75;
            f2Weight = 0.25;
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
        ArrayList<String> geneNames;
        try {
            Scanner sc = new Scanner(geneNamesFile);
            String line = sc.nextLine();
            String[] lineSplit = line.split(",");
            geneNames = new ArrayList<>(List.of(lineSplit));
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        /** Establish the cut-off criteria */
        switch (strCutOffCriteria) {
            case "MinConfidence":
                cutOffCriteria = new MinConfidenceCriteria(cutOffValue);
                break;
            case "MaxNumLinksBestConf":
                cutOffCriteria = new MaxNumLinksBestConfCriteria((int) cutOffValue);
                break;
            case "MinConfFreq":
                cutOffCriteria = new MinConfFreqCriteria(cutOffValue, files.length);
                break;
            default:
                throw new RuntimeException("The cut-off criteria entered is not available");
        }

        /** Initialize our problem with the extracted data */
        problem = new GRNProblem(files, geneNames, repairer, cutOffCriteria, f1Weight, f2Weight);

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
        FitnessObserver fitnessObserver = new FitnessObserver(100);
        algorithm.getObservable().register(fitnessObserver);

        /** Execute the designed evolutionary algorithm */
        algorithm.run();

        /** Write the evolution of fitness values to an output txt file */
        try {
            File outputFile = new File(networkFolder + "ea_consensus/fitness_evolution.txt");
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));
            String strFitnessVector = fitnessObserver.getFitnessHistory().toString();
            bw.write(strFitnessVector.substring(1, strFitnessVector.length() - 1));
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Extract the population of the last iteration and the total execution time. */
        List<DoubleSolution> population = algorithm.getResult();
        long computingTime = algorithm.getTotalComputingTime();

        /** Transform the solution into a simple vector of weights. */
        double[] winner = new double[problem.getNumberOfVariables()];
        for (int i = 0; i < problem.getNumberOfVariables(); i++) {
            winner[i] = population.get(0).variables().get(i);
        }

        /** Write the list of weights assigned to each technique in an output txt file */
        try {
            File outputFile = new File(networkFolder + "ea_consensus/final_weights.txt");
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            String filename;
            for (int i = 0; i < winner.length; i++) {
                filename = files[i].getName();
                bw.write(filename.substring(4, filename.lastIndexOf('.')) + ": " + winner[i]);
                bw.newLine();
            }
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Calculate the consensus list corresponding to the solution vector. */
        Map<String, ConsensusTuple> consensus = problem.makeConsensus(winner)
            .entrySet()
            .stream()
            .sorted(Map.Entry.<String, ConsensusTuple>comparingByValue())
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue,
                (e1, e2) -> e1, LinkedHashMap::new));

        /** Write the resulting list of links to an output csv file */
        try {
            File outputFile = new File(networkFolder + "ea_consensus/final_list.csv");
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
                String [] vKeySplit = pair.getKey().split("-");
                bw.write(vKeySplit[0] + "," + vKeySplit[1] + "," + pair.getValue().getConf());
                bw.newLine();
            }
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Calculate the binary matrix from the list above */
        int[][] binaryNetwork = cutOffCriteria.getNetworkFromConsensus(consensus, geneNames);

        /** Write the resulting binary matrix to an output csv file */
        try {
            File outputFile = new File(networkFolder + "ea_consensus/final_network.csv");
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            bw.write("," + String.join(",", geneNames));
            bw.newLine();
            for (int i = 0; i < binaryNetwork.length; i++) {
                bw.write(geneNames.get(i) + ",");
                for (int j = 0; j < binaryNetwork[i].length; j++) {
                    bw.write(binaryNetwork[i][j] + ((j == binaryNetwork[i].length - 1) ? "" : ","));
                }
                bw.newLine();
            }
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Report the execution time and return the best solution found by the algorithm. */
        JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
        JMetalLogger.logger.info("The resulting list of links has been stored in" + networkFolder + "ea_consensus/final_list.csv");
        JMetalLogger.logger.info("The resulting binary matrix has been stored in" + networkFolder + "ea_consensus/final_network.csv");
        JMetalLogger.logger.info("The evolution of fitness values has been stored in" + networkFolder + "ea_consensus/fitness_evolution.txt");
        JMetalLogger.logger.info("List of the weights assigned to each technique has been stored in" + networkFolder + "ea_consensus/final_weights.txt");
    }
}


