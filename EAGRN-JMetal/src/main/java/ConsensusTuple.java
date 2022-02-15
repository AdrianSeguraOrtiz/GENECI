public class ConsensusTuple {
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

    public String toString() {
        return "Freq: " + freq + ", Conf: " + conf;
    }

    public double getConf() {
        return conf;
    }

    public int getFreq() {
        return freq;
    }
}
