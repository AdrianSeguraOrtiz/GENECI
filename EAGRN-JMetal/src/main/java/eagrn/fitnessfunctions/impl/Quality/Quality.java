package eagrn.fitnessfunctions.impl.Quality;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import eagrn.fitnessfunctions.FitnessFunction;

public abstract class Quality implements FitnessFunction{
    private Map<String, Double[]> inferredNetworks;
    private Map<String, Double[]> trendMeasureIntervalMap;

    public Quality (int numberOfNodes, Map<String, Double[]> inferredNetworks, TrendMeasureEnum trendMeasure) {
        this.inferredNetworks = inferredNetworks;
        this.trendMeasureIntervalMap = calculateTrendMeasureIntervalMap(inferredNetworks, trendMeasure);
    }

    protected Map<String, Double[]> calculateTrendMeasureIntervalMap(Map<String, Double[]> inferredNetworks, TrendMeasureEnum trendMeasure) {
        /**
         * For each interaction, calculate the trend measure and the distance to the farthest point 
         * of it for the confidence levels reported by each technique.
         */

        Map<String, Double[]> res = new HashMap<>();

        for (Map.Entry<String, Double[]> entry : inferredNetworks.entrySet()) {
            Double[] confidences = entry.getValue();
            Arrays.sort(confidences);

            double trendMeasureValue = 0.0;
            switch (trendMeasure) {
                case MEDIAN:
                    int middle = confidences.length / 2;
                    if (confidences.length % 2 == 0) {
                        trendMeasureValue = (confidences[middle - 1] + confidences[middle]) / 2.0;
                    } else {
                        trendMeasureValue = confidences[middle];
                    }
                case MEAN:
                    double sum = 0.0;
                    for (int i = 0; i < confidences.length; i++) {
                        sum += confidences[i];
                    }
                    trendMeasureValue = sum / Double.valueOf(confidences.length);
            }

            double min = Collections.min(Arrays.asList(confidences));
            double max = Collections.max(Arrays.asList(confidences));
            double interval = Math.max(trendMeasureValue - min, max - trendMeasureValue);

            res.put(entry.getKey(), new Double[]{trendMeasureValue, interval});
        }
        return res;
    }

    protected Map<String, Double> makeDistanceMap(Map<String, Double> consensus, Double[] x){
        Map<String, Double> distanceMap = new HashMap<>();

        for (Map.Entry<String, Double[]> pair : this.inferredNetworks.entrySet()) {
            Double[] trendMeasureIntervalArray = this.trendMeasureIntervalMap.get(pair.getKey());
            double trendMeasure = trendMeasureIntervalArray[0];
            double interval = trendMeasureIntervalArray[1];

            Double[] weightDistances = new Double[x.length];
            for (int i = 0; i < x.length; i++) {
                weightDistances[i] = ((Math.abs(trendMeasure - pair.getValue()[i]) / interval) + x[i]) / 2.0;
            }

            double min = Collections.min(Arrays.asList(weightDistances));
            double max = Collections.max(Arrays.asList(weightDistances));

            distanceMap.put(pair.getKey(), max - min);
        }

        return consensus;
    }
}
