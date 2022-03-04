package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class MaxNumLinksBestConfCriteriaTest {

    @Test
    void shouldReturnNetworkFromConsensus() {
        MaxNumLinksBestConfCriteria maxNumLinksBestConfCriteria = new MaxNumLinksBestConfCriteria(2);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(1, 0.2));
        links.put("A-C", new ConsensusTuple(1, 0.6));
        links.put("B-C", new ConsensusTuple(1, 0.4));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = maxNumLinksBestConfCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{1, 1, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseA() {
        MaxNumLinksBestConfCriteria maxNumLinksBestConfCriteria = new MaxNumLinksBestConfCriteria(1);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 0.8);
        links.put("A-C", 0.2);
        links.put("B-C", 0.0);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = maxNumLinksBestConfCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{1, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseB() {
        MaxNumLinksBestConfCriteria maxNumLinksBestConfCriteria = new MaxNumLinksBestConfCriteria(2);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 1.0);
        links.put("A-C", 0.2);
        links.put("B-C", 0.6);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = maxNumLinksBestConfCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{1, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 1, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseC() {
        MaxNumLinksBestConfCriteria maxNumLinksBestConfCriteria = new MaxNumLinksBestConfCriteria(3);

        Map<String, Double> links = new HashMap<>();
        links.put("A-B", 0.3);
        links.put("A-D", 0.5);
        links.put("B-C", 0.1);
        links.put("C-D", 0.9);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");
        geneNames.add("D");

        int[][] matrix = maxNumLinksBestConfCriteria.getNetwork(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{1, 0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0, 1}, matrix[2]);
        assertArrayEquals(new int[]{1, 0, 1, 0}, matrix[3]);
    }

}