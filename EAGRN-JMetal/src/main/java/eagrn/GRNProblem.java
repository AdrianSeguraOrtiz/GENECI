package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.operator.repairer.WeightRepairer;
import java.io.File;
import java.util.*;

import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;


public class GRNProblem extends AbstractDoubleProblem {
    private Map<String, Double[]> inferredNetworks;
    private Map<String, MedianTuple> medianInterval;
    private ArrayList<String> geneNames;
    private int numberOfNodes;
    private WeightRepairer initialPopulationRepairer;
    private CutOffCriteria cutOffCriteria;
    private double qualityWeight;
    private double topologyWeight;
    private int cntEvaluations;
    private double bestFitness;
    private ArrayList<Double> fitnessList;
    private double bestQuality;
    private ArrayList<Double> qualityList;
    private double bestTopology;
    private ArrayList<Double> topologyList;
    private int populationSize;

    /** Constructor Creates a default instance of the GRN problem */
    public GRNProblem(File[] inferredNetworkFiles, ArrayList<String> geneNames, WeightRepairer initialPopulationRepairer, CutOffCriteria cutOffCriteria, double qualityWeight, double topologyWeight) {
        /** if the weights do not add up to 1 an error is thrown */
        if (qualityWeight + topologyWeight != 1.0) {
            throw new RuntimeException("The weights of both functions must add up to 1");
        }
        
        this.inferredNetworks = readAll(inferredNetworkFiles);
        this.medianInterval = calculateMedian(inferredNetworks);
        this.geneNames = geneNames;
        this.numberOfNodes = geneNames.size();
        this.initialPopulationRepairer = initialPopulationRepairer;
        this.cutOffCriteria = cutOffCriteria;
        this.qualityWeight = qualityWeight;
        this.topologyWeight = topologyWeight;
        this.cntEvaluations = 0;
        this.bestFitness = 1;
        this.fitnessList = new ArrayList<>();
        this.bestQuality = 1;
        this.qualityList = new ArrayList<>();
        this.bestTopology = 1;
        this.topologyList = new ArrayList<>();
        this.populationSize = 0;

        setNumberOfVariables(inferredNetworkFiles.length);
        setNumberOfObjectives(1);
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
        this.populationSize += 1;
        return solution;
    }

    /** Evaluate() method */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {
        double[] x = new double[getNumberOfVariables()];
        for (int i = 0; i < getNumberOfVariables(); i++) {
            x[i] = solution.variables().get(i);
        }

        Map<String, ConsensusTuple> consensus = makeConsensus(x);
        double q = quality(consensus);

        int [][] binaryNetwork = cutOffCriteria.getNetworkFromConsensus(consensus, geneNames);
        double t = topology(binaryNetwork);

        double fitness = this.qualityWeight*q + this.topologyWeight*t;
        solution.objectives()[0] = fitness;

        this.cntEvaluations += 1;
        if (fitness < this.bestFitness) {
            this.bestFitness = fitness;
            this.bestQuality = q;
            this.bestTopology = t;
        }
        if (this.cntEvaluations % this.populationSize == 0){
            this.fitnessList.add(this.bestFitness);
            this.qualityList.add(this.bestQuality);
            this.topologyList.add(this.bestTopology);
        }

        return solution;
    }

    /** ReadAll() method */
    private Map<String, Double[]> readAll(File[] inferredNetworkFiles) {
        /**
         * It scans the lists of links offered by the different techniques and stores them in a map 
         * with vector values for later query during the construction of the consensus network.
         */

        Map<String, Double[]> res = new HashMap<String, Double[]>();
        Double[] initialValue = new Double[inferredNetworkFiles.length];
        Arrays.fill(initialValue, 0.0);

        for (int i = 0; i < inferredNetworkFiles.length; i++) {
            Map<String, Double> map = new ListOfLinks(inferredNetworkFiles[i]).getMapWithLinks();

            for (Map.Entry<String, Double> entry : map.entrySet()) {
                Double[] value = res.getOrDefault(entry.getKey(), initialValue.clone());
                value[i] = entry.getValue();
                res.put(entry.getKey(), value);
            }
        }

        return res;
    }

    /** CalculateMedian() method */
    private Map<String, MedianTuple> calculateMedian(Map<String, Double[]> inferredNetworks) {
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

    /** MakeConsensus() method */
    public Map<String, ConsensusTuple> makeConsensus(double[] x) {
        /**
         * Elaborate the list of consensus links from the vector of weights
         * and the results provided by each technique.
         */

        Map<String, ConsensusTuple> consensus = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : inferredNetworks.entrySet()) {
            ConsensusTuple mapConsTuple = new ConsensusTuple(0.0, 0.0);
            MedianTuple medInt = medianInterval.get(pair.getKey());
            Double[] weightDistances = new Double[x.length];

            for (int i = 0; i < x.length; i++) {
                mapConsTuple.increaseConf(x[i] * pair.getValue()[i]);
                weightDistances[i] = ((Math.abs(medInt.getMedian() - pair.getValue()[i]) / medInt.getInterval()) + x[i]) / 2.0;
            }

            double min = Collections.min(Arrays.asList(weightDistances));
            double max = Collections.max(Arrays.asList(weightDistances));

            mapConsTuple.setDist(max - min);
            consensus.put(pair.getKey(), mapConsTuple);
        }

        return consensus;
    }

    /** Quality() method */
    public double quality(Map<String, ConsensusTuple> consensus) {
        /**
         * Try to minimize the quantity of high quality links (getting as close as possible
         * to 10 percent of the total possible links in the network) and at the same time maximize
         * the quality of these good links (maximize the mean of their confidence and weight adjustment).
         *
         * High quality links are those whose confidence-distance mean is above average.
         */

        /** 1. Calculate the mean of the confidence-distance means. */
        double conf, dist, confDistSum = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            dist = pair.getValue().getDist();
            confDistSum += (conf + (1 - dist)) / 2.0;
        }
        double mean = confDistSum / consensus.size();

        /** 2. Quantify the number of high quality links and calculate the average of their confidence-distance means */
        confDistSum = 0;
        double confDist, cnt = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            dist = pair.getValue().getDist();
            confDist = (conf + (1 - dist)) / 2.0;
            if (confDist > mean) {
                confDistSum += confDist;
                cnt += 1;
            }
        }

        /** 3. Calculate first term value */
        double numberOfLinks = (double) (numberOfNodes * numberOfNodes);
        double f1 = Math.abs(cnt - 0.1 * numberOfLinks)/((1 - 0.1) * numberOfLinks);
        double f2 = 1.0 - confDistSum/cnt;
        double fitness = 0.25*f1 + 0.75*f2;

        return fitness;
    }

    /** Topology() method */
    public double topology(int[][] network) {
        /**
         * The aim is to minimize the number of nodes whose degree is higher than the 
         * average while trying to maximize the degree of these nodes.
         */

        int[] degrees = new int[numberOfNodes];

        for (int i = 0; i < numberOfNodes; i++) {
            for (int j = 0; j < numberOfNodes; j++) {
                degrees[i] += network[i][j];
            }
        }

        int sum = 0;
        for (int i = 0; i < numberOfNodes; i++) {
            sum += degrees[i];
        }
        double mean = (double) sum/numberOfNodes;

        int hubs = 0;
        int hubsDegreesSum = 0;
        for (int i = 0; i < numberOfNodes; i++) {
            if (degrees[i] > mean) {
                hubs += 1;
                hubsDegreesSum += degrees[i];
            } 
        }

        double f1 = Math.abs(hubs - 0.1 * numberOfNodes)/((1 - 0.1) * numberOfNodes);
        double f2 = 1.0;
        if (hubs > 0) f2 = 1.0 - (double) (hubsDegreesSum/hubs)/(numberOfNodes - 1);
        double fitness = (f1 + f2)/2;

        return fitness;
    }

    public Map<String, Double[]> getFitnessEvolution() {
        Map<String, Double[]> fitnessEvolution = new HashMap<String, Double[]>();
        fitnessEvolution.put("Fitness", this.fitnessList.toArray(new Double[this.fitnessList.size()]));
        fitnessEvolution.put("F1", this.qualityList.toArray(new Double[this.qualityList.size()]));
        fitnessEvolution.put("F2", this.topologyList.toArray(new Double[this.topologyList.size()]));
        return fitnessEvolution;
    }

}
