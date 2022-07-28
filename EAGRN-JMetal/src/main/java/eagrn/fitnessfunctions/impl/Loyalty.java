package eagrn.fitnessfunctions.impl;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;

import eagrn.ConsensusTuple;
import eagrn.fitnessfunctions.FitnessFunction;

public class Loyalty implements FitnessFunction {
    private Map<String, Double[]> timeSeriesMap;
    private Map<String, Double> regulationSigns;

    public Loyalty(String strTimeSeriesFile) {
        if (strTimeSeriesFile == null) {
            throw new RuntimeException("In case of specifying the 'Loyalty' function, the path to the file with the time series of expression levels must be provided.");
        }
        this.timeSeriesMap = readTimeSeries(strTimeSeriesFile);
        this.regulationSigns = getRegulationSigns();
    }

    @Override
    public double run(Map<String, ConsensusTuple> consensus) {

        double sumSquareError = 0;
        int cnt = 0;
        for (Map.Entry<String, Double[]> tsPair : this.timeSeriesMap.entrySet()) {
            ArrayList<Double> factors = new ArrayList<>();
            for (Map.Entry<String, ConsensusTuple> cPair : consensus.entrySet()) {
                String target = cPair.getKey().split(";")[1];
                if (tsPair.getKey().equals(target)){
                    factors.add(cPair.getValue().getConf() * this.regulationSigns.get(cPair.getKey()));
                }
            }
            
            for (int i = 0; i < tsPair.getValue().length - 1; i++) {
                double currExpLevel = tsPair.getValue()[i];
                double nextExpLevel = tsPair.getValue()[i+1];
                double prediction = 0;
                for (int j = 0; j < factors.size(); j++){
                    prediction += currExpLevel * factors.get(j);
                }
                prediction = 1/(1 + Math.pow(Math.E, -5 * prediction));
                sumSquareError += Math.pow(nextExpLevel - prediction, 2);
                cnt ++;
            }
        }
        return sumSquareError / (double) cnt;
    }

    private Map<String, Double[]> readTimeSeries(String strTimeSeriesFile) {
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

    private Map<String, Double> getRegulationSigns() {
        Map<String, Double[]> map = new HashMap<String, Double[]>();

        for (Map.Entry<String, Double[]> entry : this.timeSeriesMap.entrySet()) {
            Double[] array = new Double[entry.getValue().length - 1];
            for (int i = 0; i < entry.getValue().length - 1; i++) {
                array[i] = entry.getValue()[i+1] - entry.getValue()[i];
            }
            map.put(entry.getKey(), array);
        }

        Set<String> keys = map.keySet();
        String[] genes = keys.toArray(new String[keys.size()]);
        Map<String, Double> res = new HashMap<String, Double>();

        for (int i = 0; i < genes.length; i++) {
            for (int j = 0; j < genes.length; j++) {
                if (j == i) continue;
                Double[] arr1 = map.get(genes[i]);
                Double[] arr2 = map.get(genes[j]);
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
