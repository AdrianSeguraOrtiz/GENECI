package eagrn.cutoffcriteria.impl;

import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public class NumLinksWithBestConfCriteriaTest {

    @Test
    void shouldReturnNetworkCaseA() {
        Map<String, Double> links = new HashMap<>();
        links.put("A;B", 0.2);
        links.put("A;C", 0.6);
        links.put("B;C", 0.4);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        NumLinksWithBestConfCriteria numLinksWithBestConfCriteria = new NumLinksWithBestConfCriteria(2, geneNames);
        int[][] matrix = numLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new int[]{0, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseB() {
        Map<String, Double> links = new HashMap<>();
        links.put("A;B", 0.8);
        links.put("A;C", 0.2);
        links.put("B;C", 0.0);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        NumLinksWithBestConfCriteria numLinksWithBestConfCriteria = new NumLinksWithBestConfCriteria(1, geneNames);
        int[][] matrix = numLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseC() {
        Map<String, Double> links = new HashMap<>();
        links.put("A;B", 1.0);
        links.put("A;C", 0.2);
        links.put("B;C", 0.6);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");

        NumLinksWithBestConfCriteria numLinksWithBestConfCriteria = new NumLinksWithBestConfCriteria(2, geneNames);
        int[][] matrix = numLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new int[]{0, 1, 0}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 1}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0}, matrix[2]);
    }

    @Test
    void shouldReturnNetworkCaseD() {
        Map<String, Double> links = new HashMap<>();
        links.put("A;B", 0.3);
        links.put("A;D", 0.5);
        links.put("B;C", 0.1);
        links.put("C;D", 0.9);

        ArrayList<String> geneNames = new ArrayList<>();
        geneNames.add("A");
        geneNames.add("B");
        geneNames.add("C");
        geneNames.add("D");

        NumLinksWithBestConfCriteria numLinksWithBestConfCriteria = new NumLinksWithBestConfCriteria(3, geneNames);
        int[][] matrix = numLinksWithBestConfCriteria.getNetwork(links);

        assertArrayEquals(new int[]{0, 1, 0, 1}, matrix[0]);
        assertArrayEquals(new int[]{0, 0, 0, 0}, matrix[1]);
        assertArrayEquals(new int[]{0, 0, 0, 1}, matrix[2]);
        assertArrayEquals(new int[]{0, 0, 0, 0}, matrix[3]);
    }

}