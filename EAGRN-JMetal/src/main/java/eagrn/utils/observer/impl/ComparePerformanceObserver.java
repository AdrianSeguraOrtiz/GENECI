package eagrn.utils.observer.impl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

import eagrn.utils.observer.ProblemObserver.ObserverInterface;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

public class ComparePerformanceObserver implements ObserverInterface {
    private int populationSize;
    private AtomicInteger parallelCount;
    private double[][] referenceFront;
    private CopyOnWriteArrayList<Integer> nonDominatedSols;
    private int numReferenceSolutions;
    private List<Double> percentageDomPoints;

    public ComparePerformanceObserver(int populationSize, File referenceFront, String referencePoint) {
        this.populationSize = populationSize;
        try {
            this.referenceFront = readFront(referenceFront);
        } catch (IOException e) {
            e.printStackTrace();
        }
        nonDominatedSols = new CopyOnWriteArrayList<>();
        for (int i = 0; i < this.referenceFront.length; i++) {
            nonDominatedSols.add(i);
        }

        if (!(referencePoint.equals("") || referencePoint.equals("-"))) {
            double[] refPoint = Arrays.stream(referencePoint.split(";")).mapToDouble(Double::parseDouble).toArray();

            for (int i = 0; i < this.referenceFront.length; i++) {
                for (int j = 0; j < this.referenceFront[i].length; j++) {
                    if (this.referenceFront[i][j] > refPoint[j]) {
                        nonDominatedSols.remove((Integer) i);
                        break;
                    }
                }
            }
        }
        this.numReferenceSolutions = nonDominatedSols.size();
        this.percentageDomPoints = new ArrayList<>();
        this.parallelCount = new AtomicInteger();
    }

    private double[][] readFront(File referenceFront) throws IOException {
        List<double[]> front = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(referenceFront))) {
            String line = br.readLine(); // Read and ignore the header
            while ((line = br.readLine()) != null) {
                // Split the line by commas and parse as doubles
                String[] tokens = line.split(",");
                double[] point = Arrays.stream(tokens).mapToDouble(Double::parseDouble).toArray();
                front.add(point);
            }
        }

        return front.toArray(new double[0][]);
    }

    @Override
    public void register(DoubleSolution result) {
        double[] objectives = result.objectives();

        nonDominatedSols.removeIf(i -> {
            boolean dominates = true;

            // Comparar cada objetivo
            for (int j = 0; j < objectives.length; j++) {
                if (objectives[j] > referenceFront[i][j]) {
                    dominates = false;
                    break;
                }
            }
            return dominates; // Eliminar si la solución actual domina al punto del frente
        });

        int cnt = this.parallelCount.incrementAndGet();
        if (cnt % this.populationSize == 0) {
            synchronized (this.percentageDomPoints) {
                this.percentageDomPoints.add(
                    (double) (this.numReferenceSolutions - nonDominatedSols.size()) * 100 / this.numReferenceSolutions
                );
            }
        }
    }

    @Override
    public void writeToFile(String strFile) {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(strFile))) {
            String strVector = this.percentageDomPoints.toString();
            bw.write(strVector.substring(1, strVector.length() - 1) + "\n");
        } catch (IOException ioe) {
            throw new RuntimeException(ioe);
        }
    }
}