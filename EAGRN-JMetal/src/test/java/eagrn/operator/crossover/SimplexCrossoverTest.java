package eagrn.operator.crossover;

import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

import eagrn.old.repairer.WeightRepairer;
import eagrn.old.repairer.impl.StandardizationRepairer;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import org.testng.annotations.Test;

public class SimplexCrossoverTest {
    @Test
    public void shouldReturnOffSpringWithSum1() {
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

        // Instantiate repairer
        WeightRepairer initialPopulationRepairer = new StandardizationRepairer();

        // Instantiate crossover operator
        CrossoverOperator<DoubleSolution> crossover = new SimplexCrossover(3, 1, 1);

        for (int i = 0; i < 50; i++) {
            // Create parents
            DoubleSolution parent1 = new DefaultDoubleSolution(1, 0, bounds);
            DoubleSolution parent2 = new DefaultDoubleSolution(1, 0, bounds);
            DoubleSolution parent3 = new DefaultDoubleSolution(1, 0, bounds);
            initialPopulationRepairer.repairSolution(parent1);
            initialPopulationRepairer.repairSolution(parent2);
            initialPopulationRepairer.repairSolution(parent3);

            // Insert them in a list
            List<DoubleSolution> parents = new ArrayList<DoubleSolution>();
            parents.add(parent1);
            parents.add(parent2);
            parents.add(parent3);

            // Apply SPX crossover
            List<DoubleSolution> childs = crossover.execute(parents);

            // Get child
            double sum = 0.0;
            for (int j = 0; j < numberOfVariables; j++) {
                sum += childs.get(0).variables().get(j);
            }

            // Verify that the sum of their values is 1
            assertTrue(Math.abs(sum - 1.0) < 0.01);
        }
    }
}
