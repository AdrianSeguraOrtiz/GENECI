import com.sun.xml.bind.v2.schemagen.xmlschema.Union;
import generic.Tuple;
import operator.repairer.WeightRepairer;
import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import smile.timeseries.AR;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class GRNProblem extends AbstractDoubleProblem {
    private Map<String, Double>[] inferredNetworks;
    private WeightRepairer initialPopulationRepairer;

    /** Constructor Creates a default instance of the GRN problem */
    public GRNProblem(File[] inferredNetworkFiles, WeightRepairer initialPopulationRepairer) {
        this.inferredNetworks = readAll(inferredNetworkFiles);
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
        solution.objectives()[0] = fitnessF1(consensus);
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
                    mapConsTuple.increaseFreq();
                    mapConsTuple.increaseConf(x[i] * pair.getValue());
                    consensus.put(pair.getKey(), mapConsTuple);
                }
            }
        }

        return consensus;
    }

    /** FitnessF1() method */
    public double fitnessF1(Map<String, ConsensusTuple> consensus) {
        double max = 0.0;
        double conf, freq;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            if (conf > max) max = conf;
        }
        double cutOff = (2/3) * max;

        double confSum = 0.0;
        double freqSum = 0.0;
        int cnt = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            freq = pair.getValue().getFreq();
            if (conf > cutOff) {
                confSum += conf;
                freqSum += freq;
                cnt += 1;
            }
        }

        double f1 = cnt / consensus.size();
        double f2 = 1 - (freqSum/cnt);
        double f3 = 1 - (confSum/cnt);
        double fitness = f1 + f2 + f3;

        return fitness;
    }

    /** FitnessF2() method */
    public double fitnessF2(double[] weights) {
        double min = Double.POSITIVE_INFINITY;
        for(double cur: weights)
            min = Math.min(min, cur);

        return min;
    }

}
