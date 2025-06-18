package eagrn.operator.mutation;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.stream.Collectors;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.StaticUtils;

public class SimplexMutationWithLocalSearch extends SimplexMutation {

    public interface DistanceFunction {
        public double run(Map<String, Float> consensusMap);
    }

    protected Map<String, Float[]> inferredNetworks;
    protected Map<String, Float> knownInteractionsMap;
    protected DistanceFunction distanceFunction;
    public double memeticPropability;

    public SimplexMutationWithLocalSearch(double mutationProbability, double mutationStrength, Map<String, Float[]> inferredNetworks, String strKnownInteractionsFile, String strMemeticDistanceType, double memeticPropability) {
        super(mutationProbability, mutationStrength);
        this.inferredNetworks = inferredNetworks;
        this.memeticPropability = memeticPropability;
        this.knownInteractionsMap = StaticUtils.getMapWithLinks(new File(strKnownInteractionsFile));
        if (strMemeticDistanceType.equals("all")) {
            this.distanceFunction = (Map<String, Float> consensusMap) -> {
                return distanceAll(consensusMap);
            };
        } else if (strMemeticDistanceType.equals("some")) {
            this.distanceFunction = (Map<String, Float> consensusMap) -> {
                return distanceSome(consensusMap);
            };
        } else if (strMemeticDistanceType.equals("one")) {
            this.distanceFunction = (Map<String, Float> consensusMap) -> {
                return distanceOne(consensusMap);
            };
        } else {
            throw new IllegalArgumentException("Invalid distance type");
        }
    }

    protected double absDistance(Map<String, Float> consensusMap, Map<String, Float> inputKnownInteractionsMap) {
        double sum = 0;
        for (Map.Entry<String, Float> pair : inputKnownInteractionsMap.entrySet()) {
            sum += consensusMap.containsKey(pair.getKey()) ? Math.abs(pair.getValue() - consensusMap.get(pair.getKey())) : 1;
        }
        return sum;
    }

    protected double distanceAll(Map<String, Float> consensusMap) {
        return absDistance(consensusMap, knownInteractionsMap);
    }

    protected double distanceSome(Map<String, Float> consensusMap) {
        int subsetSize = knownInteractionsMap.size() == 1 ? 1 : 1 + new Random().nextInt(knownInteractionsMap.size() - 1);
        return absDistance(consensusMap, getRandomSubsetMap(knownInteractionsMap, subsetSize));
    }

    protected double distanceOne(Map<String, Float> consensusMap) {
        return absDistance(consensusMap, getRandomSubsetMap(knownInteractionsMap, 1));
    }

    private Map<String, Float> getRandomSubsetMap(Map<String, Float> map, int subsetSize) {
        List<Map.Entry<String, Float>> entries = new ArrayList<>(map.entrySet());
        Collections.shuffle(entries);
        return entries.stream()
            .limit(subsetSize)
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
    }

    public double distance(Map<String, Float> consensusMap) {
        return distanceFunction.run(consensusMap);
    }

    @Override
    public DoubleSolution execute(DoubleSolution source) {
        DoubleSolution mutated_sol = super.execute(source);

        if (Math.random() <= memeticPropability) {
            int numTecs = mutated_sol.variables().size();
            Double[] x = new Double[numTecs];
            for (int i = 0; i < numTecs; i++) {
                x[i] = mutated_sol.variables().get(i);
            }
            DoubleSolution resSolution = (DoubleSolution) mutated_sol.copy();
            double minDistance = Double.MAX_VALUE;
            for (int i = -1; i < numTecs; i++) {
                DoubleSolution tmpSolution = (DoubleSolution) mutated_sol.copy();
                if (i != -1) {
                    tmpSolution.variables().set(i, (x[i] + (1.0/numTecs)) / (1 + (1.0/numTecs)));
                    for (int j = 0; j < numTecs; j++) {
                        if (j != i) tmpSolution.variables().set(j, x[j] / (1 + (1.0/numTecs)));
                    }
                }
                Double[] y = new Double[numTecs];
                for (int j = 0; j < numTecs; j++) {
                    y[j] = tmpSolution.variables().get(j);
                }

                double tmpDistance = distance(StaticUtils.makeConsensus(y, this.inferredNetworks));
                if (tmpDistance < minDistance) {
                    minDistance = tmpDistance;
                    resSolution = tmpSolution;
                }
            }
            mutated_sol.variables().clear();
            mutated_sol.variables().addAll(resSolution.variables());
        } 

        return mutated_sol;
    }
}
