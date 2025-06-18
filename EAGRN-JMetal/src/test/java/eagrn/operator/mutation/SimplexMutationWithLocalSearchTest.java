package eagrn.operator.mutation;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

public class SimplexMutationWithLocalSearchTest {

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
    
    @Test
    void shouldReturnClosestOptionCaseA() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.2);
        solution.variables().set(1, 0.2);
        solution.variables().set(2, 0.2);
        solution.variables().set(3, 0.2);
        solution.variables().set(4, 0.2);

        DoubleSolution result = null;
        try {
            File tempFile = File.createTempFile("known_interactions", ".csv");
            String[] strKnownInteractions = new String[]{
                "G1,G2,1",
                "G1,G3,1",
            };
            writeDataToCsv(tempFile, strKnownInteractions);

            Map<String, Float[]> inferredNetworks = new HashMap<>();
            inferredNetworks.put("G1;G2", new Float[]{0.9f, 0.5f, 0.0f, 0.2f, 0.6f});
            inferredNetworks.put("G1;G3", new Float[]{0.8f, 0.5f, 0.2f, 0.1f, 0.4f});

            SimplexMutationWithLocalSearch mutation = new SimplexMutationWithLocalSearch(0.0, 0.0, inferredNetworks, tempFile.getAbsolutePath(), "all", 1.0);
            result = mutation.execute(solution);

        } catch (IOException e) {
            e.printStackTrace();
        }

        assertArrayEquals(
            new double[]{0.3333, 0.1667, 0.1667, 0.1667, 0.1667},
            result.variables().stream().mapToDouble(Double::doubleValue).toArray(),
            0.001
        );
    }

    @Test
    void shouldReturnClosestOptionCaseB() {
        Bounds<Double> bounds = Bounds.create(0.0, 1.0);
        List<Bounds<Double>> listOfBounds = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) listOfBounds.add(bounds);

        DefaultDoubleSolution solution = new DefaultDoubleSolution(1, 0, listOfBounds);
        solution.variables().set(0, 0.1);
        solution.variables().set(1, 0.1);
        solution.variables().set(2, 0.1);
        solution.variables().set(3, 0.1);
        solution.variables().set(4, 0.6);

        DoubleSolution result = null;
        try {
            File tempFile = File.createTempFile("known_interactions", ".csv");
            String[] strKnownInteractions = new String[]{
                "G1,G2,1",
                "G1,G3,1",
            };
            writeDataToCsv(tempFile, strKnownInteractions);

            Map<String, Float[]> inferredNetworks = new HashMap<>();
            inferredNetworks.put("G1;G2", new Float[]{0.9f, 0.5f, 0.0f, 0.2f, 0.6f});
            inferredNetworks.put("G1;G3", new Float[]{0.8f, 0.5f, 0.2f, 0.1f, 0.4f});

            SimplexMutationWithLocalSearch mutation = new SimplexMutationWithLocalSearch(0.0, 0.0, inferredNetworks, tempFile.getAbsolutePath(), "all", 1.0);
            result = mutation.execute(solution);

        } catch (IOException e) {
            e.printStackTrace();
        }

        assertArrayEquals(
            new double[]{0.25, 0.0833, 0.0833, 0.0833, 0.5},
            result.variables().stream().mapToDouble(Double::doubleValue).toArray(),
            0.001
        );
    }
}
