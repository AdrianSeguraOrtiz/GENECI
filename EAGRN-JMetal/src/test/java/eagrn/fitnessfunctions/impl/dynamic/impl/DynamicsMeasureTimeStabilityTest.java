package eagrn.fitnessfunctions.impl.dynamic.impl;

import org.testng.annotations.Test;

public class DynamicsMeasureTimeStabilityTest {

    @Test
    void shouldReturnFitnessValueCaseA() {
        genericTest(50);
    }

    @Test
    void shouldReturnFitnessValueCaseB() {
        genericTest(100);
    }

    @Test
    void shouldReturnFitnessValueCaseC() {
        genericTest(500);
    }

    @Test
    void shouldReturnFitnessValueCaseD() {
        genericTest(1000);
    }


    private void genericTest(int size) {
        // TODO: Implement test

        assert(true);
    }
}
