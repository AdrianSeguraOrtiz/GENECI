package eagrn.operator.mutation;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import eagrn.StaticUtils;

public class SimplexMutation implements MutationOperator<DoubleSolution> {
    private double mutationProbability;
    private double mutationStrength;
    private JMetalRandom random;

    public SimplexMutation(double mutationProbability, double mutationStrength) {
        this.mutationProbability = mutationProbability;
        this.mutationStrength = mutationStrength;
        this.random = JMetalRandom.getInstance();
    }

    @Override
    public DoubleSolution execute(DoubleSolution source) {
        if (random.nextDouble(0, 1) < mutationProbability) {
            int numVariables = source.variables().size();
            int teamRestSize = random.nextInt(1, numVariables - 1);
            int teamSumSize = random.nextInt(1, numVariables - teamRestSize);

            List<Integer> availablePositions = IntStream.range(0, numVariables).boxed().collect(Collectors.toList());
            Collections.shuffle(availablePositions);
            List<Integer> teamRestPositions = availablePositions.subList(0, teamRestSize);
            List<Integer> teamSumPositions = availablePositions.subList(teamRestSize, teamRestSize + teamSumSize);

            double amount = 0.0;
            double[] teamRest = new double[teamRestSize];
            for (int i = 0; i < teamRestSize; i++) {
                teamRest[i] = source.variables().get(teamRestPositions.get(i));
                amount += teamRest[i];
            }
            amount *= mutationStrength;
            double[] teamRestNormalized = StaticUtils.standardize(teamRest);

            for (int i = 0; i < teamRestSize; i++) {
                source.variables().set(teamRestPositions.get(i), teamRest[i] - amount * teamRestNormalized[i]);
            }

            double[] teamSum = new double[teamSumSize];
            for (int i = 0; i < teamSumSize; i++) {
                teamSum[i] = source.variables().get(teamSumPositions.get(i));
            }
            double[] teamSumNormalized = StaticUtils.standardize(teamSum);

            for (int i = 0; i < teamSumSize; i++) {
                source.variables().set(teamSumPositions.get(i), teamSum[i] + amount * teamSumNormalized[i]);
            }
        }

        return source;
    }

    @Override
    public double getMutationProbability() {
        return mutationProbability;
    }
    
}
