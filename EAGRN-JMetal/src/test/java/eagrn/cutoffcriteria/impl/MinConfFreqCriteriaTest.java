package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class MinConfFreqCriteriaTest {

    @Test
    void shouldReturnNetworkFromConsensusCaseA() {
        MinConfFreqCriteria minConfFreqCriteria = new MinConfFreqCriteria(0.5, 4);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(2, 0.6));
        links.put("A-C", new ConsensusTuple(3, 0.1));
        links.put("B-C", new ConsensusTuple(1, 0.8));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfFreqCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{1, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 1, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkFromConsensusCaseB() {
        MinConfFreqCriteria minConfFreqCriteria = new MinConfFreqCriteria(0.6, 10);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(2, 0.9));
        links.put("A-C", new ConsensusTuple(7, 0.6));
        links.put("B-C", new ConsensusTuple(4, 0.3));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfFreqCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{1, 0, 0}, matrix[2]);
    }

}