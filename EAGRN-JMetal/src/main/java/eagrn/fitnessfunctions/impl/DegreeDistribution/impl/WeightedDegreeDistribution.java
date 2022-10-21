package eagrn.fitnessfunctions.impl.DegreeDistribution.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import eagrn.fitnessfunctions.impl.DegreeDistribution.DegreeDistribution;

public class WeightedDegreeDistribution extends DegreeDistribution {
    private ArrayList<String> geneNames;

    public WeightedDegreeDistribution(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
    }

    public double run(Map<String, Double> consensus, Double[] x) {
        
        Map<String, Double> undirectedDegreesMap = new HashMap<>();
        for (Map.Entry<String, Double> pair : consensus.entrySet()) {
            String[] genes = pair.getKey().split(";");
            undirectedDegreesMap.put(genes[0], undirectedDegreesMap.getOrDefault(genes[0], 0.0) + pair.getValue());
            undirectedDegreesMap.put(genes[1], undirectedDegreesMap.getOrDefault(genes[1], 0.0) + pair.getValue());
        }

        double[] undirectedDegreesPlusMin = new double[geneNames.size()];
        for (int i = 0; i < geneNames.size(); i++) {
            undirectedDegreesPlusMin[i] = undirectedDegreesMap.get(geneNames.get(i)) + Double.MIN_VALUE;
        }
        return -super.paretoTest(undirectedDegreesPlusMin);
    }
}
