package eagrn.operator.repairer.impl;

import org.testng.annotations.Test;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class StandardizationRepairerTest {

    @Test
    void shouldReturnWeightVectorCaseA() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(3);
        for (int i = 0; i < 3; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.5);
        solution.variables().set(1, 1.0);
        solution.variables().set(2, 0.5);

        StandardizationRepairer repairer = new StandardizationRepairer(null, null, null, 0);
        repairer.repairSolutionOnly(solution);

        assertArrayEquals(new Double[]{0.25, 0.5, 0.25}, solution.variables().toArray());
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

        StandardizationRepairer repairer = new StandardizationRepairer(null, null, null, 0);
        repairer.repairSolutionOnly(solution);

        assertArrayEquals(new Double[]{0.1, 0.2, 0.1, 0.4, 0.2}, solution.variables().toArray());
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

        StandardizationRepairer repairer = new StandardizationRepairer(null, null, null, 0);
        repairer.repairSolutionOnly(solution);

        assertArrayEquals(new Double[]{0.2, 0.1, 0.4, 0.0, 0.3}, solution.variables().toArray());
    }

    @Test
    void shouldReturnWeightVectorCaseD() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.5);
        solution.variables().set(1, 0.5);
        solution.variables().set(2, 0.5);
        solution.variables().set(3, 0.5);
        solution.variables().set(4, 0.5);

        try {
            File tempFile = File.createTempFile("known_interactions", ".csv");
            String[] strKnownInteractions = new String[]{
                "G1,G2,1",
                "G1,G3,1",
            };
            writeDataToCsv(tempFile, strKnownInteractions);

            Map<String, Double[]> inferredNetworks = new HashMap<>();
            inferredNetworks.put("G1;G2", new Double[]{0.9, 0.5, 0.0, 0.2, 0.6});
            inferredNetworks.put("G1;G3", new Double[]{0.8, 0.5, 0.2, 0.1, 0.4});

            StandardizationRepairer repairer = new StandardizationRepairer(tempFile.getAbsolutePath(), inferredNetworks, "all", 1.0);
            repairer.repairSolutionWithKnownInteractions(solution);

        } catch (IOException e) {
            e.printStackTrace();
        }

        assertArrayEquals(new Double[]{0.3333, 0.1667, 0.1667, 0.1667, 0.1667}, solution.variables().toArray());
    }

    @Test
    void shouldReturnWeightVectorCaseE() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 1.0);
        solution.variables().set(1, 0.0);
        solution.variables().set(2, 0.0);
        solution.variables().set(3, 0.0);
        solution.variables().set(4, 0.0);

        try {
            File tempFile = File.createTempFile("known_interactions", ".csv");
            String[] strKnownInteractions = new String[]{
                "G1,G2,1",
                "G1,G3,1",
            };
            writeDataToCsv(tempFile, strKnownInteractions);

            Map<String, Double[]> inferredNetworks = new HashMap<>();
            inferredNetworks.put("G1;G2", new Double[]{0.9, 0.5, 0.0, 0.2, 0.6});
            inferredNetworks.put("G1;G3", new Double[]{0.8, 0.5, 0.2, 0.1, 0.4});

            StandardizationRepairer repairer = new StandardizationRepairer(tempFile.getAbsolutePath(), inferredNetworks, "all", 1.0);
            repairer.repairSolutionWithKnownInteractions(solution);

        } catch (IOException e) {
            e.printStackTrace();
        }

        assertArrayEquals(new Double[]{1.0, 0.0, 0.0, 0.0, 0.0}, solution.variables().toArray());
    }

    private static void writeDataToCsv(File file, String[] data) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            for (String line : data) {
                writer.write(line);
                writer.newLine();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
