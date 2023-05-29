package eagrn;

import eagrn.algorithm.AsynchronousMultiThreadedGeneticAlgorithmGoodParents;
import eagrn.algorithm.AsynchronousMultiThreadedNSGAIIGoodParents;
import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.operator.crossover.SimplexCrossover;
import eagrn.operator.mutation.SimplexMutation;
import eagrn.utils.fitnessevolution.GRNProblemFitnessEvolution;
import eagrn.utils.fitnessevolution.impl.GRNProblemBestFitnessEvolution;
import eagrn.utils.solutionlistoutputwithheader.SolutionListOutputWithHeader;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.algorithm.multiobjective.smpso.SMPSOBuilder;
import org.uma.jmetal.example.AlgorithmRunner;
import org.uma.jmetal.experimental.componentbasedalgorithm.algorithm.singleobjective.geneticalgorithm.GeneticAlgorithm;
import org.uma.jmetal.experimental.componentbasedalgorithm.catalogue.replacement.Replacement;
import org.uma.jmetal.experimental.componentbasedalgorithm.catalogue.replacement.impl.MuPlusLambdaReplacement;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.operator.selection.impl.BinaryTournamentSelection;
import org.uma.jmetal.operator.selection.impl.NaryTournamentSelection;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.archive.BoundedArchive;
import org.uma.jmetal.util.archive.impl.CrowdingDistanceArchive;
import org.uma.jmetal.util.comparator.ObjectiveComparator;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.MultiThreadedSolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;
import org.uma.jmetal.util.fileoutput.impl.DefaultFileOutputContext;
import org.uma.jmetal.util.termination.Termination;
import org.uma.jmetal.util.termination.impl.TerminationByEvaluations;
import org.uma.jmetal.util.SolutionListUtils;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class GRNRunner extends AbstractAlgorithmRunner {
    /**
     * @param args Command line arguments.
     * @throws FileNotFoundException Invoking command: java
     *                               org.uma.jmetal.runner.multiobjective.nsgaii.NSGAIIRunner
     *                               problemName [referenceFront]
     *                               .
     */
    public static void main(String[] args) throws IOException {
        /** Config sort. NOTE: https://github.com/jMetal/jMetal/issues/446 */
        System.setProperty("java.util.Arrays.useLegacyMergeSort", "true");

        /** Declare the main execution variables. */
        GRNProblem problem;
        CrossoverOperator<DoubleSolution> crossover;
        MutationOperator<DoubleSolution> mutation;
        NaryTournamentSelection<DoubleSolution> selection;
        CutOffCriteria cutOffCriteria;

        /** Read input parameters. */
        String networkFolder;
        double crossoverProbability;
        int numParents;
        double mutationProbability;
        int populationSize;
        int numEvaluations;
        String strCutOffCriteria;
        float cutOffValue;
        String strFitnessFormulas;
        String strAlgorithm;
        int numOfThreads;
        boolean printEvolution;

        if (args.length > 0) {
            networkFolder = args[0];

            if (args.length == 11) {
                crossoverProbability = Double.parseDouble(args[1]);
                numParents = Integer.parseInt(args[2]);
                mutationProbability = Double.parseDouble(args[3]);
                populationSize = Integer.parseInt(args[4]);
                numEvaluations = Integer.parseInt(args[5]);
                strCutOffCriteria = args[6];
                cutOffValue = Float.parseFloat(args[7]);
                strFitnessFormulas = args[8];
                strAlgorithm = args[9];
                numOfThreads = Integer.parseInt(args[10]);
                printEvolution = Boolean.parseBoolean(args[11]);

            } else {
                crossoverProbability = 0.9;
                numParents = 3;
                mutationProbability = 0.1;
                populationSize = 100;
                numEvaluations = 25000;
                strCutOffCriteria = "MinConf";
                cutOffValue = 0.5f;
                strFitnessFormulas = "Quality;DegreeDistribution";
                strAlgorithm = "NSGAII";
                numOfThreads = Runtime.getRuntime().availableProcessors();
                printEvolution = false;
            }
        } else {
            throw new RuntimeException("At least the folder with the input trust lists must be provided.");
        }

        /**
         * Refine the name of the algorithm to be executed according to the specified
         * number of threads
         */
        if (numOfThreads < 0) {
            throw new RuntimeException("The number of threads must be a positive number.");

        } else if (numOfThreads > Runtime.getRuntime().availableProcessors()) {
            throw new RuntimeException(
                    "The specified number of threads is greater than that available on your device.");

        } else if (numOfThreads == 1) {
            strAlgorithm += "-SingleThread";

        } else if (numOfThreads > 1) {
            if (strAlgorithm.equals("GA") || strAlgorithm.equals("NSGAII")) {
                strAlgorithm += "-AsyncParallel";

            } else {
                strAlgorithm += "-SyncParallel";
            }
        }

        /** List CSV files stored in the input folder with inferred lists of links. */
        File[] files = StaticUtils.getCSVFilesFromDirectory(networkFolder + "/lists/");

        /** Extract inferred networks */
        Map<String, Float[]> inferredNetworks = StaticUtils.readAllInferredNetworkFiles(files);

        /** Extracting gene names. */
        ArrayList<String> geneNames = StaticUtils.getGeneNames(networkFolder + "/gene_names.txt");

        /** Extract the path to the file with the time series if provided */
        String strTimeSeriesFile = networkFolder + "/time_series.csv";
        if (!Files.exists(Paths.get(strTimeSeriesFile))) {
            strTimeSeriesFile = null;
        }

        /** Establish the cut-off criteria. */
        cutOffCriteria = StaticUtils.getCutOffCriteriaFromString(strCutOffCriteria, cutOffValue, geneNames);

        /** Initialize our problem with the extracted data. */
        if (printEvolution) {
            problem = new GRNProblemBestFitnessEvolution(inferredNetworks, geneNames, cutOffCriteria,
                    strFitnessFormulas, strTimeSeriesFile);
        } else {
            problem = new GRNProblem(inferredNetworks, geneNames, cutOffCriteria, strFitnessFormulas,
                    strTimeSeriesFile);
        }

        /** Set the crossover operator. */
        crossover = new SimplexCrossover(numParents, 1, crossoverProbability);

        /** Set the mutation operator. */
        mutation = new SimplexMutation(mutationProbability, 0.1);

        /** Start selection operator. */
        selection = new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>());

        /**
         * Declare variable to contain the runtime and another to store the last
         * generation of individuals.
         */
        long computingTime;
        List<DoubleSolution> population;

        /** Instantiate some variables needed for the different algorithms. */
        Termination termination = new TerminationByEvaluations(numEvaluations);
        Replacement<DoubleSolution> replacement = new MuPlusLambdaReplacement<>(new ObjectiveComparator<>(0));
        int offspringPopulationSize = populationSize;

        /** Configure the specified evolutionary algorithm. */
        if (problem.getNumberOfObjectives() == 1) {
            if (strAlgorithm.equals("GA-SingleThread")) {
                /** Instantiate the evolutionary algorithm. */
                GeneticAlgorithm<DoubleSolution> algorithm = new GeneticAlgorithm<DoubleSolution>(
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
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else if (strAlgorithm.equals("GA-AsyncParallel")) {
                /** Activate stopwatch. */
                long initTime = System.currentTimeMillis();

                /** Instantiate the evolutionary algorithm. */
                AsynchronousMultiThreadedGeneticAlgorithmGoodParents<DoubleSolution> algorithm = new AsynchronousMultiThreadedGeneticAlgorithmGoodParents<DoubleSolution>(
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
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else {
                throw new RuntimeException(
                        "The algorithm " + strAlgorithm + " is not available for single-objetive problems.");
            }
        } else {
            if (strAlgorithm.equals("NSGAII-SingleThread")) {
                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm = new NSGAIIBuilder<>(problem, crossover, mutation,
                        populationSize)
                        .setSelectionOperator(selection)
                        .setMaxEvaluations(numEvaluations)
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();

                /** Extract the population of the last iteration. */
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else if (strAlgorithm.equals("NSGAII-AsyncParallel")) {
                /** Activate stopwatch. */
                long initTime = System.currentTimeMillis();

                /** Instantiate the evolutionary algorithm. */
                AsynchronousMultiThreadedNSGAIIGoodParents<DoubleSolution> algorithm = new AsynchronousMultiThreadedNSGAIIGoodParents<DoubleSolution>(
                        numOfThreads,
                        problem,
                        populationSize,
                        crossover,
                        mutation,
                        termination);

                /** Execute the designed evolutionary algorithm. */
                algorithm.run();

                /** Stop stopwatch and calculate the total execution time. */
                long endTime = System.currentTimeMillis();
                computingTime = endTime - initTime;

                /** Extract the population of the last iteration. */
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else if (strAlgorithm.equals("SMPSO-SingleThread")) {
                /** Create archive */
                BoundedArchive<DoubleSolution> archive = new CrowdingDistanceArchive<>(populationSize);

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm = new SMPSOBuilder(problem, archive)
                        .setMutation(mutation)
                        .setMaxIterations(numEvaluations / populationSize)
                        .setSwarmSize(populationSize)
                        .setSolutionListEvaluator(new SequentialSolutionListEvaluator<DoubleSolution>())
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();

                /** Extract the population of the last iteration. */
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else if (strAlgorithm.equals("SMPSO-SyncParallel")) {
                /** Create archive */
                BoundedArchive<DoubleSolution> archive = new CrowdingDistanceArchive<>(populationSize);

                /** Instantiate the evaluator */
                SolutionListEvaluator<DoubleSolution> evaluator = new MultiThreadedSolutionListEvaluator<DoubleSolution>(
                        numOfThreads);

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm = new SMPSOBuilder(problem, archive)
                        .setMutation(mutation)
                        .setMaxIterations(numEvaluations / populationSize)
                        .setSwarmSize(populationSize)
                        .setSolutionListEvaluator(evaluator)
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();

                /** Extract the population of the last iteration. */
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

                /** Stop the evaluator */
                evaluator.shutdown();

            } else {
                throw new RuntimeException(
                        "The algorithm " + strAlgorithm + " is not available for multi-objetive problems.");
            }
        }

        /** Create output folder. */
        String outputFolder = networkFolder + "/ea_consensus/";
        try {
            Files.createDirectories(Paths.get(outputFolder));
        } catch (IOException ioe) {
            throw new RuntimeException(ioe);
        }

        /** Write the evolution of fitness values to an output txt file. */
        if (printEvolution) {
            Map<String, Double[]> fitnessEvolution = ((GRNProblemFitnessEvolution) problem).getFitnessEvolution();
            StaticUtils.writeFitnessEvolution(outputFolder + "/fitness_evolution.txt", fitnessEvolution);
        }

        /** Get files (techniques) tags */
        String[] tags = new String[files.length];
        for (int i = 0; i < files.length; i++) {
            tags[i] = files[i].getName();
        }

        /** Write the data of the last population (pareto front approximation). */
        new SolutionListOutputWithHeader(population, strFitnessFormulas.split(";"), tags)
                .setVarFileOutputContext(new DefaultFileOutputContext(outputFolder + "/VAR.csv", ","))
                .setFunFileOutputContext(new DefaultFileOutputContext(outputFolder + "/FUN.csv", ","))
                .print();

        if (problem.getNumberOfObjectives() == 1) {
            /** Transform the solution into a simple vector of weights. */
            Double[] winner = new Double[problem.getNumberOfVariables()];
            for (int i = 0; i < problem.getNumberOfVariables(); i++) {
                winner[i] = population.get(0).variables().get(i);
            }

            /** Get weighted confidence map from winner. */
            Map<String, Float> consensus = StaticUtils.makeConsensus(winner, inferredNetworks);
            Map<String, Float> consensusSorted = new LinkedHashMap<>();
            consensus.entrySet()
                    .stream()
                    .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
                    .forEachOrdered(x -> consensusSorted.put(x.getKey(), x.getValue()));

            /** Write the resulting list of links to an output csv file. */
            StaticUtils.writeConsensus(outputFolder + "/final_list.csv", consensusSorted);

            /** Calculate the binary matrix from the list above. */
            boolean[][] binaryNetwork = cutOffCriteria.getNetwork(consensusSorted);

            /** Write the resulting binary matrix to an output csv file. */
            StaticUtils.writeBinaryNetwork(outputFolder + "/final_network.csv", binaryNetwork, geneNames);
        }

        /**
         * Report the execution time and return the best solution found by the
         * algorithm.
         */
        System.out.println("Evolutionary algorithm executed: " + strAlgorithm);
        System.out.println("Threads used: " + numOfThreads);
        System.out.println("Total execution time: " + computingTime + "ms");
        System.out.println("The weights assigned to each technique/input-file have been stored in VAR.csv");
        System.out.println("The fitness values for each of the solutions have been stored in FUN.csv");

        if (printEvolution) {
            System.out.println(
                    "The evolution of fitness values has been stored in " + outputFolder + "/fitness_evolution.txt");
        }

        if (problem.getNumberOfObjectives() == 1) {
            System.out.println("The resulting list of links has been stored in " + outputFolder + "/final_list.csv");
            System.out.println("The resulting binary matrix has been stored in " + outputFolder + "/final_network.csv");
        }

        System.exit(0);
    }
}
