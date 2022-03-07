package eagrn.operator.repairer.impl;

import org.mockito.Mockito;
import org.testng.annotations.Test;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

import java.util.*;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class GreedyRepairerTest {

    @Test
    public void shouldReturnWeightVectorCaseA() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(3);
        for (int i = 0; i < 3; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.5);
        solution.variables().set(1, 1.0);
        solution.variables().set(2, 0.5);

        GreedyRepairer repairer = Mockito.spy(new GreedyRepairer());
        Mockito.when(repairer.getRandomPos(3)).thenReturn(0);
        repairer.repairSolution(solution);

        assertArrayEquals(new Double[]{0.5, 0.5, 0.0}, solution.variables().toArray());
    }

    @Test
    void shouldReturnWeightVectorCaseB() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.3);
        solution.variables().set(1, 0.6);
        solution.variables().set(2, 0.3);
        solution.variables().set(3, 1.2);
        solution.variables().set(4, 0.6);

        GreedyRepairer repairer = Mockito.spy(new GreedyRepairer());
        Mockito.when(repairer.getRandomPos(5)).thenReturn(2);
        repairer.repairSolution(solution);

        assertArrayEquals(new Double[]{0.0, 0.0, 0.3, 0.7, 0.0}, solution.variables().toArray());
    }

    @Test
    void shouldReturnWeightVectorCaseC() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.1);
        solution.variables().set(1, 0.05);
        solution.variables().set(2, 0.2);
        solution.variables().set(3, 0.0);
        solution.variables().set(4, 0.15);

        GreedyRepairer repairer = Mockito.spy(new GreedyRepairer());
        Mockito.when(repairer.getRandomPos(5)).thenReturn(2);
        repairer.repairSolution(solution);

        assertArrayEquals(new Double[]{0.1, 0.55, 0.2, 0.0, 0.15}, solution.variables().toArray());
    }
}
