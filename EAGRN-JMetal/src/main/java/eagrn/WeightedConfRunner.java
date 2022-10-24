package eagrn;

import java.io.File;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;

public class WeightedConfRunner {
    public static void main(String[] args) {
        /** Read input parameters. */
        if (args.length < 3) {
            throw new RuntimeException("It is necessary to specify at least two list of links files");
        }
        String outputFile = args[0];
        Double[] weights = new Double[args.length - 1];
        double sum = 0;
        File[] inferredNetworkFiles = new File[args.length - 1];

        /** Get files and weights separately */
        for (int i = 1; i < args.length; i++) {
            String[] tuple = args[i].split("\\*");
            if (tuple.length < 2) {
                throw new RuntimeException("The entry" + args[i] + "is invalid, remember to separate weight and file name by the '*' character");
            }
            weights[i-1] = Double.parseDouble(tuple[0]);
            sum += weights[i-1];
            inferredNetworkFiles[i-1] = new File(tuple[1]);
        }

        /** If the sum of weights is not 1, an exception is thrown. */
        if (Math.abs(sum - 1.0) > 0.01) {
            throw new RuntimeException("The sum of the weights must be 1");
        }

        /** Read all files with lists. */
        Map<String, Double[]> inferredNetworks = StaticUtils.readAllInferredNetworkFiles(inferredNetworkFiles);

        /** Calculate the list of weighted confidence levels based on the vector of weights. */
        Map<String, Double> weightedConf = StaticUtils.makeConsensus(weights, inferredNetworks);

        /** Sort map */
        Map<String, Double> weightedConfSort = weightedConf
                .entrySet()
                .stream()
                .sorted(Collections.reverseOrder(Map.Entry.comparingByValue()))
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue,
                    (e1, e2) -> e1, LinkedHashMap::new));

        /** Write result in the output file. */
        StaticUtils.writeConsensus(outputFile, weightedConfSort);

    }
}
