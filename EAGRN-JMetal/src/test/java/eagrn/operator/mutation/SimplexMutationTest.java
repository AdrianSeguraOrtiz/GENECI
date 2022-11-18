package eagrn.operator.mutation;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import org.testng.annotations.Test;
import org.uma.jmetal.operator.mutation.MutationOperator;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

import eagrn.StaticUtils;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class SimplexMutationTest {
    @Test
    public void shouldReturnSolutionsWithSum1() {
        // Define bounds
        int numberOfVariables = 10;
        List<Double> lowerLimit = new ArrayList<>(numberOfVariables);
        List<Double> upperLimit = new ArrayList<>(numberOfVariables);
        for (int i = 0; i < numberOfVariables; i++) {
            lowerLimit.add(0.0);
            upperLimit.add(1.0);
        }
        List<Bounds<Double>> bounds = IntStream.range(0, lowerLimit.size())
            .mapToObj(i -> Bounds.create(lowerLimit.get(i), upperLimit.get(i)))
            .collect(Collectors.toList());

        // Instantiate mutation operator
        MutationOperator<DoubleSolution> mutation = new SimplexMutation(1, 0.1);

        for (int i = 0; i < 50; i++) {
            // Create solution
            DoubleSolution solution = new DefaultDoubleSolution(1, 0, bounds);
            StaticUtils.standardizeInitialSolution(solution);

            // Apply mutation
            DoubleSolution result = mutation.execute(solution);

            // Get sum
            double sum = 0.0;
            for (int j = 0; j < numberOfVariables; j++) {
                sum += result.variables().get(j);
            }

            // Verify that the sum of their values is 1
            assertTrue(Math.abs(sum - 1.0) < 0.01);
        }
    }
}
