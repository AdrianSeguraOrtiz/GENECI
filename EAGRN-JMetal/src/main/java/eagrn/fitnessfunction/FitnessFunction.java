package eagrn.fitnessfunction;

import java.util.Map;

public interface FitnessFunction {
    public double run(Map<String, Float> consensus, Double[] x);
}
