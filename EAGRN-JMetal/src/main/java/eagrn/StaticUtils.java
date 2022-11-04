package eagrn;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileFilter;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.io.FileWriter;

import eagrn.fitnessfunctions.impl.clusteringmeasure.impl.AverageLocalClusteringMeasure;
import eagrn.fitnessfunctions.impl.clusteringmeasure.impl.GlobalClusteringMeasure;
import eagrn.fitnessfunctions.impl.consistencywithtimeseries.impl.ConsistencyWithTimeSeriesFinal;
import eagrn.fitnessfunctions.impl.consistencywithtimeseries.impl.ConsistencyWithTimeSeriesProgressiveCurrentImpact;
import eagrn.fitnessfunctions.impl.consistencywithtimeseries.impl.ConsistencyWithTimeSeriesProgressiveNextImpact;
import eagrn.fitnessfunctions.impl.consistencywithtimeseries.impl.ConsistencyWithTimeSeriesProgressiveNextNextImpact;
import eagrn.fitnessfunctions.impl.degreedistribution.impl.BinarizedDegreeDistribution;
import eagrn.fitnessfunctions.impl.degreedistribution.impl.WeightedDegreeDistribution;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMean;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMeanAboveAverage;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMeanAboveAverageWithContrast;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMeanAboveCutOff;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMedian;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMedianAboveAverage;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMedianAboveAverageWithContrast;
import eagrn.fitnessfunctions.impl.quality.impl.QualityMedianAboveCutOff;

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
import eagrn.cutoffcriteria.impl.NumLinksWithBestConfCriteria;
import eagrn.cutoffcriteria.impl.PercLinksWithBestConfCriteria;
import eagrn.fitnessfunctions.FitnessFunction;
import eagrn.cutoffcriteria.impl.MinConfCriteria;
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

    public static CutOffCriteria getCutOffCriteriaFromString(String strCutOffCriteria, double cutOffValue, ArrayList<String> geneNames) {
        /**
         * This function takes as input a character string representing a 
         * cut-off criteria and returns the object corresponding to it
         */
        CutOffCriteria cutOffCriteria;

        switch (strCutOffCriteria) {
            case "MinConf":
                cutOffCriteria = new MinConfCriteria(cutOffValue, geneNames);
                break;
            case "NumLinksWithBestConf":
                cutOffCriteria = new NumLinksWithBestConfCriteria((int) cutOffValue, geneNames);
                break;
            case "PercLinksWithBestConf":
                cutOffCriteria = new PercLinksWithBestConfCriteria(cutOffValue, geneNames);
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

    public static void writeConsensus(String strFile, Map<String, Double> consensus) {
        /**
         * This function is responsible for writing the consensus list of 
         * a solution to an output csv file specified as a parameter.
         */
        try {
            File outputFile = new File(strFile);
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            for (Map.Entry<String, Double> pair : consensus.entrySet()) {
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

    public static Map<String, Double> makeConsensus(Double[] weights, Map<String, Double[]> inferredNetworks) {
        /**
         * This function calculates the weighted sum of 
         * confidence levels based on the weights.
         */

        Map<String, Double> consensus = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : inferredNetworks.entrySet()) {
            double confidence = 0.0;

            for (int i = 0; i < weights.length; i++) {
                confidence += weights[i] * pair.getValue()[i];
            }

            consensus.put(pair.getKey(), confidence);
        }

        return consensus;
    }

    public static Map<String, Double[]> readAllInferredNetworkFiles(File[] inferredNetworkFiles) {
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

    public static Map<String, Double[]> readTimeSeries(String strTimeSeriesFile) {
        /**
         * It reads the file with the input time series
         */

        Map<String, Double[]> res = new HashMap<String, Double[]>();

        try {
            File timesSeriesFile = new File(strTimeSeriesFile);
            Scanner sc = new Scanner(timesSeriesFile);
            sc.nextLine();
            while(sc.hasNextLine()) {
                String line = sc.nextLine();
                String[] splitLine = line.split(",");

                String gene = splitLine[0].replace("\"", "");
                Double[] array = new Double[splitLine.length - 1];
                for (int i = 1; i < splitLine.length; i++) {
                    array[i-1] = Double.parseDouble(splitLine[i]);
                }
                res.put(gene, array);
            }
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        return res;
    }

    public static FitnessFunction getBasicFitnessFunction(String str, ArrayList<String> geneNames, Map<String, Double[]> inferredNetworks, CutOffCriteria cutOffCriteria, Map<String, Double[]> timeSeriesMap) {
        /** 
         * Function to return a basic FitnessFunction object based on a identifier string 
         */
        
        FitnessFunction res;
        switch (str.toLowerCase()) {
            case "binarizeddegreedistribution":
                res = new BinarizedDegreeDistribution(geneNames.size(), cutOffCriteria);
                break;
            case "weighteddegreedistribution":
                res = new WeightedDegreeDistribution(geneNames);
                break;
            case "averagelocalclusteringmeasure":
                res = new AverageLocalClusteringMeasure(geneNames, cutOffCriteria);
                break;
            case "globalclusteringmeasure":
                res = new GlobalClusteringMeasure(geneNames, cutOffCriteria);
                break;
            case "qualitymean":
                res = new QualityMean(inferredNetworks);
                break;
            case "qualitymedian":
                res = new QualityMedian(inferredNetworks);
                break;
            case "qualitymeanaboveaverage":
                res = new QualityMeanAboveAverage(inferredNetworks);
                break;
            case "qualitymedianaboveaverage":
                res = new QualityMedianAboveAverage(inferredNetworks);
                break;
            case "qualitymeanabovecutoff":
                res = new QualityMeanAboveCutOff(inferredNetworks, cutOffCriteria);
                break;
            case "qualitymedianabovecutoff":
                res = new QualityMedianAboveCutOff(inferredNetworks, cutOffCriteria);
                break;
            case "qualitymeanaboveaveragewithcontrast":
                res = new QualityMeanAboveAverageWithContrast(geneNames.size(), inferredNetworks);
                break;
            case "qualitymedianaboveaveragewithcontrast":
                res = new QualityMedianAboveAverageWithContrast(geneNames.size(), inferredNetworks);
                break;
            case "consistencywithtimeseriesprogressivecurrentimpact":
                res = new ConsistencyWithTimeSeriesProgressiveCurrentImpact(timeSeriesMap);
                break;
            case "consistencywithtimeseriesprogressivenextimpact":
                res = new ConsistencyWithTimeSeriesProgressiveNextImpact(timeSeriesMap);
                break;
            case "consistencywithtimeseriesprogressivenextnextimpact":
                res = new ConsistencyWithTimeSeriesProgressiveNextNextImpact(timeSeriesMap);
                break;
            case "consistencywithtimeseriesfinal":
                res = new ConsistencyWithTimeSeriesFinal(timeSeriesMap);
                break;
            default:
                throw new RuntimeException("The evaluation term " + str + " is not implemented.");
        }
        return res;
    }

    public static FitnessFunction getCompositeFitnessFunction(String formula, ArrayList<String> geneNames, Map<String, Double[]> inferredNetworks, CutOffCriteria cutOffCriteria, Map<String, Double[]> timeSeriesMap) {
        /**
         * Function to return a composite FitnessFunction object based on a formula string
         */
        
        FitnessFunction function;

        String[] subformulas = formula.split("\\+");
        if (subformulas.length == 1 && subformulas[0].split("\\*").length == 1) {
            function = getBasicFitnessFunction(formula, geneNames, inferredNetworks, cutOffCriteria, timeSeriesMap);
        } else {
            FitnessFunction[] functions = new FitnessFunction[subformulas.length];
            Double[] weights = new Double[subformulas.length];
            double totalWeight = 0;

            for (int j = 0; j < subformulas.length; j++) {
                String[] tuple = subformulas[j].split("\\*");
                if (tuple.length != 2) {
                    throw new RuntimeException("Function specified with improper formatting. Remember to separate the name of the terms by the symbol +, and assign their weight by preceding them with a decimal followed by the symbol *.");
                }

                functions[j] = getBasicFitnessFunction(tuple[1], geneNames, inferredNetworks, cutOffCriteria, timeSeriesMap);
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

        return function;
    }
}
