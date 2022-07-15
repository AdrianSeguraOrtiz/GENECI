package eagrn.fitnessfunctions;

import java.util.Map;

import eagrn.ConsensusTuple;

public interface FitnessFunction {
    public double run(Map<String, ConsensusTuple> consensus);
}
