package eagrn.old.repairer.impl;

import org.testng.annotations.Test;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

import java.util.*;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class NullRepairerTest {

    @Test
    void shouldReturnWeightVectorCaseA() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(3);
        for (int i = 0; i < 3; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.5);
        solution.variables().set(1, 0.2);
        solution.variables().set(2, 0.3);

        StandardizationRepairer repairer = new StandardizationRepairer();
        repairer.repairSolution(solution);

        assertArrayEquals(new Double[]{0.5, 0.2, 0.3}, solution.variables().toArray());
    }
}
