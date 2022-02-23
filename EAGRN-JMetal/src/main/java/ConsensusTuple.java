public class ConsensusTuple implements Comparable<ConsensusTuple> {
    private int freq;
    private double conf;

    public ConsensusTuple (int freq, double conf) {
        this.freq = freq;
        this.conf = conf;
    }

    public void increaseFreq() {
        freq += 1;
    }

    public void increaseConf(double partialConf) {
        conf += partialConf;
    }


    public double getConf() {
        return conf;
    }

    public int getFreq() {
        return freq;
    }

    public String toString() {
        return "Freq: " + freq + ", Conf: " + conf;
    }

    @Override
    public int compareTo(ConsensusTuple o) {
        if (this.conf > o.conf) return -1;
        if (this.conf < o.conf) return 1;
        return 0;
    }
}
