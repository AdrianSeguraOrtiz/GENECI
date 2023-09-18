package eagrn.cutoffcriteria.impl;

import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class PercLinksWithBestConfCriteriaTest {

    @Test
    void shouldReturnNetworkCaseA() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 0.2f);
        links.put("A;C", 0.6f);
        links.put("B;C", 0.4f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        PercLinksWithBestConfCriteria percLinksWithBestConfCriteria = new PercLinksWithBestConfCriteria(0.4f, geneNames);
        boolean[][] matrix = percLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, false, true}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, true}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = percLinksWithBestConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("A;C", 0.6f);
        test.put("B;C", 0.4f);

        assertTrue(goodLinks.equals(test));
    }

    @Test
    void shouldReturnNetworkCaseB() {
        Map<String, Float> links = new HashMap<>();
        links.put("A;B", 0.8f);
        links.put("A;C", 0.2f);
        links.put("B;C", 0.0f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        PercLinksWithBestConfCriteria percLinksWithBestConfCriteria = new PercLinksWithBestConfCriteria(0.1f, geneNames);
        boolean[][] matrix = percLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = percLinksWithBestConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("A;B", 0.8f);

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

        PercLinksWithBestConfCriteria percLinksWithBestConfCriteria = new PercLinksWithBestConfCriteria(0.4f, geneNames);
        boolean[][] matrix = percLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, true}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false}, matrix[2]);

        Map<String, Float> goodLinks = percLinksWithBestConfCriteria.getCutMap(links);
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
        links.put("C;D", 0.9f);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");
        geneNames.add("D");

        PercLinksWithBestConfCriteria percLinksWithBestConfCriteria = new PercLinksWithBestConfCriteria(0.25f, geneNames);
        boolean[][] matrix = percLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new boolean[]{false, true, false, true}, matrix[0]);
        assertArrayEquals(new boolean[]{false, false, false, false}, matrix[1]);
        assertArrayEquals(new boolean[]{false, false, false, true}, matrix[2]);
        assertArrayEquals(new boolean[]{false, false, false, false}, matrix[3]);

        Map<String, Float> goodLinks = percLinksWithBestConfCriteria.getCutMap(links);
        Map<String, Float> test = new HashMap<>();
        test.put("C;D", 0.9f);
        test.put("A;D", 0.5f);
        test.put("A;B", 0.3f);

        assertTrue(goodLinks.equals(test));
    }

}