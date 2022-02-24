import operator.repairer.WeightRepairer;
import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class GRNProblem extends AbstractDoubleProblem {
    private Map<String, Double>[] inferredNetworks;
    private ArrayList<String> geneNames;
    private int numberOfNodes;
    private WeightRepairer initialPopulationRepairer;

    /** Constructor Creates a default instance of the GRN problem */
    public GRNProblem(File[] inferredNetworkFiles, String[] geneNames, WeightRepairer initialPopulationRepairer) {
        this.inferredNetworks = readAll(inferredNetworkFiles);
        this.geneNames = new ArrayList<String>(List.of(geneNames));
        this.numberOfNodes = geneNames.length;
        this.initialPopulationRepairer = initialPopulationRepairer;
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
        double f1 = fitnessF1(consensus);

        /**
        int k = (int) Math.round(0.2 * numberOfNodes);
        int [][] binaryNetwork = getNetworkFromListWithK(consensus, k);
         */

        double percMaxConf = 0.5;
        int [][] binaryNetwork = getNetworkFromListWithConf(consensus, percMaxConf);
        double f2 = fitnessF2(binaryNetwork);

        solution.objectives()[0] = 0.5*f1 + 0.5*f2;
        return solution;
    }

    /** ReadAll() method */
    private Map<String, Double>[] readAll(File[] inferredNetworkFiles) {
        Map<String, Double>[] vmap = new HashMap[inferredNetworkFiles.length];

        for (int i = 0; i < inferredNetworkFiles.length; i++) {
            Map<String, Double> map = new HashMap<String, Double>();

            try {
                Scanner sc = new Scanner(inferredNetworkFiles[i]);
                while(sc.hasNextLine()){
                    String line = sc.nextLine();
                    String[] splitLine = line.split(",");

                    String key;
                    if(splitLine[0].compareTo(splitLine[1]) < 0) {
                        key = splitLine[0] + "-" + splitLine[1];
                    } else {
                        key = splitLine[1] + "-" + splitLine[0];
                    }

                    Double value = Double.parseDouble(splitLine[2]);
                    map.put(key, value);
                }
            } catch (FileNotFoundException fnfe) {
                throw new RuntimeException(fnfe.getMessage());
            }

            vmap[i] = map;
        }

        return vmap;
    }

    /** MakeConsensus() method */
    public Map<String, ConsensusTuple> makeConsensus(double[] x) {
        Map<String, ConsensusTuple> consensus = new HashMap<>();

        for (int i = 0; i < x.length; i++) {
            if (x[i] > 0) {
                for (Map.Entry<String, Double> pair : inferredNetworks[i].entrySet()) {
                    ConsensusTuple mapConsTuple = consensus.getOrDefault(pair.getKey(), new ConsensusTuple(0, 0.0));
                    if (x[i] > 0.05) mapConsTuple.increaseFreq();
                    mapConsTuple.increaseConf(x[i] * pair.getValue());
                    consensus.put(pair.getKey(), mapConsTuple);
                }
            }
        }

        return consensus;
    }

    /** GetNetworkFromListWithK() method */
    public int[][] getNetworkFromListWithK (Map<String, ConsensusTuple> consensus, int k) {
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, ConsensusTuple>> list = new ArrayList<>(consensus.entrySet());
        list.sort(Map.Entry.comparingByValue());

        Iterator<Map.Entry<String, ConsensusTuple>> iterator = list.iterator();
        int row, col, cnt = 0;
        String key;
        while (cnt < k) {
            key = iterator.next().getKey();
            String [] vKeySplit = key.split("-");
            row = geneNames.indexOf(vKeySplit[0]);
            col = geneNames.indexOf(vKeySplit[1]);
            network[row][col] = 1;
            network[col][row] = 1;
            cnt += 1;
        }

        return network;
    }

    /** GetNetworkFromListWithConf() method */
    public int[][] getNetworkFromListWithConf (Map<String, ConsensusTuple> consensus, double percMaxConf) {
        int[][] network = new int[numberOfNodes][numberOfNodes];

        double conf, max = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            if (conf > max) max = conf;
        }

        double cutOff = max * percMaxConf;
        int row, col;
        String key;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            if (pair.getValue().getConf() > cutOff) {
                key = pair.getKey();
                String [] vKeySplit = key.split("-");
                row = geneNames.indexOf(vKeySplit[0]);
                col = geneNames.indexOf(vKeySplit[1]);
                network[row][col] = 1;
                network[col][row] = 1;
            }
        }

        return network;
    }

    /** FitnessF1() method */
    public double fitnessF1(Map<String, ConsensusTuple> consensus) {

        double conf, confSum = 0;
        double freq, freqSum = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            confSum += conf;
            freq = pair.getValue().getFreq();
            freqSum += freq;
        }

        double numberOfLinks = (double) (numberOfNodes * (numberOfNodes - 1))/2;
        double f1 = 1.0 - (double) consensus.size() / numberOfLinks;
        double f2 = 1.0 - freqSum/(numberOfLinks * getNumberOfVariables());
        double f3 = 1.0 - confSum/numberOfLinks;
        double fitness = (f1 + f2 + f3)/3;

        return fitness;
    }

    /** FitnessF2() method */
    public double fitnessF2(int[][] network) {
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
        for (int i = 0; i < numberOfNodes; i++) {
            if (degrees[i] > mean) hubs += 1;
        }

        double fitness = (double) hubs/numberOfNodes;
        return fitness;
    }

}
