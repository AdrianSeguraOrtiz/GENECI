package eagrn.operator.repairer;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.stream.Collectors;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.ListOfLinks;

public abstract class WeightRepairer {
    protected Map<String, Double> knownInteractionsMap;
    protected DistanceFunction distanceFunction;
    protected Map<String, Double[]> inferredNetworks;

    public WeightRepairer(String strKnownInteractionsFile, Map<String, Double[]> inferredNetworks, String distanceType) {
        this.inferredNetworks = inferredNetworks;
        this.knownInteractionsMap = strKnownInteractionsFile == null ? null : new ListOfLinks(new File(strKnownInteractionsFile)).getMapWithLinks();
        if (distanceType == null) {
            this.distanceFunction = null;
        } else {
            if (distanceType.equals("all")) {
                this.distanceFunction = (Map<String, Double> consensusMap) -> {
                    return distanceAll(consensusMap);
                };
            } else if (distanceType.equals("some")) {
                this.distanceFunction = (Map<String, Double> consensusMap) -> {
                    return distanceSome(consensusMap);
                };
            } else if (distanceType.equals("one")) {
                this.distanceFunction = (Map<String, Double> consensusMap) -> {
                    return distanceOne(consensusMap);
                };
            } else {
                throw new IllegalArgumentException("Invalid distance type");
            }
        }
        
    }

    public abstract void repairSolutionOnly(DoubleSolution solution);
    public abstract void repairSolutionWithKnownInteractions(DoubleSolution solution);

    public interface DistanceFunction {
        public double run(Map<String, Double> consensusMap);
    }

    protected double absDistance(Map<String, Double> consensusMap, Map<String, Double> inputKnownInteractionsMap) {
        double sum = 0;
        for (Map.Entry<String, Double> pair : inputKnownInteractionsMap.entrySet()) {
            sum += consensusMap.containsKey(pair.getKey()) ? Math.abs(pair.getValue() - consensusMap.get(pair.getKey())) : 1;
        }
        return sum;
    }

    protected double distanceAll(Map<String, Double> consensusMap) {
        return absDistance(consensusMap, knownInteractionsMap);
    }

    protected double distanceSome(Map<String, Double> consensusMap) {
        int subsetSize = knownInteractionsMap.size() == 1 ? 1 : 1 + new Random().nextInt(knownInteractionsMap.size() - 1);
        return absDistance(consensusMap, getRandomSubsetMap(knownInteractionsMap, subsetSize));
    }

    protected double distanceOne(Map<String, Double> consensusMap) {
        return absDistance(consensusMap, getRandomSubsetMap(knownInteractionsMap, 1));
    }

    private Map<String, Double> getRandomSubsetMap(Map<String, Double> map, int subsetSize) {
        List<Map.Entry<String, Double>> entries = new ArrayList<>(map.entrySet());
        Collections.shuffle(entries);
        return entries.stream()
            .limit(subsetSize)
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
    }

    public double distance(Map<String, Double> consensusMap) {
        return distanceFunction.run(consensusMap);
    }

    protected Map<String, Double> getConfConsensusMap(double[] weights) {
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
}
