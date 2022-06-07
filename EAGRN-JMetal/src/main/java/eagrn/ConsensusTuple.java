package eagrn;

public class ConsensusTuple implements Comparable<ConsensusTuple> {
    private double conf;
    private double dist;

    public ConsensusTuple (double conf, double dist) {
        this.conf = conf;
        this.dist = dist;
    }

    public void increaseConf(double partialConf) {
        this.conf += partialConf;
    }

    public void setDist(double dist) {
        this.dist = dist;
    }

    public double getConf() {
        return this.conf;
    }

    public double getDist() {
        return this.dist;
    }

    public String toString() {
        return "Conf: " + this.conf + ", Dist: " + this.dist;
    }

    @Override
    public int compareTo(ConsensusTuple o) {
        if (this.conf > o.conf) return -1;
        if (this.conf < o.conf) return 1;
        return 0;
    }
}
