package eagrn;

import eagrn.cutoffcriteria.CutOffCriteria;

import java.io.*;
import java.util.*;

public class BinarizeNetworkRunner {
    public static void main(String[] args){
        /** Declare the main execution variables */
        CutOffCriteria cutOffCriteriaOnlyConf;

        /** Read input parameters */
        String listOfLinksStrFile;
        String geneNamesStrFile;
        String outputStrFile;
        String strCutOffCriteria;
        float cutOffValue;

        if (args.length > 2) {
            listOfLinksStrFile = args[0];
            geneNamesStrFile = args[1];
            outputStrFile = args[2];
            if (args.length == 5) {
                strCutOffCriteria = args[3];
                cutOffValue = Float.parseFloat(args[4]);
            } else {
                strCutOffCriteria = "MinConfidence";
                cutOffValue = 0.1f;
            }
        } else {
            throw new RuntimeException("The list of confidence values, the list of gene names and the path to the output file are three required parameters.");
        }

        /** Extracting gene names */
        ArrayList<String> geneNames = StaticUtils.getGeneNames(geneNamesStrFile);

        /** Establish the cut-off criteria */
        cutOffCriteriaOnlyConf = (CutOffCriteria) StaticUtils.getCutOffCriteriaFromString(strCutOffCriteria, cutOffValue, geneNames);

        /** Extract the list of links */
        Map<String, Float> map = StaticUtils.getMapWithLinks(new File(listOfLinksStrFile));

        /** Calculate the binary matrix according to the selected criteria */
        boolean[][] binaryNetwork = cutOffCriteriaOnlyConf.getNetwork(map);

        /** Write the resulting binary matrix to an output csv file */
        StaticUtils.writeBinaryNetwork(outputStrFile, binaryNetwork, geneNames);
    }
}
