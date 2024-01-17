package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.cutoffcriteria.impl.MaxNumLinksBestConfCriteria;
import eagrn.cutoffcriteria.impl.MinConfDistCriteria;
import eagrn.cutoffcriteria.impl.MinConfidenceCriteria;
import eagrn.operator.mutationwithrepair.impl.*;
import eagrn.operator.repairer.impl.GreedyRepairer;
import eagrn.operator.repairer.impl.StandardizationRepairer;
import eagrn.operator.repairer.WeightRepairer;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.uma.jmetal.experimental.componentbasedalgorithm.algorithm.ComponentBasedEvolutionaryAlgorithm;
import org.uma.jmetal.experimental.componentbasedalgorithm.algorithm.singleobjective.geneticalgorithm.GeneticAlgorithm;
import org.uma.jmetal.experimental.componentbasedalgorithm.catalogue.evaluation.impl.MultithreadedEvaluation;
import org.uma.jmetal.experimental.componentbasedalgorithm.catalogue.replacement.Replacement;
import org.uma.jmetal.experimental.componentbasedalgorithm.catalogue.replacement.impl.MuPlusLambdaReplacement;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.crossover.impl.*;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.operator.selection.impl.BinaryTournamentSelection;
import org.uma.jmetal.operator.selection.impl.NaryTournamentSelection;
import org.uma.jmetal.parallel.asynchronous.algorithm.impl.AsynchronousMultiThreadedGeneticAlgorithm;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.comparator.ObjectiveComparator;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;
import org.uma.jmetal.util.grouping.CollectionGrouping;
import org.uma.jmetal.util.grouping.impl.ListLinearGrouping;
import org.uma.jmetal.util.termination.Termination;
import org.uma.jmetal.util.termination.impl.TerminationByEvaluations;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
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
    . */
    public static void main(String[] args) throws JMetalException, IOException {
        /** Declare the main execution variables. */
        GRNProblem problem;
        CrossoverOperator<DoubleSolution> crossover;
        MutationOperator<DoubleSolution> mutation;
        WeightRepairer repairer;
        NaryTournamentSelection<DoubleSolution> selection;
        CutOffCriteria cutOffCriteria;

        /** Read input parameters. */
        String networkFolder;
        String strCrossover;
        double crossoverProbability;
        String strMutation;
        double mutationProbability;
        String strRepairer;
        String strMemeticDistanceType;
        double memeticPropability;
        int populationSize;
        int numEvaluations;
        String strCutOffCriteria;
        double cutOffValue;
        double qualityWeight;
        double topologyWeight;
        String strAlgorithm;
        int numOfThreads;

        if (args.length > 0) {
            networkFolder = args[0];

            if (args.length == 16) {
                strCrossover = args[1];
                crossoverProbability = Double.parseDouble(args[2]);
                strMutation = args[3];
                mutationProbability = Double.parseDouble(args[4]);
                strRepairer = args[5];
                strMemeticDistanceType = args[6];
                memeticPropability = Double.parseDouble(args[7]);
                populationSize = Integer.parseInt(args[8]);
                numEvaluations = Integer.parseInt(args[9]);
                strCutOffCriteria = args[10];
                cutOffValue = Double.parseDouble(args[11]);
                qualityWeight = Double.parseDouble(args[12]);
                topologyWeight = Double.parseDouble(args[13]);
                strAlgorithm = args[14];
                numOfThreads = Integer.parseInt(args[15]);
                
            } else {
                strCrossover = "SBXCrossover";
                crossoverProbability = 0.9;
                strMutation = "PolynomialMutation";
                mutationProbability = 0.1;
                strRepairer = "StandardizationRepairer";
                strMemeticDistanceType = "some";
                memeticPropability = 0.1;
                populationSize = 100;
                numEvaluations = 10000;
                strCutOffCriteria = "MinConfDist";
                cutOffValue = 0.5;
                qualityWeight = 0.75;
                topologyWeight = 0.25;
                strAlgorithm = "AsyncParallel";
                numOfThreads = Runtime.getRuntime().availableProcessors();
            }
        } else {
            throw new RuntimeException("At least the folder with the input trust lists must be provided.");
        }

        /** List CSV files stored in the input folder with inferred lists of links. */
        File dir = new File(networkFolder + "/lists/");
        FileFilter fileFilter = new WildcardFileFilter("*.csv");
        File[] files = dir.listFiles(fileFilter);

        /** Extract the path to the file with the known interactions if provided */
        String strKnownInteractionsFile = networkFolder + "/known_interactions.csv";
        if (!Files.exists(Paths.get(strKnownInteractionsFile))) {
            strKnownInteractionsFile = null;
        }

        /** Establish the chromosome repairer. */
        switch (strRepairer) {
            case "StandardizationRepairer":
                repairer = new StandardizationRepairer(strKnownInteractionsFile, GRNProblem.readAll(files), strMemeticDistanceType, memeticPropability);
                break;
            case "GreedyRepair":
                repairer = new GreedyRepairer(strKnownInteractionsFile, GRNProblem.readAll(files), strMemeticDistanceType, memeticPropability);
                break;
            default:
                throw new RuntimeException("The repairer operator entered is not available");
        }

        /** Extracting gene names. */
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

        /** Establish the cut-off criteria. */
        switch (strCutOffCriteria) {
            case "MinConfidence":
                cutOffCriteria = new MinConfidenceCriteria(cutOffValue);
                break;
            case "MaxNumLinksBestConf":
                cutOffCriteria = new MaxNumLinksBestConfCriteria((int) cutOffValue);
                break;
            case "MinConfDist":
                cutOffCriteria = new MinConfDistCriteria(cutOffValue);
                break;
            default:
                throw new RuntimeException("The cut-off criteria entered is not available");
        }

        /** Initialize our problem with the extracted data. */
        problem = new GRNProblem(files, geneNames, repairer, cutOffCriteria, qualityWeight, topologyWeight);

        /** Set the crossover operator. */
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

        /** Set the mutation operator. */
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

        /** Start selection operator. */
        selection = new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>());

        /** Declare variable to contain the runtime and another to store the last generation of individuals. */
        long computingTime;
        List<DoubleSolution> population;

        /** Instantiate some variables needed for the different algorithms. */
        Termination termination = new TerminationByEvaluations(numEvaluations);
        Replacement<DoubleSolution> replacement = new MuPlusLambdaReplacement<>(new ObjectiveComparator<>(0));
        int offspringPopulationSize = populationSize;

        /** Configure the specified evolutionary algorithm. */
        if (strAlgorithm.equals("AsyncParallel")) {
            /** Activate stopwatch. */
            long initTime = System.currentTimeMillis();

            /** Instantiate the evolutionary algorithm. */
            AsynchronousMultiThreadedGeneticAlgorithm<DoubleSolution> algorithm
                 = new AsynchronousMultiThreadedGeneticAlgorithm <DoubleSolution>(
                        numOfThreads,
                        problem,
                        populationSize,
                        crossover,
                        mutation,
                        selection,
                        replacement,
                        termination);

            /** Execute the designed evolutionary algorithm. */
            algorithm.run();
    
            /** Stop stopwatch and calculate the total execution time. */
            long endTime = System.currentTimeMillis();
            computingTime = endTime - initTime;

            /** Extract the population of the last iteration. */
            population = algorithm.getResult();

        } else if (strAlgorithm.equals("SyncParallel")) {
            /** Instantiate the evolutionary algorithm. */
            ComponentBasedEvolutionaryAlgorithm<DoubleSolution> algorithm
                 = new GeneticAlgorithm <DoubleSolution>(
                        problem,
                        populationSize,
                        offspringPopulationSize,
                        selection,
                        crossover,
                        mutation,
                        termination).withEvaluation(new MultithreadedEvaluation<>(numOfThreads, problem));

            /** Execute the designed evolutionary algorithm. */
            algorithm.run();

            /** Extract the total execution time. */
            computingTime = algorithm.getTotalComputingTime();

            /** Extract the population of the last iteration. */
            population = algorithm.getResult();

        } else if (strAlgorithm.equals("SingleThread")) {
            /** Instantiate the evolutionary algorithm. */
            GeneticAlgorithm<DoubleSolution> algorithm 
                = new GeneticAlgorithm <DoubleSolution>(
                        problem,
                        populationSize,
                        offspringPopulationSize,
                        selection,
                        crossover,
                        mutation,
                        termination);

            /** Execute the designed evolutionary algorithm. */
            algorithm.run();

            /** Extract the total execution time. */
            computingTime = algorithm.getTotalComputingTime();

            /** Extract the population of the last iteration. */
            population = algorithm.getResult();

        } else {
            throw new RuntimeException("The algorithm name entered is not available");
        }

        /** Create output folder. */
        String outputFolder = networkFolder + "/ea_consensus/";
        try {
            Files.createDirectories(Paths.get(outputFolder));
        } catch (IOException ioe) {
            throw new RuntimeException(ioe);
        }

        /** Write the evolution of fitness values to an output txt file. */
        try {
            File outputFile = new File(outputFolder + "/fitness_evolution.txt");
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            Map<String, Double[]> fitnessEvolution = problem.getFitnessEvolution();

            String strFitnessVector = Arrays.toString(fitnessEvolution.get("Fitness"));
            bw.write(strFitnessVector.substring(1, strFitnessVector.length() - 1) + "\n");

            String strF1Vector = Arrays.toString(fitnessEvolution.get("F1"));
            bw.write(strF1Vector.substring(1, strF1Vector.length() - 1) + "\n");
            
            String strF2Vector = Arrays.toString(fitnessEvolution.get("F2"));
            bw.write(strF2Vector.substring(1, strF2Vector.length() - 1) + "\n");

            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe);
        }

        /** Transform the solution into a simple vector of weights. */
        double[] winner = new double[problem.getNumberOfVariables()];
        for (int i = 0; i < problem.getNumberOfVariables(); i++) {
            winner[i] = population.get(0).variables().get(i);
        }

        /** Write the list of weights assigned to each technique in an output txt file. */
        try {
            File outputFile = new File(outputFolder + "/final_weights.txt");
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

        /** Write the resulting list of links to an output csv file. */
        try {
            File outputFile = new File(outputFolder + "/final_list.csv");
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
                String [] vKeySplit = pair.getKey().split(";");
                bw.write(vKeySplit[0] + "," + vKeySplit[1] + "," + pair.getValue().getConf());
                bw.newLine();
            }
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }

        /** Calculate the binary matrix from the list above. */
        int[][] binaryNetwork = cutOffCriteria.getNetworkFromConsensus(consensus, geneNames);

        /** Write the resulting binary matrix to an output csv file. */
        try {
            File outputFile = new File(outputFolder + "/final_network.csv");
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
        System.out.println("Evolutionary algorithm executed: " + strAlgorithm);
        System.out.println("Threads used: " + numOfThreads);
        System.out.println("Total execution time: " + computingTime + "ms");
        System.out.println("The resulting list of links has been stored in " + outputFolder + "/final_list.csv");
        System.out.println("The resulting binary matrix has been stored in " + outputFolder + "/final_network.csv");
        System.out.println("The evolution of fitness values has been stored in " + outputFolder + "/fitness_evolution.txt");
        System.out.println("List of the weights assigned to each technique has been stored in " + outputFolder + "/final_weights.txt");
        System.exit(0);
    }
}


