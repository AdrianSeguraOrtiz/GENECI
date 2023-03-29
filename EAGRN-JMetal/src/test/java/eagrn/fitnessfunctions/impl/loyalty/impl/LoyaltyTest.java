package eagrn.fitnessfunctions.impl.loyalty.impl;

import java.util.HashMap;
import java.util.Map;

import org.testng.annotations.Test;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.loyalty.impl.LoyaltyProgressiveCurrentImpact;

public class LoyaltyTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        Map<String, Double[]> timeSeriesMap = new HashMap<>();
        timeSeriesMap.put("G1", new Double[]{1.0, 4.0, 6.0, 3.0});
        timeSeriesMap.put("G2", new Double[]{0.0, 2.0, 3.0, 1.0});
        timeSeriesMap.put("G3", new Double[]{4.0, 2.0, 1.0, 3.0});
        timeSeriesMap.put("G4", new Double[]{4.0, 3.0, 2.0, 4.0});
        timeSeriesMap.put("G5", new Double[]{1.0, 2.0, 3.0, 4.0});
        timeSeriesMap.put("G6", new Double[]{4.0, 3.0, 2.0, 1.0});

        LoyaltyProgressiveCurrentImpact loyaltyProgressiveCurrentImpact = new LoyaltyProgressiveCurrentImpact(timeSeriesMap);

        Map<String, Float[]> inferredNetworks = new HashMap<>();
        inferredNetworks.put("G1;G2", new Float[]{0.78f, 0.9f, 0.69f}); //Activa
        inferredNetworks.put("G5;G6", new Float[]{0.63f, 0.71f, 0.0f}); //Inhibe
        inferredNetworks.put("G4;G3", new Float[]{0.21f, 0.0f, 0.48f}); //Activa
        inferredNetworks.put("G2;G3", new Float[]{0.0f, 0.53f, 0.36f}); //Inhibe

        /**
         * Since all interactions have been strictly reflected in the time series, the best distribution of weights 
         * in this case is the one that achieves the highest confidence values in the consensus network.
         */
        Double[] goodWeights = new Double[]{0.2, 0.6, 0.2};
        Map<String, Float> consensusOfGoodWeights = StaticUtils.makeConsensus(goodWeights, inferredNetworks);

        Double[] badWeights = new Double[]{0.5, 0.1, 0.4};
        Map<String, Float> consensusOfBadWeights = StaticUtils.makeConsensus(badWeights, inferredNetworks);

        double fitnessGoodWeights = loyaltyProgressiveCurrentImpact.run(consensusOfGoodWeights, goodWeights);
        double fitnessBadWeights = loyaltyProgressiveCurrentImpact.run(consensusOfBadWeights, badWeights);

        System.out.println("Good Weights: " + fitnessGoodWeights);
        System.out.println("Bad Weights: " + fitnessBadWeights);

        assert(fitnessGoodWeights < fitnessBadWeights);
    }
    
}
