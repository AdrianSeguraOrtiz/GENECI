package eagrn.utils.observer.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.BufferedWriter;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import com.google.common.util.concurrent.AtomicDoubleArray;
import eagrn.utils.observer.ProblemObserver.ObserverInterface;


/**
 * Implements ObserverInterface to observe and track the fitness evolution
 * across generations in a genetic algorithm. It monitors the fitness
 * improvements of solutions and records the average fitness values found 
 * for each objective over time.
 */
public class FitnessEvolutionAvgObserver implements ObserverInterface {
    // Size of the population.
    private int populationSize;
    // Number of objectives to be optimized.
    private int numObjectives;
    // Stores the sum of the fitness values found for each objective so far.
    private AtomicDoubleArray progressiveValues;
    // Lists to track the average fitness values for each generation and objective.
    private ArrayList<Double>[] generationFitness;
    // Counter to keep track of the number of evaluations, used to identify when a generation ends.
    private AtomicInteger parallelCount;

    /**
     * Constructor for the FitnessEvolutionAvgObserver.
     * Initializes the observer with the given population size and number of objectives.
     * Sets up tracking structures for the evolution of fitness values.
     *
     * @param populationSize The size of the population in the genetic algorithm.
     * @param numObjectives The number of objectives being optimized.
     */
    @SuppressWarnings("unchecked")
    public FitnessEvolutionAvgObserver(int populationSize, int numObjectives) {
        this.populationSize = populationSize;
        this.numObjectives = numObjectives;
        this.progressiveValues = new AtomicDoubleArray(numObjectives);
        this.generationFitness = new ArrayList[numObjectives];
        this.parallelCount = new AtomicInteger();

        // Initialize arrays to track fitness evolution.
        for (int i = 0; i < numObjectives; i++) {
            this.progressiveValues.set(i, 0.0);
            this.generationFitness[i] = new ArrayList<>();
        }
    }

    /**
     * Registers a solution's fitness values and updates the tracking of fitness evolution.
     *
     * @param result The solution to be registered and evaluated.
     */
    public void register(DoubleSolution result){
        // Increment the evaluation count and update average fitness values if necessary.
        int cnt = this.parallelCount.incrementAndGet();
        for (int i = 0; i < this.numObjectives; i++) {
            this.progressiveValues.addAndGet(i, result.objectives()[i]);

            // Add the average fitness to the tracking list at the end of each generation.
            if (cnt % this.populationSize == 0) {
                this.generationFitness[i].add(this.progressiveValues.get(i)/this.populationSize);
                this.progressiveValues.set(i, 0.0);
            }
        }
    }

    /**
     * Writes the evolution of fitness values to a specified output text file.
     * Each line in the output file corresponds to a series of fitness values
     * for a particular individual or solution, with values separated by commas.
     *
     * @param strFile The path and name of the output file where fitness evolution data will be written.
     */
    public void writeToFile(String strFile) {
        try {
            // Create a File object representing the specified output file.
            File outputFile = new File(strFile);
            // Initialize a BufferedWriter to write text to the output file, wrapping a FileWriter for efficient writing.
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            // Iterate through each entry in the fitnessEvolution map.
            Map<String, Double[]> fitnessEvolution = getFitnessEvolution();
            for (Map.Entry<String, Double[]> entry : fitnessEvolution.entrySet()) {
                // Convert the array of Double fitness values to a string representation, removing the brackets.
                String strVector = Arrays.toString(entry.getValue());
                // Write the string representation of the fitness values array to the file, followed by a newline.
                bw.write(strVector.substring(1, strVector.length() - 1) + "\n");
            }

            // Flush any buffered content to the file.
            bw.flush();
            // Close the BufferedWriter to release system resources.
            bw.close();
        } catch (IOException ioe) {
            // In case of an IOException, wrap and rethrow it as a RuntimeException.
            throw new RuntimeException(ioe);
        }
    }

    /**
     * Returns the fitness evolution of each objective function over generations.
     *
     * @return A map with fitness function identifiers as keys and arrays of average fitness values over generations as values.
     */
    public Map<String, Double[]> getFitnessEvolution() {
        Map<String, Double[]> fitnessEvolution = new HashMap<>();
        for (int i = 0; i < this.numObjectives; i++) {
            fitnessEvolution.put("F" + i, this.generationFitness[i].toArray(new Double[0]));
        }
        return fitnessEvolution;
    }
}
