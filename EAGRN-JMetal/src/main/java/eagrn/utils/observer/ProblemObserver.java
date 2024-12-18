package eagrn.utils.observer;

import java.util.ArrayList;
import java.util.Map;

import org.uma.jmetal.solution.doublesolution.DoubleSolution;

import eagrn.GRNProblem;
import eagrn.cutoffcriteria.CutOffCriteria;

/**
 * The ProblemObserver class extends the Problem class to incorporate observer functionality.
 * This class is designed to observe the evolution of solutions in a genetic algorithm or any optimization problem.
 * It allows for registration of observer instances that can perform actions (e.g., logging or writing to a file) when a solution is evaluated.
 */
public class ProblemObserver extends GRNProblem {
    // Array of observer instances to be notified upon solution evaluation
    protected ObserverInterface[] observers;

    /**
     * Defines the contract for observer instances that wish to be notified about solution evaluations.
     */
    public interface ObserverInterface {
        // Method to register a solution evaluation event
        void register(DoubleSolution result);
        // Method to write information to a file
        void writeToFile(String strFile);
    }

    public ProblemObserver(Map<String, Float[]> inferredNetworks, ArrayList<String> geneNames, CutOffCriteria cutOffCriteria, String strFitnessFormulas, String strTimeSeriesFile, ObserverInterface[] observers) {

        super(inferredNetworks, geneNames, cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
        this.observers = observers;
    }

    /**
     * Overrides the evaluate method from the Problem class to include observer notification logic.
     * @param solution The DoubleSolution instance to be evaluated.
     * @return DoubleSolution The evaluated solution instance, after observer notification.
     */
    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {
        // Call the super class's evaluate method to perform the actual evaluation
        DoubleSolution result = super.evaluate(solution);
        // Notify all registered observers with the evaluation result
        for (ObserverInterface observer : observers) {
            observer.register(result);
        }
        // Return the evaluated solution
        return result;
    }
}
