import org.uma.jmetal.solution.doublesolution.DoubleSolution;

public class WeightRepairer {

    /** RepairSolution() method */
    public void repairSolution(DoubleSolution solution) {
        double v, sum = 0;

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            sum += v;
        }

        for (int i = 0; i < solution.variables().size(); i++) {
            v = solution.variables().get(i);
            v = Math.round(v/sum * 10000.0) / 10000.0;
            solution.variables().set(i, v);
        }
    }
}
