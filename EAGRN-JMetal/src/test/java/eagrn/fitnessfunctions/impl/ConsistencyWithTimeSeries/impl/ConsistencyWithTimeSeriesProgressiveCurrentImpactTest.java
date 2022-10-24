package eagrn.fitnessfunctions.impl.ConsistencyWithTimeSeries.impl;

import java.util.HashMap;
import java.util.Map;

import org.testng.annotations.Test;

import eagrn.StaticUtils;

public class ConsistencyWithTimeSeriesProgressiveCurrentImpactTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        Map<String, Double[]> timeSeriesMap = new HashMap<>();
        timeSeriesMap.put("G1", new Double[]{1.0, 4.0, 6.0, 3.0});
        timeSeriesMap.put("G2", new Double[]{0.0, 2.0, 3.0, 1.0});
        timeSeriesMap.put("G3", new Double[]{4.0, 2.0, 1.0, 3.0});
        timeSeriesMap.put("G4", new Double[]{4.0, 3.0, 2.0, 4.0});
        timeSeriesMap.put("G5", new Double[]{1.0, 2.0, 3.0, 4.0});
        timeSeriesMap.put("G6", new Double[]{4.0, 3.0, 2.0, 1.0});

        ConsistencyWithTimeSeriesProgressiveCurrentImpact consistencyWithTimeSeriesProgressiveCurrentImpact = new ConsistencyWithTimeSeriesProgressiveCurrentImpact(timeSeriesMap);

        Map<String, Double[]> inferredNetworks = new HashMap<>();
        inferredNetworks.put("G1;G2", new Double[]{0.78, 0.9, 0.69}); //Activa
        inferredNetworks.put("G5;G6", new Double[]{0.63, 0.71, 0.0}); //Inhibe
        inferredNetworks.put("G4;G3", new Double[]{0.21, 0.0, 0.48}); //Activa
        inferredNetworks.put("G2;G3", new Double[]{0.0, 0.53, 0.36}); //Inhibe

        /**
         * Since all interactions have been strictly reflected in the time series, the best distribution of weights 
         * in this case is the one that achieves the highest confidence values in the consensus network.
         */
        Double[] goodWeights = new Double[]{0.2, 0.6, 0.2};
        Map<String, Double> consensusOfGoodWeights = StaticUtils.makeConsensus(goodWeights, inferredNetworks);

        Double[] badWeights = new Double[]{0.5, 0.1, 0.4};
        Map<String, Double> consensusOfBadWeights = StaticUtils.makeConsensus(badWeights, inferredNetworks);

        double fitnessGoodWeights = consistencyWithTimeSeriesProgressiveCurrentImpact.run(consensusOfGoodWeights, goodWeights);
        double fitnessBadWeights = consistencyWithTimeSeriesProgressiveCurrentImpact.run(consensusOfBadWeights, badWeights);

        System.out.println("Good Weights: " + fitnessGoodWeights);
        System.out.println("Bad Weights: " + fitnessBadWeights);

        assert(fitnessGoodWeights < fitnessBadWeights);
    }
    
}
