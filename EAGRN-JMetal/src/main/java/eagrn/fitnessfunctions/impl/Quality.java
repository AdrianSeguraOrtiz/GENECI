package eagrn.fitnessfunctions.impl;

import java.util.Map;

import eagrn.ConsensusTuple;
import eagrn.fitnessfunctions.FitnessFunction;

/**
 * Try to minimize the quantity of high quality links (getting as close as possible
 * to 10 percent of the total possible links in the network) and at the same time maximize
 * the quality of these good links (maximize the mean of their confidence and weight adjustment).
 *
 * High quality links are those whose confidence-distance mean is above average.
 */

public class Quality implements FitnessFunction {
    private int numberOfNodes;

    public Quality (int numberOfNodes) {
        this.numberOfNodes = numberOfNodes;
    }
    
    public double run(Map<String, ConsensusTuple> consensus) {
        /** 1. Calculate the mean of the confidence-distance means. */
        double conf, dist, confDistSum = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            dist = pair.getValue().getDist();
            confDistSum += (conf + (1 - dist)) / 2.0;
        }
        double mean = confDistSum / consensus.size();

        /** 2. Quantify the number of high quality links and calculate the average of their confidence-distance means */
        confDistSum = 0;
        double confDist, cnt = 0;
        for (Map.Entry<String, ConsensusTuple> pair : consensus.entrySet()) {
            conf = pair.getValue().getConf();
            dist = pair.getValue().getDist();
            confDist = (conf + (1 - dist)) / 2.0;
            if (confDist > mean) {
                confDistSum += confDist;
                cnt += 1;
            }
        }

        /** 3. Calculate first term value */
        double numberOfLinks = (double) (numberOfNodes * numberOfNodes);
        double f1 = Math.abs(cnt - 0.1 * numberOfLinks)/((1 - 0.1) * numberOfLinks);
        double f2 = 1.0 - confDistSum/cnt;
        double fitness = 0.25*f1 + 0.75*f2;

        return fitness;
    }
}
