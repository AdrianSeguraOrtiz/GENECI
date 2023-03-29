package eagrn.cutoffcriteria.impl;

import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class MinConfCriteriaTest {

    @Test
    void shouldReturnNetworkCaseA() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 0.0f);
        links.put("A;C", 0.0f);
        links.put("B;C", 0.0f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        MinConfCriteria minConfCriteria = new MinConfCriteria(1f, geneNames);
        boolean[][] matrix = minConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, false, false}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = minConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();

        assertTrue(goodLinks.equals(test));
    }

    @Test
    void shouldReturnNetworkCaseB() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 0.6f);
        links.put("A;C", 0.4f);
        links.put("B;C", 0.0f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        MinConfCriteria minConfCriteria = new MinConfCriteria(0.5f, geneNames);
        boolean[][] matrix = minConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = minConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("A;B", 0.6f);

        assertTrue(goodLinks.equals(test));
    }

    @Test
    void shouldReturnNetworkCaseC() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 1.0f);
        links.put("A;C", 0.2f);
        links.put("B;C", 0.6f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        MinConfCriteria minConfCriteria = new MinConfCriteria(0.5f, geneNames);
        boolean[][] matrix = minConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, true}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = minConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("A;B", 1.0f);
        test.put("B;C", 0.6f);

        assertTrue(goodLinks.equals(test));
    }

    @Test
    void shouldReturnNetworkCaseD() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 0.3f);
        links.put("A;D", 0.5f);
        links.put("B;C", 0.1f);
        links.put("C;D", 0.1f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");
        geneNames.add("D");

        MinConfCriteria minConfCriteria = new MinConfCriteria(0.2f, geneNames);
        boolean[][] matrix = minConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false, true}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, false, false}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false, false}, matrix[2]);
        assertArrayEquals(new boolean[]{false, false, false, false}, matrix[3]);

        Map<String, Float> goodLinks = minConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("A;B", 0.3f);
        test.put("A;D", 0.5f);

        assertTrue(goodLinks.equals(test));
    }

}