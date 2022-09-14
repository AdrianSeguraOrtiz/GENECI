package eagrn;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.uma.jmetal.lab.experiment.util.ExperimentProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.errorchecking.JMetalException;

public class ComputingReferenceParetoFronts {
    private static final int INDEPENDENT_RUNS = 25;

    public static void main(String[] args) throws IOException {
        if (args.length != 1) {
            throw new JMetalException("Needed arguments: experimentBaseDirectory");
        }
        String experimentBaseDirectory = args[0];

        List<ExperimentProblem<DoubleSolution>> problemList = new ArrayList<>();
    }
}
