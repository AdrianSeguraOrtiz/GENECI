package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class MinConfidenceCriteriaTest {

    @Test
    void shouldReturnNetworkFromConsensus() {
        MinConfidenceCriteria minConfidenceCriteria = new MinConfidenceCriteria(0.5);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(1, 0.6));
        links.put("A-C", new ConsensusTuple(1, 0.4));
        links.put("B-C", new ConsensusTuple(1, 0.0));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfidenceCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseA() {
        MinConfidenceCriteria minConfidenceCriteria = new MinConfidenceCriteria(1.0);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 0.0);
        links.put("A-C", 0.0);
        links.put("B-C", 0.0);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfidenceCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 0, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseB() {
        MinConfidenceCriteria minConfidenceCriteria = new MinConfidenceCriteria(0.5);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 1.0);
        links.put("A-C", 0.2);
        links.put("B-C", 0.6);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfidenceCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseC() {
        MinConfidenceCriteria minConfidenceCriteria = new MinConfidenceCriteria(0.2);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 0.3);
        links.put("A-D", 0.5);
        links.put("B-C", 0.1);
        links.put("C-D", 0.1);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");
        geneNames.add("D");

        int[][] matrix = minConfidenceCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0, 0}, matrix[2]);
        assertArrayEquals(new int[]{0, 0, 0, 0}, matrix[3]);
    }

}