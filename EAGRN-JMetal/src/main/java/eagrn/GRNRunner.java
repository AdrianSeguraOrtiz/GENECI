package eagrn;

import eagrn.algorithm.impl.GDE3BuilderWithRepair;
import eagrn.algorithm.impl.SMPSOCorrectMutationBuilder;
import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.operator.mutationwithrepair.impl.*;
import eagrn.operator.repairer.WeightRepairer;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.moead.MOEADBuilder;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.example.AlgorithmRunner;
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
import org.uma.jmetal.parallel.asynchronous.algorithm.impl.AsynchronousMultiThreadedNSGAII;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.archive.BoundedArchive;
import org.uma.jmetal.util.archive.impl.CrowdingDistanceArchive;
import org.uma.jmetal.util.comparator.ObjectiveComparator;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.MultiThreadedSolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;
import org.uma.jmetal.util.fileoutput.SolutionListOutput;
import org.uma.jmetal.util.fileoutput.impl.DefaultFileOutputContext;
import org.uma.jmetal.util.grouping.CollectionGrouping;
import org.uma.jmetal.util.grouping.impl.ListLinearGrouping;
import org.uma.jmetal.util.termination.Termination;
import org.uma.jmetal.util.termination.impl.TerminationByEvaluations;
import org.uma.jmetal.util.SolutionListUtils;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
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
        int populationSize;
        int numEvaluations;
        String strCutOffCriteria;
        double cutOffValue;
        String strFitnessFormulas;
        String strAlgorithm;
        int numOfThreads;
        boolean printEvolution;

        if (args.length > 0) {
            networkFolder = args[0];

            if (args.length == 14) {
                strCrossover = args[1];
                crossoverProbability = Double.parseDouble(args[2]);
                strMutation = args[3];
                mutationProbability = Double.parseDouble(args[4]);
                strRepairer = args[5];
                populationSize = Integer.parseInt(args[6]);
                numEvaluations = Integer.parseInt(args[7]);
                strCutOffCriteria = args[8];
                cutOffValue = Double.parseDouble(args[9]);
                strFitnessFormulas = args[10];
                strAlgorithm = args[11];
                numOfThreads = Integer.parseInt(args[12]);
                printEvolution = Boolean.parseBoolean(args[13]);
                
            } else {
                strCrossover = "SBXCrossover";
                crossoverProbability = 0.9;
                strMutation = "PolynomialMutation";
                mutationProbability = 0.1;
                strRepairer = "StandardizationRepairer";
                populationSize = 100;
                numEvaluations = 25000;
                strCutOffCriteria = "MinConfDist";
                cutOffValue = 0.5;
                strFitnessFormulas = "Quality;Topology";
                strAlgorithm = "NSGAII";
                numOfThreads = Runtime.getRuntime().availableProcessors();
                printEvolution = false;
            }
        } else {
            throw new RuntimeException("At least the folder with the input trust lists must be provided.");
        }

        /** Refine the name of the algorithm to be executed according to the specified number of threads */
        if (numOfThreads < 0) {
            throw new RuntimeException("The number of threads must be a positive number.");

        } else if (numOfThreads > Runtime.getRuntime().availableProcessors()) {
            throw new RuntimeException("The specified number of threads is greater than that available on your device.");

        } else if (numOfThreads == 1) {
            strAlgorithm += "-SingleThread";

        } else if (numOfThreads > 1) {
            if (strAlgorithm.equals("GA") || strAlgorithm.equals("NSGAII")) {
                strAlgorithm += "-AsyncParallel";

            } else if (strAlgorithm.equals("MOEAD")) {
                System.out.println("The MOEAD algorithm is not implemented for parallel execution, so only one thread will be used during execution.");
                numOfThreads = 1;
                strAlgorithm += "-SingleThread";

            } else {
                strAlgorithm += "-SyncParallel";
            }
        }

        /** Establish the chromosome repairer. */
        repairer = StaticUtils.getRepairerFromString(strRepairer);

        /** List CSV files stored in the input folder with inferred lists of links. */
        File[] files = StaticUtils.getCSVFilesFromDirectory(networkFolder + "/lists/");

        /** Extracting gene names. */
        ArrayList<String> geneNames = StaticUtils.getGeneNames(networkFolder + "/gene_names.txt");

        /** Extract the path to the file with the time series if provided */
        String strTimeSeriesFile = networkFolder + "/time_series.csv";
        if (! Files.exists(Paths.get(strTimeSeriesFile))) {
            strTimeSeriesFile = null;
        }

        /** Establish the cut-off criteria. */
        cutOffCriteria = StaticUtils.getCutOffCriteriaFromString(strCutOffCriteria, cutOffValue, false);

        /** Initialize our problem with the extracted data. */
        if (printEvolution) {
            problem = new GRNProblemFitnessEvolution(files, geneNames, repairer, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
        } else {
            problem = new GRNProblem(files, geneNames, repairer, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
        }
        

        /** Set the crossover operator. */
        double crossoverDistributionIndex = 20.0;
        int numPointsCrossover = 2;
        crossover = StaticUtils.getCrossoverOperatorFromString(strCrossover, crossoverProbability, crossoverDistributionIndex, numPointsCrossover);

        /** Set the mutation operator. */
        double mutationDistributionIndex = 20.0;
        double delta = 0.5;
        int numberOfGroups = 4;
        CollectionGrouping<List<Double>> grouping = new ListLinearGrouping<>(numberOfGroups);
        double perturbation = 0.5;
        int maxMutIterations = 10;
        mutation = StaticUtils.getMutationOperatorFromString(strMutation, mutationProbability, repairer, mutationDistributionIndex, delta, numberOfGroups, grouping, perturbation, maxMutIterations);

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
        if (problem.getNumberOfObjectives() == 1) {
            if (strAlgorithm.equals("GA-AsyncParallel")) {
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
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());
    
            } else if (strAlgorithm.equals("GA-SyncParallel")) {
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
    
            } else if (strAlgorithm.equals("GA-SingleThread")) {
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
    
            } 
            else {
                throw new RuntimeException("The algorithm " + strAlgorithm + " is not available for single-objetive problems.");
            }
        } else {
            if (strAlgorithm.equals("NSGAII-SingleThread")) {
                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm
                    = new NSGAIIBuilder<>(problem, crossover, mutation, populationSize)
                        .setSelectionOperator(selection)
                        .setMaxEvaluations(numEvaluations)
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();
    
                /** Extract the population of the last iteration. */
                population = algorithm.getResult();

                
            } else if (strAlgorithm.equals("NSGAII-AsyncParallel")) {
                /** Activate stopwatch. */
                long initTime = System.currentTimeMillis();
    
                /** Instantiate the evolutionary algorithm. */
                AsynchronousMultiThreadedNSGAII<DoubleSolution> algorithm
                    = new AsynchronousMultiThreadedNSGAII<DoubleSolution>(
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
                Algorithm<List<DoubleSolution>> algorithm
                    = new SMPSOCorrectMutationBuilder(problem, archive)
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
                population = algorithm.getResult();

            } else if (strAlgorithm.equals("SMPSO-SyncParallel")) {
                /** Create archive */
                BoundedArchive<DoubleSolution> archive = new CrowdingDistanceArchive<>(populationSize);

                /** Instantiate the evaluator */
                SolutionListEvaluator<DoubleSolution> evaluator = new MultiThreadedSolutionListEvaluator<DoubleSolution>(numOfThreads);

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm 
                    = new SMPSOCorrectMutationBuilder(problem, archive)
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
                population = algorithm.getResult();

                /** Stop the evaluator */
                evaluator.shutdown();

            } else if (strAlgorithm.equals("MOEAD-SingleThread")) {
                if (!strCrossover.equals("DifferentialEvolutionCrossover")) {
                    throw new RuntimeException("The MOEAD algorithm can only be executed by selecting the differential evolution crossover");
                }

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm
                    = new MOEADBuilder(problem, MOEADBuilder.Variant.MOEAD)
                        .setCrossover(crossover)
                        .setMutation(mutation)
                        .setMaxEvaluations(numEvaluations)
                        .setPopulationSize(populationSize)
                        .setResultPopulationSize(populationSize)
                        .setNeighborhoodSelectionProbability(0.9)
                        .setMaximumNumberOfReplacedSolutions(2)
                        .setNeighborSize(20)
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();
    
                /** Extract the population of the last iteration. */
                population = SolutionListUtils.getNonDominatedSolutions(algorithm.getResult());

            } else if (strAlgorithm.equals("GDE3-SingleThread")) {
                if (!strCrossover.equals("DifferentialEvolutionCrossover")) {
                    throw new RuntimeException("The GDE3 algorithm can only be executed by selecting the differential evolution crossover");
                }

                /** Instantiate the empty mutation operator to repair solutions. */
                mutation = new NullMutationWithRepair(repairer);
                System.out.println("The GDE3 algorithm has its own mutation operator, so the one indicated in the input will be ignored in this case.");

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm
                    = new GDE3BuilderWithRepair(problem)
                        .setCrossover((DifferentialEvolutionCrossover)crossover)
                        .setMutation(mutation)
                        .setMaxEvaluations(numEvaluations)
                        .setPopulationSize(populationSize)
                        .setSolutionSetEvaluator(new SequentialSolutionListEvaluator<>())
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();
    
                /** Extract the population of the last iteration. */
                population = algorithm.getResult();

            } else if (strAlgorithm.equals("GDE3-SyncParallel")) {
                if (!strCrossover.equals("DifferentialEvolutionCrossover")) {
                    throw new RuntimeException("The GDE3 algorithm can only be executed by selecting the differential evolution crossover");
                }

                /** Instantiate the empty mutation operator to repair solutions. */
                mutation = new NullMutationWithRepair(repairer);
                System.out.println("The GDE3 algorithm has its own mutation operator, so the one indicated in the input will be ignored in this case.");

                /** Instantiate the evaluator */
                SolutionListEvaluator<DoubleSolution> evaluator = new MultiThreadedSolutionListEvaluator<DoubleSolution>(numOfThreads);

                /** Instantiate the evolutionary algorithm. */
                Algorithm<List<DoubleSolution>> algorithm
                    = new GDE3BuilderWithRepair(problem)
                        .setCrossover((DifferentialEvolutionCrossover)crossover)
                        .setMutation(mutation)
                        .setMaxEvaluations(numEvaluations)
                        .setPopulationSize(populationSize)
                        .setSolutionSetEvaluator(evaluator)
                        .build();

                /** Execute the designed evolutionary algorithm. */
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm).execute();

                /** Extract the total execution time. */
                computingTime = algorithmRunner.getComputingTime();
    
                /** Extract the population of the last iteration. */
                population = algorithm.getResult();

                /** Stop the evaluator */
                evaluator.shutdown();

            } else {
                throw new RuntimeException("The algorithm " + strAlgorithm + " is not available for multi-objetive problems.");
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

        /** Write the data of the last population (pareto front approximation). */
        new SolutionListOutput(population)
            .setVarFileOutputContext(new DefaultFileOutputContext(outputFolder + "/VAR.csv", ","))
            .setFunFileOutputContext(new DefaultFileOutputContext(outputFolder + "/FUN.csv", ","))
            .print();

        
        if (problem.getNumberOfObjectives() == 1) {
            /** Transform the solution into a simple vector of weights. */
            double[] winner = new double[problem.getNumberOfVariables()];
            for (int i = 0; i < problem.getNumberOfVariables(); i++) {
                winner[i] = population.get(0).variables().get(i);
            }

            /** Write the list of weights assigned to each technique in an output txt file. */
            String[] tags = new String[files.length];
            for (int i = 0; i < files.length; i++) {
                String filename = files[i].getName();
                tags[i] = filename.substring(4, filename.lastIndexOf('.'));
            }
            StaticUtils.writeWeights(outputFolder + "/final_weights.txt", winner, tags);

            /** Calculate the consensus list corresponding to the solution vector. */
            Map<String, ConsensusTuple> consensus = problem.makeConsensus(winner)
                .entrySet()
                .stream()
                .sorted(Map.Entry.<String, ConsensusTuple>comparingByValue())
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue,
                    (e1, e2) -> e1, LinkedHashMap::new));

            /** Write the resulting list of links to an output csv file. */
            StaticUtils.writeConsensusList(outputFolder + "/final_list.csv", consensus);

            /** Calculate the binary matrix from the list above. */
            int[][] binaryNetwork = cutOffCriteria.getNetworkFromConsensus(consensus, geneNames);

            /** Write the resulting binary matrix to an output csv file. */
            StaticUtils.writeBinaryNetwork(outputFolder + "/final_network.csv", binaryNetwork, geneNames);
        }

        /** Report the execution time and return the best solution found by the algorithm. */
        System.out.println("Evolutionary algorithm executed: " + strAlgorithm);
        System.out.println("Threads used: " + numOfThreads);
        System.out.println("Total execution time: " + computingTime + "ms");

        if (printEvolution) {
            System.out.println("The evolution of fitness values has been stored in " + outputFolder + "/fitness_evolution.txt");
        }

        if (problem.getNumberOfObjectives() == 1) {
            System.out.println("The resulting list of links has been stored in " + outputFolder + "/final_list.csv");
            System.out.println("The resulting binary matrix has been stored in " + outputFolder + "/final_network.csv");
            System.out.println("List of the weights assigned to each technique has been stored in " + outputFolder + "/final_weights.txt");
        }

        System.exit(0);
    }
}


