import java.io.*;
import java.util.*;

public class SingleNetworkRunner {
    public static void main(String[] args){
        /** Read input parameters */
        String networkStrFile;
        String geneNamesStrFile;
        String outputStrFile;

        if (args.length == 3) {
            networkStrFile = args[0];
            geneNamesStrFile = args[1];
            outputStrFile = args[2];
        } else {
            networkStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv";
            geneNamesStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/gene_names.txt";
            outputStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/networks/GRN_GENIE3_RF.csv";
        }

        /** Extracting gene names */
        ArrayList<String> geneNames;
        try {
            Scanner sc = new Scanner(new File(geneNamesStrFile));
            String line = sc.nextLine();
            geneNames = new ArrayList<String>(List.of(line.split(" ")));
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        Map<String, Double> map = new ListOfLinks(new File(networkStrFile)).getMapWithLinks();
        double percMaxConf = 0.5;
        int[][] binaryNetwork = getNetworkFromListWithConf(map, geneNames, percMaxConf);

        /** Write the resulting binary matrix to an output csv file */
        try {
            File outputFile = new File(outputStrFile);
            outputFile.getParentFile().mkdirs();
            BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

            bw.write("," + String.join(",", geneNames));
            bw.newLine();
            for (int i = 0; i < binaryNetwork.length; i++) {
                bw.write(geneNames.get(i) + ",");
                for (int j = 0; j < binaryNetwork[i].length; j++) {
                    bw.write(binaryNetwork[i][j] + ((j == binaryNetwork[i].length - 1) ? "" : ","));
                }
                bw.newLine();
            }
            bw.flush();
        } catch (IOException ioe) {
            throw new RuntimeException(ioe.getMessage());
        }
    }

    /** GetNetworkFromListWithK() method */
    public static int[][] getNetworkFromListWithK (Map<String, Double> map, ArrayList<String> geneNames, int k) {
        /**
         * Constructs the Boolean matrix by setting a maximum number of links as the cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        List<Map.Entry<String, Double>> list = new ArrayList<>(map.entrySet());
        Iterator<Map.Entry<String, Double>> iterator = list.iterator();
        int row, col, cnt = 0;
        String key;
        while (cnt < k) {
            key = iterator.next().getKey();
            String [] vKeySplit = key.split("-");
            row = geneNames.indexOf(vKeySplit[0]);
            col = geneNames.indexOf(vKeySplit[1]);
            network[row][col] = 1;
            network[col][row] = 1;
            cnt += 1;
        }

        return network;
    }

    /** GetNetworkFromListWithConf() method */
    private static int[][] getNetworkFromListWithConf(Map<String, Double> map, ArrayList<String> geneNames, double percMaxConf) {
        /**
         * Construct the Boolean matrix by setting a minimum confidence value as a cut-off.
         */

        int numberOfNodes = geneNames.size();
        int[][] network = new int[numberOfNodes][numberOfNodes];

        double conf, max = 0;
        for (Map.Entry<String, Double> pair : map.entrySet()) {
            conf = pair.getValue();
            if (conf > max) max = conf;
        }

        double cutOff = max * percMaxConf;
        int row, col;
        String key;
        for (Map.Entry<String, Double> pair : map.entrySet()) {
            if (pair.getValue() > cutOff) {
                key = pair.getKey();
                String [] vKeySplit = key.split("-");
                row = geneNames.indexOf(vKeySplit[0]);
                col = geneNames.indexOf(vKeySplit[1]);
                network[row][col] = 1;
                network[col][row] = 1;
            }
        }

        return network;
    }

}
