package eagrn.fitnessfunction.impl.quality;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import eagrn.fitnessfunction.FitnessFunction;


public abstract class Quality implements FitnessFunction{
    private Map<String, Float[]> inferredNetworks;
    private Map<String, Float[]> trendMeasureIntervalMap;

    public Quality (Map<String, Float[]> inferredNetworks, TrendMeasureEnum trendMeasure) {
        this.inferredNetworks = inferredNetworks;
        this.trendMeasureIntervalMap = calculateTrendMeasureIntervalMap(inferredNetworks, trendMeasure);
    }

    protected Map<String, Float[]> calculateTrendMeasureIntervalMap(Map<String, Float[]> inferredNetworks, TrendMeasureEnum trendMeasure) {
        /**
         * For each interaction, calculate the trend measure and the distance to the farthest point 
         * of it for the confidence levels reported by each technique.
         */

        Map<String, Float[]> res = new HashMap<>();

        for (Map.Entry<String, Float[]> entry : inferredNetworks.entrySet()) {
            Float[] confidences = entry.getValue();

            float trendMeasureValue = 0.0f;
            switch (trendMeasure) {
                case MEDIAN:
                    Float[] cloneSorted = confidences.clone();
                    Arrays.sort(cloneSorted);
                    int middle = cloneSorted.length / 2;
                    if (cloneSorted.length % 2 == 0) {
                        trendMeasureValue = (float) ((cloneSorted[middle - 1] + cloneSorted[middle]) / 2.0);
                    } else {
                        trendMeasureValue = cloneSorted[middle];
                    }
                    break;
                case MEAN:
                    double sum = 0.0;
                    for (int i = 0; i < confidences.length; i++) {
                        sum += confidences[i];
                    }
                    trendMeasureValue = (float) (sum / Float.valueOf(confidences.length));
                    break;
            }

            float min = Collections.min(Arrays.asList(confidences));
            float max = Collections.max(Arrays.asList(confidences));
            float interval = Math.max(trendMeasureValue - min, max - trendMeasureValue);

            res.put(entry.getKey(), new Float[]{trendMeasureValue, interval});
        }

        return res;
    }

    protected Map<String, Float> makeDistanceMap(Map<String, Float> consensus, Double[] x){
        Map<String, Float> distanceMap = new HashMap<>();

        for (Map.Entry<String, Float[]> pair : this.inferredNetworks.entrySet()) {
            Float[] trendMeasureIntervalArray = this.trendMeasureIntervalMap.get(pair.getKey());
            float trendMeasure = trendMeasureIntervalArray[0];
            float interval = trendMeasureIntervalArray[1];

            Float[] weightDistances = new Float[x.length];
            for (int i = 0; i < x.length; i++) {
                weightDistances[i] = (float) (((Math.abs(trendMeasure - pair.getValue()[i]) / interval) + x[i]) / 2.0);
            }

            float min = Collections.min(Arrays.asList(weightDistances));
            float max = Collections.max(Arrays.asList(weightDistances));

            distanceMap.put(pair.getKey(), max - min);
        }

        return distanceMap;
    }
}
