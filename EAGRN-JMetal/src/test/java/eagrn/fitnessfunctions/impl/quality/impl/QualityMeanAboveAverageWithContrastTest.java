package eagrn.fitnessfunctions.impl.quality.impl;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.quality.impl.QualityMeanAboveAverageWithContrast;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.testng.annotations.Test;

public class QualityMeanAboveAverageWithContrastTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        Map<String, Float[]> inferredNetworks = new HashMap<>();
        inferredNetworks.put("G1;G2", new Float[]{0.78f, 0.9f, 0.69f});
        inferredNetworks.put("G5;G6", new Float[]{0.63f, 0.71f, 0.0f});
        inferredNetworks.put("G4;G3", new Float[]{0.21f, 0.0f, 0.48f});
        inferredNetworks.put("G2;G3", new Float[]{0.0f, 0.53f, 0.36f});

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("G1");
        geneNames.add("G2");
        geneNames.add("G3");
        geneNames.add("G4");
        geneNames.add("G5");
        geneNames.add("G6");

        QualityMeanAboveAverageWithContrast qualityMeanAboveAverageWithContrast = new QualityMeanAboveAverageWithContrast(geneNames.size(), inferredNetworks);

        Double[] goodWeights = new Double[]{0.5, 0.3, 0.2};
        Map<String, Float> consensusOfGoodWeights = StaticUtils.makeConsensus(goodWeights, inferredNetworks);

        Double[] badWeights = new Double[]{0.2, 0.3, 0.5};
        Map<String, Float> consensusOfBadWeights = StaticUtils.makeConsensus(badWeights, inferredNetworks);

        double fitnessGoodWeights = qualityMeanAboveAverageWithContrast.run(consensusOfGoodWeights, goodWeights);
        double fitnessBadWeights = qualityMeanAboveAverageWithContrast.run(consensusOfBadWeights, badWeights);

        System.out.println("Good Weights: " + fitnessGoodWeights);
        System.out.println("Bad Weights: " + fitnessBadWeights);

        assert(fitnessGoodWeights < fitnessBadWeights);
    }
    
}
