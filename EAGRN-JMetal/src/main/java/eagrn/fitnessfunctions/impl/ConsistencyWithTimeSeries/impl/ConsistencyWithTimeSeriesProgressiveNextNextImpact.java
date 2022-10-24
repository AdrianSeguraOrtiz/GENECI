package eagrn.fitnessfunctions.impl.ConsistencyWithTimeSeries.impl;

import java.util.HashMap;
import java.util.Map;

import eagrn.fitnessfunctions.impl.ConsistencyWithTimeSeries.ConsistencyWithTimeSeries;

public class ConsistencyWithTimeSeriesProgressiveNextNextImpact extends ConsistencyWithTimeSeries {
    
    public ConsistencyWithTimeSeriesProgressiveNextNextImpact(Map<String, Double[]> timeSeriesMap) {
        super(timeSeriesMap);
        this.regulationSigns = getRegulationSigns(2);
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {

        double sumSquareError = 0;
        int cnt = 0;
        for (Map.Entry<String, Double[]> tsPair : super.timeSeriesMap.entrySet()) {
            Map<String, Double> factors = new HashMap<String, Double>();
            for (Map.Entry<String, Double> cPair : consensus.entrySet()) {
                String[] genes = cPair.getKey().split(";");
                if (tsPair.getKey().equals(genes[1])){
                    factors.put(genes[0], cPair.getValue() * super.regulationSigns.get(cPair.getKey()));
                }
            }
            
            for (int i = 2; i < tsPair.getValue().length - 1; i++) {
                double currExpLevel = tsPair.getValue()[i];
                double nextExpLevel = tsPair.getValue()[i+1];
                double prediction = currExpLevel;
                for (Map.Entry<String, Double> factor : factors.entrySet()) {
                    prediction += this.variationsMap.get(factor.getKey())[i-2] * factor.getValue();
                }
                sumSquareError += Math.pow(nextExpLevel - prediction, 2);
                cnt ++;
            }
        }
        return sumSquareError / Double.valueOf(cnt);
    }
}
