package eagrn;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.algorithm.multiobjective.smpso.SMPSOBuilder;
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
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.qualityindicator.impl.Epsilon;
import org.uma.jmetal.qualityindicator.impl.GenerationalDistance;
import org.uma.jmetal.qualityindicator.impl.InvertedGenerationalDistance;
import org.uma.jmetal.qualityindicator.impl.InvertedGenerationalDistancePlus;
import org.uma.jmetal.qualityindicator.impl.Spread;
import org.uma.jmetal.qualityindicator.impl.hypervolume.impl.PISAHypervolume;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.archive.BoundedArchive;
import org.uma.jmetal.util.archive.impl.CrowdingDistanceArchive;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.errorchecking.JMetalException;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.cutoffcriteria.impl.PercLinksWithBestConfCriteria;
import eagrn.operator.crossover.SimplexCrossover;
import eagrn.operator.mutation.SimplexMutation;

public class ComputingReferenceParetoFronts {
    private static final int INDEPENDENT_RUNS = 25;

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

        String strFitnessFormulas = "Quality;DegreeDistribution";
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
                new ExperimentBuilder<DoubleSolution, List<DoubleSolution>>("GRN-ComputingReferenceParetoFronts-D3-100")
                        .setAlgorithmList(algorithmList)
                        .setProblemList(problemList)
                        .setExperimentBaseDirectory(experimentBaseDirectory)
                        .setOutputParetoFrontFileName("FUN")
                        .setOutputParetoSetFileName("VAR")
                        .setReferenceFrontDirectory(experimentBaseDirectory + "/GRN-ComputingReferenceParetoFronts-D3-100/referenceFronts")
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
        int populationSize = 100;
        int numEvaluations = 100000;

        for (int run = 0; run < INDEPENDENT_RUNS; run++) {
            for (ExperimentProblem<DoubleSolution> experimentProblem : problemList) {
                Algorithm<List<DoubleSolution>> algorithm 
                    = new NSGAIIBuilder<>(experimentProblem.getProblem(), 
                                        new SimplexCrossover(3, 1, 0.9), 
                                        new SimplexMutation(0.1, 0.1), 
                                        populationSize)
                        .setSelectionOperator(new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>()))
                        .setMaxEvaluations(numEvaluations)
                        .build();
                algorithms.add(new ExperimentAlgorithm<>(algorithm, "NSGAII", experimentProblem, run));
            }

            for (ExperimentProblem<DoubleSolution> experimentProblem : problemList) {
                BoundedArchive<DoubleSolution> archive = new CrowdingDistanceArchive<>(populationSize);
                Algorithm<List<DoubleSolution>> algorithm 
                    = new SMPSOBuilder((DoubleProblem) experimentProblem.getProblem(), archive)
                        .setMutation(new SimplexMutation(0.1, 0.1))
                        .setMaxIterations(numEvaluations / populationSize)
                        .setSwarmSize(populationSize)
                        .setSolutionListEvaluator(new SequentialSolutionListEvaluator<DoubleSolution>())
                        .build();
                algorithms.add(new ExperimentAlgorithm<>(algorithm, "SMPSO", experimentProblem, run));
            }
        }
        return algorithms;
    }
}
