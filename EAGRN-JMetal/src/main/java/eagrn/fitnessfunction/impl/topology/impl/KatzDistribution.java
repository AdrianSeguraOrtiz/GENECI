package eagrn.fitnessfunction.impl.topology.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.ehcache.Cache;
import org.ehcache.CacheManager;
import org.ehcache.config.builders.CacheConfigurationBuilder;
import org.ehcache.config.builders.CacheManagerBuilder;
import org.ehcache.config.builders.ResourcePoolsBuilder;
import org.apache.commons.lang.ArrayUtils;
import org.jgrapht.Graph;
import org.jgrapht.alg.scoring.KatzCentrality;
import org.jgrapht.graph.DefaultWeightedEdge;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.impl.topology.Topology;

public class KatzDistribution extends Topology {
    private Cache<String, Double> cache;
    private int decimals;
    private Map<String, Integer> geneIndexMap;

    public KatzDistribution(ArrayList<String> geneNames){
        CacheManager hybridCacheManager = CacheManagerBuilder.newCacheManagerBuilder().build();
        hybridCacheManager.init();
        this.cache = hybridCacheManager.createCache("FitnessFunctionCache", CacheConfigurationBuilder.newCacheConfigurationBuilder(String.class, Double.class, ResourcePoolsBuilder.heap(1000)).build());
        this.decimals = Math.max(1, 4 - (int) Math.log10(geneNames.size()));
        this.geneIndexMap = new HashMap<>();
        for (int i = 0; i < geneNames.size(); i++) {
            this.geneIndexMap.put(geneNames.get(i), i);
        }
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        double score = 0.0;
        String key = StaticUtils.getConsensusRoundedString(consensus, decimals);

        if (this.cache.containsKey(key)){
            score = this.cache.get(key);
        } else {
            Graph<Integer, DefaultWeightedEdge> graph = StaticUtils.getWeightedGraph(consensus, geneIndexMap, decimals, true);
            KatzCentrality<Integer, DefaultWeightedEdge> evaluator = new KatzCentrality<>(graph);
            Double[] scores = evaluator.getScores().values().toArray(new Double[0]);
            for (int i = 0; i < scores.length; i++) {
                scores[i] += 1;
            }
            score = super.paretoTest(ArrayUtils.toPrimitive(scores));
            this.cache.put(key, score);
        }

        return score;
    }
    
}
