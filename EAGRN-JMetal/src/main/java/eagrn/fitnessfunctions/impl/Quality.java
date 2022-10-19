package eagrn.fitnessfunctions.impl;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import eagrn.StaticUtils;
import eagrn.fitnessfunctions.FitnessFunction;

/**
 * Try to minimize the quantity of high quality links (getting as close as possible
 * to 10 percent of the total possible links in the network) and at the same time maximize
 * the quality of these good links (maximize the mean of their confidence and weight adjustment).
 *
 * High quality links are those whose confidence-distance mean is above average.
 */

public class Quality implements FitnessFunction {
    private int numberOfNodes;
    private Map<String, Double[]> inferredNetworks;
    private Map<String, Double[]> medIntMap;

    public Quality (int numberOfNodes, Map<String, Double[]> inferredNetworks) {
        this.numberOfNodes = numberOfNodes;
        this.inferredNetworks = inferredNetworks;
        this.medIntMap = StaticUtils.calculateMedIntMap(inferredNetworks);
    }
    
    public double run(Map<String, Double> consensus, Double[] x) {
        /** 
         * 1. We create the map with the distances corresponding to the difference between the maximum and minimum 
         * of the vectors containing the mean between the weight and the distance normalized to the median of the total 
         * number of techniques 
         */
        Map<String, Double> distances = makeDistanceMap(consensus, x);

        /** 2. Calculate the mean of the confidence-distance means. */
        double conf, dist, confDistSum = 0;
        for (Map.Entry<String, Double> pair : consensus.entrySet()) {
            conf = pair.getValue();
            dist = distances.get(pair.getKey());
            confDistSum += (conf + (1 - dist)) / 2.0;
        }
        double mean = confDistSum / consensus.size();

        /** 3. Quantify the number of high quality links and calculate the average of their confidence-distance means */
        confDistSum = 0;
        double confDist, cnt = 0;
        for (Map.Entry<String, Double> pair : consensus.entrySet()) {
            conf = pair.getValue();
            dist = distances.get(pair.getKey());
            confDist = (conf + (1 - dist)) / 2.0;
            if (confDist > mean) {
                confDistSum += confDist;
                cnt += 1;
            }
        }

        /** 4. Calculate first term value */
        double numberOfLinks = (double) (numberOfNodes * numberOfNodes);
        double f1 = Math.abs(cnt - 0.1 * numberOfLinks)/((1 - 0.1) * numberOfLinks);
        double f2 = 1.0 - confDistSum/cnt;
        double fitness = 0.25*f1 + 0.75*f2;

        return fitness;
    }

    private Map<String, Double> makeDistanceMap(Map<String, Double> consensus, Double[] x){
        Map<String, Double> distanceMap = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : this.inferredNetworks.entrySet()) {
            Double[] medIntArray = this.medIntMap.get(pair.getKey());
            double median = medIntArray[0];
            double interval = medIntArray[1];

            Double[] weightDistances = new Double[x.length];
            for (int i = 0; i < x.length; i++) {
                weightDistances[i] = ((Math.abs(median - pair.getValue()[i]) / interval) + x[i]) / 2.0;
            }

            double min = Collections.min(Arrays.asList(weightDistances));
            double max = Collections.max(Arrays.asList(weightDistances));

            distanceMap.put(pair.getKey(), max - min);
        }

        return consensus;
    }
}
