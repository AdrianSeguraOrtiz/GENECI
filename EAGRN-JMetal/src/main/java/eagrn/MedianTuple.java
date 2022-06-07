package eagrn;

public class MedianTuple {
    private double median;
    private double interval;

    public MedianTuple (double median, double interval) {
        this.median = median;
        this.interval = interval;
    }

    public void setMedian(double median) {
        this.median = median;
    }

    public void setInterval(double interval) {
        this.interval = interval;
    }

    public double getMedian() {
        return this.median;
    }

    public double getInterval() {
        return this.interval;
    }

    public String toString() {
        return "Median: " + this.median + ", Interval: " + this.interval;
    }
}
