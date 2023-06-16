# Parameterization

To enhance the performance of our algorithm, we have undertaken a parameterization exercise aimed at selecting the optimal combination of values for the following parameters:

* `--population-size`: 100, 200, 300
* `--crossover-probability`: 0.7, 0.8, 0.9
* `--num-parents`: 3, 4
* `--mutation-probability`: 0.05, 0.1, 0.2
* `--mutation-strength`: 0.1, 0.2, 0.3

To accomplish this, we conducted a comprehensive analysis using GENECI on a dataset comprising networks with fewer than 1000 genes. For each case, we performed five independent runs. The cutoff criterion employed was *PercLinksWithBestConf* with a value set at 0.4. Additionally, we selected three fitness functions: *Quality*, *DegreeDistribution*, and *Motifs*.

Once all the results have been obtained, a reference front has been built for each problem, taking the best solutions of each combination. After that, the reference front is compared with each independent result and the following metrics are calculated: Epsilon (EP), Generational Distance (GD), PISAHypervolume (HV), Inverted Generational Distance (IGD), Inverted Generational Distance Plus (IGD+) and Spread (SP)

## Epsilon (EP)

The Epsilon metric evaluates the convergence of an approximate solution set to the true Pareto front. It calculates the minimum distance between each approximate solution and the true Pareto front, and then compares these distances with a reference value called Epsilon. A low Epsilon value indicates good convergence of the algorithm to the true Pareto front.


## Generational Distance (GD)

This metric calculates the average distance between each approximate solution and the true Pareto front. It provides a measure of how close the solutions are to the optimal Pareto front. A low Generational Distance value indicates a better approximation to the true Pareto front.

## PISAHypervolume (HV)

The PISA Hypervolume is a metric that evaluates the quality of an approximate solution set in terms of the region of the objective space it covers. The higher the hypervolume, the better the quality of the solutions. This metric considers both convergence to the Pareto front and diversity of the solutions.

## Inverted Generational Distance (IGD) 

It is a metric that measures the average distance between each solution from the true Pareto front and its nearest neighbor in the approximate set. A low IGD score indicates that the approximate solutions are close to the true Pareto front and, therefore, have better quality.

## Inverted Generational Distance Plus (IGD+) 

It is a variant of the IGD metric that also takes into account the spatial distribution of the approximate solutions. It calculates both the average distance and the density of solutions on the Pareto front. IGD+ penalizes solutions that are very close to each other, thereby promoting better dispersion of solutions along the Pareto front.

## Spread (SP)

The Spread metric measures the diversity of solutions in the approximate Pareto front. It assesses how well the solutions are distributed along the Pareto front and provides a measure of spatial dispersion. A high Spread value indicates better diversity and wider coverage of the Pareto front.