package eagrn;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.lab.experiment.Experiment;
import org.uma.jmetal.lab.experiment.ExperimentBuilder;
import org.uma.jmetal.lab.experiment.component.impl.ComputeQualityIndicators;
import org.uma.jmetal.lab.experiment.component.impl.ExecuteAlgorithms;
import org.uma.jmetal.lab.experiment.component.impl.GenerateBoxplotsWithR;
import org.uma.jmetal.lab.experiment.component.impl.GenerateFriedmanHolmTestTables;
import org.uma.jmetal.lab.experiment.component.impl.GenerateHtmlPages;
import org.uma.jmetal.lab.experiment.component.impl.GenerateLatexTablesWithStatistics;
import org.uma.jmetal.lab.experiment.component.impl.GenerateReferenceParetoSetAndFrontFromDoubleSolutions;
import org.uma.jmetal.lab.experiment.component.impl.GenerateWilcoxonTestTablesWithR;
import org.uma.jmetal.lab.experiment.util.ExperimentAlgorithm;
import org.uma.jmetal.lab.experiment.util.ExperimentProblem;
import org.uma.jmetal.operator.selection.impl.BinaryTournamentSelection;
import org.uma.jmetal.qualityindicator.impl.Epsilon;
import org.uma.jmetal.qualityindicator.impl.GenerationalDistance;
import org.uma.jmetal.qualityindicator.impl.InvertedGenerationalDistance;
import org.uma.jmetal.qualityindicator.impl.InvertedGenerationalDistancePlus;
import org.uma.jmetal.qualityindicator.impl.Spread;
import org.uma.jmetal.qualityindicator.impl.hypervolume.impl.PISAHypervolume;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.cutoffcriteria.impl.PercLinksWithBestConfCriteria;
import eagrn.operator.crossover.SimplexCrossover;
import eagrn.operator.mutation.SimplexMutation;

public class ComputingReferenceParetoFronts {
    private static final int INDEPENDENT_RUNS = 5;

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            throw new JMetalException("It is necessary to specify at least one problem folder");
        }
        String[] networkFolders = args;
        String experimentBaseDirectory = "./pareto_fronts";

        File[][] files = new File[networkFolders.length][];
        for (int i = 0; i < networkFolders.length; i++) {
            files[i] = StaticUtils.getCSVFilesFromDirectory(networkFolders[i] + "/lists/");
        }

        ArrayList<String>[] geneNames = new ArrayList[networkFolders.length];
        for (int i = 0; i < networkFolders.length; i++) {
            geneNames[i] = StaticUtils.getGeneNames(networkFolders[i] + "/gene_names.txt");
        }

        String strFitnessFormulas = "Quality;DegreeDistribution;Motifs";
        String strTimeSeriesFile = null;

        List<ExperimentProblem<DoubleSolution>> problemList = new ArrayList<>();
        for (int i = 0; i < networkFolders.length; i++) {
            Map<String, Float[]> inferredNetworks = StaticUtils.readAllInferredNetworkFiles(files[i]);
            CutOffCriteria cutOffCriteria = new PercLinksWithBestConfCriteria(0.4f, geneNames[i]);
            GRNProblem problem = new GRNProblem(inferredNetworks, geneNames[i], cutOffCriteria, strFitnessFormulas, strTimeSeriesFile);
            problem.setName(new File(networkFolders[i]).getName());
            problemList.add(new ExperimentProblem<>(problem));
        }

        List<ExperimentAlgorithm<DoubleSolution, List<DoubleSolution>>> algorithmList =
            configureAlgorithmList(problemList);

        Experiment<DoubleSolution, List<DoubleSolution>> experiment =
                new ExperimentBuilder<DoubleSolution, List<DoubleSolution>>("GRN-ComputingReferenceParetoFronts_0-500")
                        .setAlgorithmList(algorithmList)
                        .setProblemList(problemList)
                        .setExperimentBaseDirectory(experimentBaseDirectory)
                        .setOutputParetoFrontFileName("FUN")
                        .setOutputParetoSetFileName("VAR")
                        .setReferenceFrontDirectory(experimentBaseDirectory + "/GRN-ComputingReferenceParetoFronts_0-500/referenceFronts")
                        .setIndicatorList(Arrays.asList(
                                new Epsilon(),
                                new Spread(),
                                new GenerationalDistance(),
                                new PISAHypervolume(),
                                new InvertedGenerationalDistance(),
                                new InvertedGenerationalDistancePlus()))
                        .setIndependentRuns(INDEPENDENT_RUNS)
                        .setNumberOfCores(Runtime.getRuntime().availableProcessors())
                        .build();

        new ExecuteAlgorithms<>(experiment).run();
        new GenerateReferenceParetoSetAndFrontFromDoubleSolutions(experiment).run();
        new ComputeQualityIndicators<>(experiment).run();
        new GenerateLatexTablesWithStatistics(experiment).run();
        new GenerateFriedmanHolmTestTables<>(experiment).run();
        new GenerateWilcoxonTestTablesWithR<>(experiment).run();
        new GenerateBoxplotsWithR<>(experiment).setRows(3).setColumns(2).run();
        new GenerateHtmlPages<>(experiment).run() ;
    }

    static List<ExperimentAlgorithm<DoubleSolution, List<DoubleSolution>>> configureAlgorithmList(
          List<ExperimentProblem<DoubleSolution>> problemList) {

        List<ExperimentAlgorithm<DoubleSolution, List<DoubleSolution>>> algorithms = new ArrayList<>();
        int numEvaluations = 100000;

        for (int run = 0; run < INDEPENDENT_RUNS; run++) {

            // NSGAII
            double[] crossoverProbabilities = new double[]{0.7, 0.8, 0.9};
            double[] mutationProbabilities = new double[]{0.05, 0.1, 0.2};
            double[] mutationStrength = new double[]{0.1, 0.2, 0.3};
            int[] populationSizes = new int[]{100, 200, 300};
            int[] numParents = new int[]{3, 4};
            for(double cp : crossoverProbabilities){
                for(double mp : mutationProbabilities){
                    for(double ms : mutationStrength){
                        for(int ps : populationSizes) {
                            for (int np : numParents) {
                                for (ExperimentProblem<DoubleSolution> experimentProblem : problemList) {
                                    Algorithm<List<DoubleSolution>> algorithm 
                                        = new NSGAIIBuilder<>(experimentProblem.getProblem(), 
                                                            new SimplexCrossover(np, 1, cp), 
                                                            new SimplexMutation(mp, ms), 
                                                            ps)
                                            .setSelectionOperator(new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>()))
                                            .setMaxEvaluations(numEvaluations)
                                            .build();
                                    String tag = String.valueOf(ps);
                                    //if (ps == 102) tag = "100";
                                    //else if (ps == 201) tag = "200";
                                    algorithms.add(new ExperimentAlgorithm<>(algorithm, "NSGAII-PS" + tag + "-CP" + cp + "-MP" + mp + "-NP" + np + "-MS" + ms, experimentProblem, run));
                                }
                            }
                        }
                }
                }
            }

        }
        return algorithms;
    }
}
