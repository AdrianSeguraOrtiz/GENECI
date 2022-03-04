package eagrn;

import eagrn.cutoffcriteria.CutOffCriteriaOnlyConf;
import eagrn.cutoffcriteria.impl.MaxNumLinksBestConfCriteria;
import eagrn.cutoffcriteria.impl.MinConfidenceCriteria;

import java.io.*;
import java.util.*;

public class SingleNetworkRunner {
    public static void main(String[] args){
        /** Declare the main execution variables */
        CutOffCriteriaOnlyConf cutOffCriteriaOnlyConf;

        /** Read input parameters */
        String listOfLinksStrFile;
        String geneNamesStrFile;
        String outputStrFile;
        String strCutOffCriteria;
        double cutOffValue;

        if (args.length == 5) {
            listOfLinksStrFile = args[0];
            geneNamesStrFile = args[1];
            outputStrFile = args[2];
            strCutOffCriteria = args[3];
            cutOffValue = Double.parseDouble(args[4]);
        } else {
            listOfLinksStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv";
            geneNamesStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/gene_names.txt";
            outputStrFile = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/networks/GRN_GENIE3_RF.csv";
            strCutOffCriteria = "MinConfidence";
            cutOffValue = 0.1;
        }

        /** Establish the cut-off criteria */
        switch (strCutOffCriteria) {
            case "MinConfidence":
                cutOffCriteriaOnlyConf = new MinConfidenceCriteria(cutOffValue);
                break;
            case "MaxNumLinksBestConfCriteria":
                cutOffCriteriaOnlyConf = new MaxNumLinksBestConfCriteria((int) cutOffValue);
                break;
            default:
                throw new RuntimeException("The cut-off criteria entered is not available");
        }

        /** Extracting gene names */
        ArrayList<String> geneNames;
        try {
            Scanner sc = new Scanner(new File(geneNamesStrFile));
            String line = sc.nextLine();
            String[] lineSplit = line.split(" ");
            geneNames = new ArrayList<>(List.of(lineSplit));
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        /** Extract the list of links */
        Map<String, Double> map = new ListOfLinks(new File(listOfLinksStrFile)).getMapWithLinks();

        /** Calculate the binary matrix according to the selected criteria */
        int[][] binaryNetwork = cutOffCriteriaOnlyConf.getNetwork(map, geneNames);

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
}
