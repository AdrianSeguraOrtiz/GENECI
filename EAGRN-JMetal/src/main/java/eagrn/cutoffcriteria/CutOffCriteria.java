package eagrn.cutoffcriteria;

import java.util.Map;

public interface CutOffCriteria {
    public boolean[][] getNetwork (Map<String, Float> links);
    public Map<String, Float> getCutMap (Map<String, Float> links);
}
