package eagrn.cutoffcriteria;

import eagrn.ConsensusTuple;

import java.util.ArrayList;
import java.util.Map;

public interface CutOffCriteria {
    public int[][] getNetworkFromConsensusList (Map<String, ConsensusTuple> consensus, ArrayList<String> geneNames);
    public int[][] getNetworkFromList (Map<String, Double> map, ArrayList<String> geneNames);
}
