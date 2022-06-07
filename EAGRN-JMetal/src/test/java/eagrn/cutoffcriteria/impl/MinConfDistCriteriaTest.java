package eagrn.cutoffcriteria.impl;

import eagrn.ConsensusTuple;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class MinConfDistCriteriaTest {

    @Test
    void shouldReturnNetworkFromConsensusCaseA() {
        MinConfDistCriteria minConfDistCriteria = new MinConfDistCriteria(0.5);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(0.6, 0.2));
        links.put("A-C", new ConsensusTuple(0.8, 0.9));
        links.put("B-C", new ConsensusTuple(0.9, 0.4));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfDistCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkFromConsensusCaseB() {
        MinConfDistCriteria minConfDistCriteria = new MinConfDistCriteria(0.6);

        Map<String, ConsensusTuple> links = new HashMap<>();
        links.put("A-B", new ConsensusTuple(0.6, 0.9));
        links.put("A-C", new ConsensusTuple(0.9, 0.1));
        links.put("B-C", new ConsensusTuple(0.7, 0.8));

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        int[][] matrix = minConfDistCriteria.getNetworkFromConsensus(links, geneNames);

        assertArrayEquals(new int[]{0, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

}