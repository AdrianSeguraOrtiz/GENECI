package eagrn.fitnessfunctions;

import java.util.Map;

public interface FitnessFunction {
    public double run(Map<String, Double> consensus, Double[] x);
}
