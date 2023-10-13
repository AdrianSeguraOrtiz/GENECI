package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.Map;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.FitnessFunction;

import org.apache.commons.math3.ode.FirstOrderDifferentialEquations;
import org.apache.commons.math3.ode.nonstiff.EulerIntegrator;


public class DynamicsMeasureODE implements FitnessFunction { 

    private ArrayList<String> geneNames;

    public DynamicsMeasureODE(ArrayList<String> geneNames) {
        this.geneNames = geneNames;
    }

    @Override
    public double run(Map<String, Float> consensus, Double[] x) {
        float[][] adjacencyMatrix = StaticUtils.getFloatMatrixFromEdgeList(consensus, geneNames, 4);
        return calcularPuntajeEstabilidad(adjacencyMatrix);
    }
    
    public double calcularPuntajeEstabilidad(float[][] matrizAdyacencia) {
        // Crear el modelo de ODE a partir de la matriz de adyacencia
        FirstOrderDifferentialEquations modelo = new ModeloODE(matrizAdyacencia);

        // Crear el integrador (por ejemplo, el método de Euler)
        EulerIntegrator integrador = new EulerIntegrator(0.01); // Paso de integración de 0.01

        // Definir las condiciones iniciales
        int numNodos = matrizAdyacencia.length;
        double[] condicionesIniciales = new double[numNodos];

        // Asignar valores iniciales a los nodos
        for (int i = 0; i < numNodos; i++) {
            condicionesIniciales[i] = 1.0;
        }

        // Simular la evolución de la red
        double[] estadoFinal = new double[matrizAdyacencia.length];
        integrador.integrate(modelo, 0.0, condicionesIniciales, 1.0, estadoFinal);

        // Calcular el puntaje de estabilidad (por ejemplo, el promedio de los valores finales)
        double puntajeEstabilidad = calcularPromedio(estadoFinal);

        return puntajeEstabilidad;
    }

    // Clase que define el modelo de ODE
    public class ModeloODE implements FirstOrderDifferentialEquations {
        private float[][] matrizAdyacencia;

        public ModeloODE(float[][] matrizAdyacencia) {
            this.matrizAdyacencia = matrizAdyacencia;
        }

        @Override
        public int getDimension() {
            return matrizAdyacencia.length;
        }

        @Override
        public void computeDerivatives(double t, double[] y, double[] yDot) {
            // Calcular las derivadas de los nodos en función de la matriz de adyacencia
            int n = getDimension();
            for (int i = 0; i < n; i++) {
                double derivada = 0.0;
                for (int j = 0; j < n; j++) {
                    derivada += matrizAdyacencia[i][j] * y[j];
                }
                yDot[i] = y[i] - derivada;
            }
        }
    }

    // Función auxiliar para calcular el promedio de un arreglo
    public double calcularPromedio(double[] arreglo) {
        double suma = 0.0;
        for (double valor : arreglo) {
            suma += valor;
        }
        return suma / arreglo.length;
    }
    
}
