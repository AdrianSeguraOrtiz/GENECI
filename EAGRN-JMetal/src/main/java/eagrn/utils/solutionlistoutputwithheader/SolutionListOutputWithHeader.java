package eagrn.utils.solutionlistoutputwithheader;

import java.io.BufferedWriter;
import java.io.IOException;
import java.util.List;

import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.errorchecking.JMetalException;
import org.uma.jmetal.util.fileoutput.FileOutputContext;
import org.uma.jmetal.util.fileoutput.SolutionListOutput;

public class SolutionListOutputWithHeader extends SolutionListOutput {
    private String[] fitnessFormulas;
    private String[] fileLabels;

    public SolutionListOutputWithHeader(List<? extends Solution<?>> solutionList, String[] fitnessFormulas, String[] fileLabels) {
        super(solutionList);
        this.fitnessFormulas = fitnessFormulas;
        this.fileLabels = fileLabels;
    }

    @Override
    public void printVariablesToFile(FileOutputContext context, List<? extends Solution<?>> solutionList) {
        BufferedWriter bufferedWriter = context.getFileWriter();

        try {
            if (solutionList.size() > 0) {
                bufferedWriter.write(String.join(",", fileLabels));
                bufferedWriter.newLine();
                int numberOfVariables = solutionList.get(0).variables().size();
                for (int i = 0; i < solutionList.size(); i++) {
                    for (int j = 0; j < numberOfVariables - 1; j++) {
                        bufferedWriter.write("" + solutionList.get(i).variables().get(j) + context.getSeparator());
                    }
                    bufferedWriter.write("" + solutionList.get(i).variables().get(numberOfVariables - 1));

                    bufferedWriter.newLine();
                }
            }

            bufferedWriter.close();
        } catch (IOException e) {
            throw new JMetalException("Error writing data ", e);
        }
    }

    @Override
    public void printObjectivesToFile(FileOutputContext context, List<? extends Solution<?>> solutionList){
        BufferedWriter bufferedWriter = context.getFileWriter();

        try {
            if (solutionList.size() > 0) {
                bufferedWriter.write(String.join(",", fitnessFormulas));
                bufferedWriter.newLine();
                int numberOfObjectives = solutionList.get(0).objectives().length;
                for (int i = 0; i < solutionList.size(); i++) {
                    for (int j = 0; j < numberOfObjectives - 1; j++) {
                        bufferedWriter.write(solutionList.get(i).objectives()[j] + context.getSeparator());
                    }
                    bufferedWriter.write("" + solutionList.get(i).objectives()[numberOfObjectives - 1]);
                    bufferedWriter.newLine();
                }
            }

            bufferedWriter.close();
        } catch (IOException e) {
            throw new JMetalException("Error printing objectives to file: ", e);
        }
    }
    
}
