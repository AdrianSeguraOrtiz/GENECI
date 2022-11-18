package eagrn.fitnessfunction.impl.quality.impl;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.impl.quality.Quality;
import eagrn.fitnessfunction.impl.quality.TrendMeasureEnum;

import java.util.Map;


/**
 * Try to minimize the quantity of high quality links (getting as close as possible
 * to 10 percent of the total possible links in the network) and at the same time maximize
 * the quality of these good links (maximize the mean of their confidence and weight adjustment).
 *
 * High quality links are those whose confidence-distance mean is above average.
 */

public class QualityMeanAboveCutOff extends Quality {
    private CutOffCriteria cutOffCriteria;
    
    public QualityMeanAboveCutOff(Map<String, Double[]> inferredNetworks, CutOffCriteria cutOffCriteria) {
        super(inferredNetworks, TrendMeasureEnum.MEAN);
        this.cutOffCriteria = cutOffCriteria;
    }

    public double run(Map<String, Double> consensus, Double[] x) {
        /** 
         * 1. We create the map with the distances corresponding to the difference between the maximum and minimum 
         * of the vectors containing the mean between the weight and the distance normalized to the mean of the total 
         * number of techniques 
         */
        Map<String, Double> distances = super.makeDistanceMap(consensus, x);

        /** 2. Get high quality links */
        Map<String, Double> goodLinks = cutOffCriteria.getCutMap(consensus);

        /** 3. Calculate the average of confidence-distance means of high quality links */
        double conf, dist, confDistSum = 0;
        for (Map.Entry<String, Double> pair : goodLinks.entrySet()) {
            conf = pair.getValue();
            dist = distances.get(pair.getKey());
            confDistSum += (conf + (1 - dist)) / 2.0;
        }
        double mean = confDistSum / goodLinks.size();

        /** 4. Return fitness */
        return 1.0 - mean;
    }
}
