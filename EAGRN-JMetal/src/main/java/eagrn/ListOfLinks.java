package eagrn;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class ListOfLinks {
    private Map<String, Double> mapWithLinks;

    public ListOfLinks (File listFile) {
        this.mapWithLinks = readListFile(listFile);
    }

    private Map<String, Double> readListFile(File listFile) {
        Map<String, Double> map = new HashMap<String, Double>();

        try {
            Scanner sc = new Scanner(listFile);
            while(sc.hasNextLine()) {
                String line = sc.nextLine();
                String[] splitLine = line.split(",");

                String key = splitLine[0] + ";" + splitLine[1];
                Double value = Double.parseDouble(splitLine[2]);
                map.put(key, value);
            }
            sc.close();
        } catch (FileNotFoundException fnfe) {
            throw new RuntimeException(fnfe.getMessage());
        }

        return map;
    }

    public Map<String, Double> getMapWithLinks() {
        return mapWithLinks;
    }
}
