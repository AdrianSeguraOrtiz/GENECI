package eagrn.algorithm.impl;

import org.uma.jmetal.algorithm.multiobjective.smpso.SMPSOBuilder;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.archive.BoundedArchive;

public class SMPSOCorrectMutationBuilder extends SMPSOBuilder {
    public SMPSOCorrectMutationBuilder(DoubleProblem problem, BoundedArchive<DoubleSolution> leaders) {
        super(problem, leaders);
    }

    @Override
    public SMPSOCorrectMutation build() {
        return new SMPSOCorrectMutation(super.getProblem(), super.getSwarmSize(), super.getLeaders(), 
            super.getMutation(), super.getMaxIterations(), super.getR1Min(), super.getR1Max(),
            super.getR2Min(), super.getR2Max(), super.getC1Min(), super.getC1Max(), super.getC2Min(), 
            super.getC2Max(), super.getWeightMin(), super.getWeightMax(), super.getChangeVelocity1(),
            super.getChangeVelocity2(), super.getEvaluator());
    }
}
