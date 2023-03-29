package eagrn.fitnessfunction.impl.loyalty.impl;

import java.util.HashMap;
import java.util.Map;

import eagrn.fitnessfunction.impl.loyalty.Loyalty;

public class LoyaltyFinal extends Loyalty {
    
    public LoyaltyFinal(Map<String, Double[]> timeSeriesMap) {
        super(timeSeriesMap);
        this.regulationSigns = getRegulationSigns(0);
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {

        double sumSquareError = 0;
        int cnt = 0;
        for (Map.Entry<String, Double[]> tsPair : super.timeSeriesMap.entrySet()) {
            Map<String, Double> factors = new HashMap<String, Double>();
            for (Map.Entry<String, Float> cPair : consensus.entrySet()) {
                String[] genes = cPair.getKey().split(";");
                if (tsPair.getKey().equals(genes[1])){
                    Double[] tsFactor = super.timeSeriesMap.get(genes[0]);
                    double globalChange = tsFactor[tsFactor.length - 1] - tsFactor[0];
                    factors.put(genes[0], cPair.getValue() * super.regulationSigns.get(cPair.getKey()) * globalChange);
                }
            }
            
            Double[] tsTarget = tsPair.getValue();
            double firstExpLevel = tsTarget[0];
            double lastExpLevel = tsTarget[tsTarget.length - 1];
            double prediction = firstExpLevel;
            for (Map.Entry<String, Double> factor : factors.entrySet()) {
                prediction += factor.getValue();
            }
            sumSquareError += Math.pow(lastExpLevel - prediction, 2);
            cnt ++;
        }
        return sumSquareError / Double.valueOf(cnt);
    }
}
