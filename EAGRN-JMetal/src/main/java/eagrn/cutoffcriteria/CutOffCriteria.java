package eagrn.cutoffcriteria;

import java.util.Map;

public interface CutOffCriteria {
    public int[][] getNetwork (Map<String, Double> links);
    public Map<String, Double> getCutMap (Map<String, Double> links);
}
