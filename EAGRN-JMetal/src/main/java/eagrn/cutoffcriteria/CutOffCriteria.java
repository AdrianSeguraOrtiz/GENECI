package eagrn.cutoffcriteria;

import eagrn.ConsensusTuple;

import java.util.ArrayList;
import java.util.Map;

public interface CutOffCriteria {
    public int[][] getNetworkFromConsensus (Map<String, ConsensusTuple> consensus, ArrayList<String> geneNames);
}
