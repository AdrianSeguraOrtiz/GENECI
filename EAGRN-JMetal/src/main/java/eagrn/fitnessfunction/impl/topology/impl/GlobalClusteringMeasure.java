package eagrn.fitnessfunction.impl.topology.impl;

import java.util.Arrays;
import java.util.Map;

import org.ehcache.Cache;
import org.ehcache.CacheManager;
import org.ehcache.config.builders.CacheConfigurationBuilder;
import org.ehcache.config.builders.CacheManagerBuilder;
import org.ehcache.config.builders.ResourcePoolsBuilder;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.ClusteringCoefficient;
import org.jgrapht.graph.DefaultEdge;

import eagrn.cutoffcriteria.CutOffCriteria;
import eagrn.fitnessfunction.impl.topology.Topology;

public class GlobalClusteringMeasure extends Topology {
    private CutOffCriteria cutOffCriteria;
    private Cache<String, Double> cache;

    public GlobalClusteringMeasure(CutOffCriteria cutOffCriteria){
        this.cutOffCriteria = cutOffCriteria;
        CacheManager hybridCacheManager = CacheManagerBuilder.newCacheManagerBuilder().build();
        hybridCacheManager.init();
        this.cache = hybridCacheManager.createCache("FitnessFunctionCache", CacheConfigurationBuilder.newCacheConfigurationBuilder(String.class, Double.class, ResourcePoolsBuilder.heap(1000)).build());
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) { 
        double score = 0.0;
        String key = Arrays.deepToString(cutOffCriteria.getBooleanMatrix(consensus));

        if (this.cache.containsKey(key)){
            score = this.cache.get(key);
        } else {
            Graph<Integer, DefaultEdge> graph = cutOffCriteria.getBooleanGraph(consensus, false);
            ClusteringCoefficient<Integer, DefaultEdge> evaluator = new ClusteringCoefficient<>(graph);
            score = -evaluator.getGlobalClusteringCoefficient();
            this.cache.put(key, score);
        }
        
        return score;
    }
}
