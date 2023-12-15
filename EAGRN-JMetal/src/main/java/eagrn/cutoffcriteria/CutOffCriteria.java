package eagrn.cutoffcriteria;

import java.util.Map;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;

public interface CutOffCriteria {
    public boolean[][] getBooleanMatrix (Map<String, Float> links);
    public Graph<Integer, DefaultEdge> getBooleanGraph (Map<String, Float> links, boolean directed);
    public Map<String, Float> getCutMap (Map<String, Float> links);
}
