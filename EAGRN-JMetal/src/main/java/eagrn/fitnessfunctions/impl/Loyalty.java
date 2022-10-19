package eagrn.fitnessfunctions.impl;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;

import eagrn.fitnessfunctions.FitnessFunction;

/**
 * It attempts to minimize the difference between the 
 * input time series and the one predicted from the previous 
 * state by using the confidence levels inferred by the 
 * consensus algorithm.
 */

public class Loyalty implements FitnessFunction {
    // Stores for each gene (key) the time series given in the input (value)
    private Map<String, Double[]> timeSeriesMap;
    // Stores for each gene (key) the differences between the i+1 and i time states during the input time series (value)
    private Map<String, Double[]> variationsMap;
    // Stores for each gene-gene interaction (key) the direction of regulation (activation 1 or inhibition -1) calculated after a simple analysis of the input time series
    private Map<String, Double> regulationSigns;

    public Loyalty(String strTimeSeriesFile) {
        if (strTimeSeriesFile == null) {
            throw new RuntimeException("In case of specifying the 'Loyalty' function, the path to the file with the time series of expression levels must be provided.");
        }
        this.timeSeriesMap = readTimeSeries(strTimeSeriesFile);

        this.variationsMap = new HashMap<String, Double[]>();
        for (Map.Entry<String, Double[]> entry : this.timeSeriesMap.entrySet()) {
            Double[] array = new Double[entry.getValue().length - 1];
            for (int i = 0; i < entry.getValue().length - 1; i++) {
                array[i] = entry.getValue()[i+1] - entry.getValue()[i];
            }
            this.variationsMap.put(entry.getKey(), array);
        }

        this.regulationSigns = getRegulationSigns();
    }

    @Override
    public double run(Map<String, Double> consensus, Double[] x) {

        double sumSquareError = 0;
        int cnt = 0;
        for (Map.Entry<String, Double[]> tsPair : this.timeSeriesMap.entrySet()) {
            Map<String, Double> factors = new HashMap<String, Double>();
            for (Map.Entry<String, Double> cPair : consensus.entrySet()) {
                String[] genes = cPair.getKey().split(";");
                if (tsPair.getKey().equals(genes[1])){
                    factors.put(genes[0], cPair.getValue() * this.regulationSigns.get(cPair.getKey()));
                }
            }
            
            for (int i = 0; i < tsPair.getValue().length - 1; i++) {
                double currExpLevel = tsPair.getValue()[i];
                double nextExpLevel = tsPair.getValue()[i+1];
                double prediction = currExpLevel;
                for (Map.Entry<String, Double> factor : factors.entrySet()) {
                    prediction += this.variationsMap.get(factor.getKey())[i] * factor.getValue();
                }
                sumSquareError += Math.pow(nextExpLevel - prediction, 2);
                cnt ++;
            }
        }
        return sumSquareError / (double) cnt;
    }

    /** ReadTimeSeries() method */
    private Map<String, Double[]> readTimeSeries(String strTimeSeriesFile) {
        /**
         * It reads the file with the input time series
         */

        Map<String, Double[]> res = new HashMap<String, Double[]>();

        try {
            File timesSeriesFile = new File(strTimeSeriesFile);
            Scanner sc = new Scanner(timesSeriesFile);
            sc.nextLine();
            while(sc.hasNextLine()) {
                String line = sc.nextLine();
                String[] splitLine = line.split(",");

                String gene = splitLine[0].replace("\"", "");
                Double[] array = new Double[splitLine.length - 1];
                for (int i = 1; i < splitLine.length; i++) {
                    array[i-1] = Double.parseDouble(splitLine[i]);
                }
                res.put(gene, array);
            }
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        return res;
    }

    /** ReadTimeSeries() method */
    private Map<String, Double> getRegulationSigns() {
        /**
         * Calculate the direction of regulation (activation 1 or inhibition -1) 
         * for each interaction. To do so, observe whether the increase/decrease 
         * of the factor expression has a positive or negative impact on the 
         * expression level of the target.
         */

        // The res map stores the sign for each interaction
        Set<String> keys = this.variationsMap.keySet();
        String[] genes = keys.toArray(new String[keys.size()]);
        Map<String, Double> res = new HashMap<String, Double>();

        /**
         * The sign will be the one that has the result of adding the divisions 
         * between the variations of the target and those of the factor. Thus, 
         * from the point of view of magnitude, cases where a small change in the 
         * factor (denominator) has a great impact on the target (numerator) will 
         * have a greater value and, on the contrary, cases where a large change 
         * in the factor (denominator) modifies very little the level of expression 
         * of the target (numerator) will have a lower value. Regarding the sign, 
         * activation will be considered in the case of variations of the same direction 
         * in both genes and inhibition in those with opposite directions. The final sign 
         * is calculated after the complete sum of all the divisions with their respective 
         * magnitudes. It should be remembered that only the sign of the sum remains and 
         * that in case there is no real interaction between two genes, this will not be 
         * inferred by the algorithm and therefore the calculated sign will not be used.
         */
        for (int i = 0; i < genes.length; i++) {
            for (int j = 0; j < genes.length; j++) {
                if (j == i) continue;
                Double[] arr1 = this.variationsMap.get(genes[i]);
                Double[] arr2 = this.variationsMap.get(genes[j]);
                Double sign = 0.0;
                for (int k = 0; k < arr1.length; k++) {
                    sign += arr2[k]/arr1[k];
                }
                sign = sign > 0.0 ? 1.0 : -1.0;
                res.put(genes[i] + ";" + genes[j], sign);
            }
        }

        return res;
    }
    
}
