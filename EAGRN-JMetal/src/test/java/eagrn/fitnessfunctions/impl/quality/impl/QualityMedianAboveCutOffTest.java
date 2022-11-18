package eagrn.fitnessfunctions.impl.quality.impl;

import eagrn.StaticUtils;
import eagrn.cutoffcriteria.impl.NumLinksWithBestConfCriteria;
import eagrn.fitnessfunction.impl.quality.impl.QualityMedianAboveCutOff;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.testng.annotations.Test;

public class QualityMedianAboveCutOffTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        Map<String, Double[]> inferredNetworks = new HashMap<>();
        inferredNetworks.put("G1;G2", new Double[]{0.78, 0.9, 0.69});
        inferredNetworks.put("G5;G6", new Double[]{0.63, 0.71, 0.0});
        inferredNetworks.put("G4;G3", new Double[]{0.21, 0.0, 0.48});
        inferredNetworks.put("G2;G3", new Double[]{0.0, 0.53, 0.36});

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("G1");
        geneNames.add("G2");
        geneNames.add("G3");
        geneNames.add("G4");
        geneNames.add("G5");
        geneNames.add("G6");

        NumLinksWithBestConfCriteria numLinksWithBestConfCriteria = new NumLinksWithBestConfCriteria(2, geneNames);
        QualityMedianAboveCutOff qualityMedianAboveCutOff = new QualityMedianAboveCutOff(inferredNetworks, numLinksWithBestConfCriteria);

        Double[] goodWeights = new Double[]{0.5, 0.3, 0.2};
        Map<String, Double> consensusOfGoodWeights = StaticUtils.makeConsensus(goodWeights, inferredNetworks);

        Double[] badWeights = new Double[]{0.2, 0.3, 0.5};
        Map<String, Double> consensusOfBadWeights = StaticUtils.makeConsensus(badWeights, inferredNetworks);

        double fitnessGoodWeights = qualityMedianAboveCutOff.run(consensusOfGoodWeights, goodWeights);
        double fitnessBadWeights = qualityMedianAboveCutOff.run(consensusOfBadWeights, badWeights);

        System.out.println("Good Weights: " + fitnessGoodWeights);
        System.out.println("Bad Weights: " + fitnessBadWeights);

        assert(fitnessGoodWeights < fitnessBadWeights);
    }
    
}
