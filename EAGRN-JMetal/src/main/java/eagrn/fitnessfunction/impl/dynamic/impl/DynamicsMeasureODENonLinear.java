package eagrn.fitnessfunction.impl.dynamic.impl;

import java.util.ArrayList;
import java.util.Map;

import eagrn.StaticUtils;
import eagrn.fitnessfunction.FitnessFunction;

import org.apache.commons.math3.ode.FirstOrderDifferentialEquations;
import org.apache.commons.math3.ode.nonstiff.DormandPrince54Integrator;


public class DynamicsMeasureODENonLinear implements FitnessFunction { 

    private ArrayList<String> geneNames;

    public DynamicsMeasureODENonLinear(ArrayList<String> geneNames) {
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
        DormandPrince54Integrator integrador = new DormandPrince54Integrator(1e-8, 1.0, 1e-10, 1e-10);

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
                double suma = 0.0;
                for (int j = 0; j < n; j++) {
                    suma += matrizAdyacencia[j][i] * y[j];
                }
                yDot[i] = -y[i] + f(suma);
            }
        }

        // Función no lineal para calcular las derivadas de los nodos
        public double f(double x) {
            double n = 2.0; // Parámetro que ajusta la no-linealidad
            double k = 0.5; // Parámetro que ajusta la no-linealidad
            return Math.pow(x, n) / (Math.pow(k, n) + Math.pow(x, n));
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
