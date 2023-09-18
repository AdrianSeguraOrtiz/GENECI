package eagrn.operator.crossover;

import java.util.ArrayList;
import java.util.List;

import org.uma.jmetal.operator.crossover.CrossoverOperator;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.Check;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

public class SimplexCrossover implements CrossoverOperator<DoubleSolution> {
    private int numberOfParents;
	private int numberOfOffspring;
	private double epsilon;
    private double crossoverProbability;
    private JMetalRandom random;

    public SimplexCrossover(int numberOfParents, int numberOfOffspring, double crossoverProbability) {
        this(numberOfParents, numberOfOffspring, crossoverProbability, Math.sqrt(numberOfParents + 1));
    }

    public SimplexCrossover(int numberOfParents, int numberOfOffspring, double crossoverProbability, double epsilon) {
        this.numberOfParents = numberOfParents;
		this.numberOfOffspring = numberOfOffspring;
		this.epsilon = epsilon;
        this.crossoverProbability = crossoverProbability;
        this.random = JMetalRandom.getInstance();
    }

    @Override
    public List<DoubleSolution> execute(List<DoubleSolution> source) {
        Check.that(
        getNumberOfRequiredParents() == source.size(),
        "Simplex Crossover requires "
            + getNumberOfRequiredParents()
            + " parents, but got "
            + source.size());

        List<DoubleSolution> offspring = new ArrayList<>();
        if (random.nextDouble(0, 1) <= this.crossoverProbability) {
            int n = source.size();
            int m = source.get(0).variables().size();

            double[] G = new double[m]; // center of mass
            double[][] x = new double[n][m]; // expanded simplex vertices
            double[] r = new double[n - 1]; // random numbers
            double[][] C = new double[n][m]; // random offset vectors

            // compute center of mass
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < m; j++) {
                    G[j] += source.get(i).variables().get(j);
                }
            }

            for (int j = 0; j < m; j++) {
                G[j] /= n;
            }

            // compute simplex vertices expanded by epsilon
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < m; j++) {
                    x[i][j] = G[j]
                            + epsilon
                            * (source.get(i).variables().get(j) - G[j]);
                }
            }

            // generate offspring
            for (int k = 0; k < numberOfOffspring; k++) {
                DoubleSolution child = (DoubleSolution) source.get(n - 1).copy();

                for (int i = 0; i < n - 1; i++) {
                    r[i] = Math.pow(random.nextDouble(), 1.0 / (i + 1.0));
                }

                for (int i = 0; i < n; i++) {
                    for (int j = 0; j < m; j++) {
                        if (i == 0) {
                            C[i][j] = 0;
                        } else {
                            C[i][j] = r[i - 1]
                                    * (x[i - 1][j] - x[i][j] + C[i - 1][j]);
                        }
                    }
                }

                for (int j = 0; j < m; j++) {
                    double value = x[n - 1][j] + C[n - 1][j];

                    if (value < child.getBounds(j).getLowerBound() || value > child.getBounds(j).getUpperBound()) {
                        return execute(source);
                    }

                    child.variables().set(j, value);
                }

                offspring.add(child);
            }
        } else {
            for (int k = 0; k < numberOfOffspring; k++) {
                offspring.add((DoubleSolution) source.get(k).copy());
            }
        }

		return offspring;
    }

    @Override
    public double getCrossoverProbability() {
        return this.crossoverProbability;
    }

    @Override
    public int getNumberOfRequiredParents() {
        return this.numberOfParents;
    }

    @Override
    public int getNumberOfGeneratedChildren() {
        return this.numberOfOffspring;
    }
    
}
