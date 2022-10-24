package eagrn.fitnessfunctions.impl.Quality.impl;

import eagrn.fitnessfunctions.impl.Quality.Quality;
import eagrn.fitnessfunctions.impl.Quality.TrendMeasureEnum;
import java.util.Map;


/**
 * Try to minimize the quantity of high quality links (getting as close as possible
 * to 10 percent of the total possible links in the network) and at the same time maximize
 * the quality of these good links (maximize the mean of their confidence and weight adjustment).
 *
 * High quality links are those whose confidence-distance mean is above average.
 */

public class QualityMeanAboveAverageWithContrast extends Quality {
    private int numberOfNodes;
    
    public QualityMeanAboveAverageWithContrast(int numberOfNodes, Map<String, Double[]> inferredNetworks) {
        super(inferredNetworks, TrendMeasureEnum.MEAN);
        this.numberOfNodes = numberOfNodes;
    }

    public double run(Map<String, Double> consensus, Double[] x) {
        /** 
         * 1. We create the map with the distances corresponding to the difference between the maximum and minimum 
         * of the vectors containing the mean between the weight and the distance normalized to the mean of the total 
         * number of techniques 
         */
        Map<String, Double> distances = super.makeDistanceMap(consensus, x);

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
        double numberOfLinks = Double.valueOf(numberOfNodes * numberOfNodes);
        double f1 = Math.abs(cnt - 0.1 * numberOfLinks)/((1 - 0.1) * numberOfLinks);
        double f2 = 1.0 - confDistSum/cnt;
        double fitness = 0.25*f1 + 0.75*f2;

        return fitness;
    }
}
