package eagrn;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileFilter;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.io.FileWriter;

import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.operator.crossover.impl.BLXAlphaCrossover;
import org.uma.jmetal.operator.crossover.impl.DifferentialEvolutionCrossover;
import org.uma.jmetal.operator.crossover.impl.NPointCrossover;
import org.uma.jmetal.operator.crossover.impl.NullCrossover;
import org.uma.jmetal.operator.crossover.impl.SBXCrossover;
import org.uma.jmetal.operator.crossover.impl.WholeArithmeticCrossover;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.grouping.CollectionGrouping;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.cutoffcriteria.impl.MaxNumLinksBestConfCriteria;
import eagrn.cutoffcriteria.impl.MinConfDistCriteria;
import eagrn.cutoffcriteria.impl.MinConfidenceCriteria;
import eagrn.operator.mutationwithrepair.impl.CDGMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.GroupedAndLinkedPolynomialMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.GroupedPolynomialMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.LinkedPolynomialMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.NonUniformMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.NullMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.PolynomialMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.SimpleRandomMutationWithRepair;
import eagrn.operator.mutationwithrepair.impl.UniformMutationWithRepair;
import eagrn.operator.repairer.WeightRepairer;
import eagrn.operator.repairer.impl.GreedyRepairer;
import eagrn.operator.repairer.impl.StandardizationRepairer;

public final class StaticUtils {
    public static Map<String, Double> getMapWithLinks(File listFile) {
        /**
         * This function takes as input the file with the list of links and 
         * their respective confidence levels, and returns a map containing 
         * all information
         */
        Map<String, Double> map = new HashMap<String, Double>();

        try {
            Scanner sc = new Scanner(listFile);
            while(sc.hasNextLine()) {
                String line = sc.nextLine();
                String[] splitLine = line.split(",");

                String key = splitLine[0] + ";" + splitLine[1];
                Double value = Double.parseDouble(splitLine[2]);
                map.put(key, value);
            }
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        return map;
    }

    public static WeightRepairer getRepairerFromString(String strRepairer) {
        /**
         * This function takes as input a character string representing a 
         * repairer and returns the object corresponding to it
         */
        WeightRepairer repairer;

        switch (strRepairer) {
            case "StandardizationRepairer":
                repairer = new StandardizationRepairer();
                break;
            case "GreedyRepair":
                repairer = new GreedyRepairer();
                break;
            default:
                throw new RuntimeException("The repairer operator entered is not available.");
        }

        return repairer;
    }

    public static File[] getCSVFilesFromDirectory(String directory) {
        /**
         * This function takes as input a directory and returns the 
         * list of CSV files contained in it
         */
        File dir = new File(directory);
        FileFilter fileFilter = new WildcardFileFilter("*.csv");
        return dir.listFiles(fileFilter);
    }

    public static ArrayList<String> getGeneNames(String strFile) {
        /**
         * This function receives the path to the file containing the 
         * list of gene names and returns a vector with all of them.
         */
        ArrayList<String> geneNames;

        File geneNamesFile = new File(strFile);
        try {
            Scanner sc = new Scanner(geneNamesFile);
            String line = sc.nextLine();
            String[] lineSplit = line.split(",");
            geneNames = new ArrayList<>(List.of(lineSplit));
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        return geneNames;
    }

    public static CutOffCriteria getCutOffCriteriaFromString(String strCutOffCriteria, double cutOffValue, boolean onlyConf) {
        /**
         * This function takes as input a character string representing a 
         * cut-off criteria and returns the object corresponding to it
         */
        CutOffCriteria cutOffCriteria;

        switch (strCutOffCriteria) {
            case "MinConfidence":
                cutOffCriteria = new MinConfidenceCriteria(cutOffValue);
                break;
            case "MaxNumLinksBestConf":
                cutOffCriteria = new MaxNumLinksBestConfCriteria((int) cutOffValue);
                break;
            case "MinConfDist":
                if (onlyConf) {
                    throw new RuntimeException("The cut-off criterion MinConfDist can only be used during the consensus process.");
                }
                cutOffCriteria = new MinConfDistCriteria(cutOffValue);
                break;
            default:
                throw new RuntimeException("The cut-off criteria entered is not available");
        }

        return cutOffCriteria;
    }

    public static CrossoverOperator<DoubleSolution> getCrossoverOperatorFromString(String strCrossover, double crossoverProbability, double crossoverDistributionIndex, int numPointsCrossover) {
        /**
         * This function takes as input a character string representing a 
         * crossover operator and returns the object corresponding to it
         */
        CrossoverOperator<DoubleSolution> crossover;
        
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
                crossover = new NullCrossover<DoubleSolution>();
                break;
            case "WholeArithmeticCrossover":
                crossover = new WholeArithmeticCrossover(crossoverProbability);
                break;
            default:
                throw new RuntimeException("The crossover operator entered is not available");
        }

        return crossover;
    }

    public static MutationOperator<DoubleSolution> getMutationOperatorFromString(String strMutation, double mutationProbability, WeightRepairer repairer, double mutationDistributionIndex, double delta, int numberOfGroups, CollectionGrouping<List<Double>> grouping, double perturbation, int maxMutIterations) {
        /**
         * This function takes as input a character string representing a 
         * mutation operator and returns the object corresponding to it
         */
        MutationOperator<DoubleSolution> mutation;

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

        return mutation;
    }

    public static void writeFitnessEvolution(String strFile, Map<String, Double[]> fitnessEvolution) {
        /**
         * This function is responsible for writing the evolution of the 
         * fitness values in an output txt file specified as parameter
         */
        try {
            File outputFile = new File(strFile);
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (Map.Entry<String, Double[]> entry : fitnessEvolution.entrySet()) {
                String strVector = Arrays.toString(entry.getValue());
                bw.write(strVector.substring(1, strVector.length() - 1) + "\n");
            }

            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe);
        }
    }

    public static void writeWeights(String strFile, double[] weights, String[] tags) {
        /**
         * This function is responsible for writing the weights of a 
         * solution to an output txt file specified as parameter
         */
        try {
            File outputFile = new File(strFile);
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (int i = 0; i < weights.length; i++) {
                bw.write(tags[i] + ": " + weights[i]);
                bw.newLine();
            }

            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }
    }

    public static void writeWeightedConfList(String strFile, Map<String, Double> weightedConf) {
        /**
         * This function is responsible for writing the consensus list of 
         * a solution to an output csv file specified as a parameter.
         */
        try {
            File outputFile = new File(strFile);
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (Map.Entry<String, Double> pair : weightedConf.entrySet()) {
                String [] vKeySplit = pair.getKey().split(";");
                bw.write(vKeySplit[0] + "," + vKeySplit[1] + "," + pair.getValue());
                bw.newLine();
            }
            bw.flush();
            bw.close();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }
    }

    public static void writeBinaryNetwork(String strFile, int[][] binaryNetwork, ArrayList<String> geneNames) {
        /**
         * This function is responsible for writing the binary network 
         * of a solution to an output csv file specified as a parameter.
         */
        try {
            File outputFile = new File(strFile);
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
    }

    public static Map<String, Double> getWeightedConf(double[] weights, Map<String, Double[]> inferredNetworks) {
        /**
         * This function calculates the weighted sum of 
         * confidence levels based on the weights.
         */
        Map<String, Double> weightedConf = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : inferredNetworks.entrySet()) {
            double conf = 0;
            for (int i = 0; i < weights.length; i++) {
                conf += weights[i] * pair.getValue()[i];
            }
            weightedConf.put(pair.getKey(), conf);
        }

        return weightedConf;
    }

    public static Map<String, Double[]> readAll(File[] inferredNetworkFiles) {
        /**
         * It scans the lists of links offered by the different techniques and stores them in a map 
         * with vector values for later query during the construction of the consensus network.
         */

        Map<String, Double[]> res = new HashMap<String, Double[]>();
        Double[] initialValue = new Double[inferredNetworkFiles.length];
        Arrays.fill(initialValue, 0.0);

        for (int i = 0; i < inferredNetworkFiles.length; i++) {
            Map<String, Double> map = StaticUtils.getMapWithLinks(inferredNetworkFiles[i]);

            for (Map.Entry<String, Double> entry : map.entrySet()) {
                Double[] value = res.getOrDefault(entry.getKey(), initialValue.clone());
                value[i] = entry.getValue();
                res.put(entry.getKey(), value);
            }
        }

        return res;
    }

    public static Map<String, MedianTuple> calculateMedian(Map<String, Double[]> inferredNetworks) {
        /**
         * For each interaction, calculate the median and the distance to the farthest point 
         * of it for the confidence levels reported by each technique.
         */

        Map<String, MedianTuple> res = new HashMap<String, MedianTuple>();

        for (Map.Entry<String, Double[]> entry : inferredNetworks.entrySet()) {
            Double[] confidences = entry.getValue();
            Arrays.sort(confidences);

            int middle = confidences.length / 2;
            double median;
            if (confidences.length % 2 == 0) {
                median = (confidences[middle - 1] + confidences[middle]) / 2.0;
            } else {
                median = confidences[middle];
            }

            double min = Collections.min(Arrays.asList(confidences));
            double max = Collections.max(Arrays.asList(confidences));
            double interval = Math.max(median - min, max - median);

            MedianTuple value = new MedianTuple(median, interval);
            res.put(entry.getKey(), value);
        }
        return res;
    }
}
