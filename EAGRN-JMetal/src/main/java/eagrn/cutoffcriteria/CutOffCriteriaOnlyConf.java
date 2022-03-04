package eagrn.cutoffcriteria;

import java.util.ArrayList;
import java.util.Map;

public interface CutOffCriteriaOnlyConf extends CutOffCriteria {
    public int[][] getNetwork (Map<String, Double> map, ArrayList<String> geneNames);
}
