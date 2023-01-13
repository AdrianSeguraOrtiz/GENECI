
import java.util.*;

public class Friedman {

	public static void main(String[] args) {

		Vector <String> algoritmos;
		Vector <String> datasets;
		Vector <Vector <Double>> datos;
		String cadena = "";
		StringTokenizer lineas, tokens;
		String linea, token;
		int i, j, k, m;
		int posicion;
		double mean[][];
		double meanAR[][];
		Pareja orden[][];
		Pareja rank[][];
		Pareja ordenAR[];
		Pareja rankAR[];
		Pareja bRank[];
		Pareja bOrden[];
		double diffBlocks[];
		double CE[][][];
		double medians[][];
		double estimators[];
		boolean encontrado;
		int ig;
		double sum;
		boolean visto[];
		Vector <Integer> porVisitar;
		double Rj[];
		double RjAR[];
		double Sj[];
		double SMj[];
		double min, max;
		double friedman;
		double sumatoria=0;
		double temporal;
		double termino1, termino2, termino3;
		double numerador, denominador;
		double iman;
		boolean vistos[];
		int pos;
		double maxVal, minVal;
		double diffMax = 0;
		double Pm = 0;
		double PmAR = 0;
		double PmQ = 0;		
		double rankingRef;
		double Pi[];
		double PiAR[];
		double PiQ[];
		double ALPHAiHolm[];
		double ALPHAiHolland[];
		double ALPHAiRom[];
		double ALPHAiFinner[];
		double ALPHA2Li = 0;
		double adjustedRom[];
		String ordenAlgoritmosF[];
		String ordenAlgoritmosAF[];
		String ordenAlgoritmosQ[];
		double adjustedP[][];
		double Ci[];
		double SE;
		boolean parar, otro;
		int lineaN = 0;
		int columnaN = 0;

		if (args.length != 1) {
			System.err.println("Error. 1 parameter is needed: Input file in CSV format.");
			System.exit(1);
		}

		algoritmos = new Vector <String>();
		datasets = new Vector <String>();
		datos = new Vector <Vector <Double>>();

		/** Read the data file *****************************************************************************************/

		/*Read the result file*/
		cadena = Fichero.leeFichero(args[0]);
		lineas = new StringTokenizer (cadena,"\n\r");
		while (lineas.hasMoreTokens()) {
			linea = lineas.nextToken();
			tokens = new StringTokenizer(linea,",\t");
			columnaN = 0;
			while (tokens.hasMoreTokens()) {
				if (lineaN == 0) {
					if (columnaN == 0) {
						token = tokens.nextToken();
					} else {
						token = tokens.nextToken();
						algoritmos.add(new String(token));
						datos.add(new Vector <Double>());
					}
				} else {
					if (columnaN == 0) {
						token = tokens.nextToken();
						datasets.add(new String(token));
					} else {
						token = tokens.nextToken();
						datos.elementAt(columnaN-1).add(new Double(token));
					}
				}
				columnaN++;
			}
			lineaN++;
		}

		mean = new double[datasets.size()][algoritmos.size()];

		/*Compute the average performance per algorithm for each data set*/
		for (i=0; i<datasets.size(); i++) {
			for (j=0; j<algoritmos.size(); j++) {
				mean[i][j] = datos.elementAt(j).elementAt(i).doubleValue();
			}
		}
		
		/** FRIEDMAN PROCEDURE ****************************************************************************************/

	    /*We use the pareja structure to compute and order rankings*/
	    orden = new Pareja[datasets.size()][algoritmos.size()];
	    for (i=0; i<datasets.size(); i++) {
	    	for (j=0; j<algoritmos.size(); j++){
	    		orden[i][j] = new Pareja (j,mean[i][j]);
	    	}
	    	Arrays.sort(orden[i]);
	    }

	    /*building of the rankings table per algorithms and data sets*/
	    rank = new Pareja[datasets.size()][algoritmos.size()];
	    posicion = 0;
	    for (i=0; i<datasets.size(); i++) {
	    	for (j=0; j<algoritmos.size(); j++){
	    		encontrado = false;
	    		for (k=0; k<algoritmos.size() && !encontrado; k++) {
	    			if (orden[i][k].indice == j) {
	    				encontrado = true;
	    				posicion = k+1;
	    			}
	    		}
	    		rank[i][j] = new Pareja(posicion,orden[i][posicion-1].valor);
	    	}
	    }

	    /*In the case of having the same performance, the rankings are equal*/
	    for (i=0; i<datasets.size(); i++) {
	    	visto = new boolean[algoritmos.size()];
	    	porVisitar= new Vector <Integer> ();

	    	Arrays.fill(visto,false);
	    	for (j=0; j<algoritmos.size(); j++) {
		    	porVisitar.removeAllElements();
	    		sum = rank[i][j].indice;
	    		visto[j] = true;
	    		ig = 1;
	    		for (k=j+1;k<algoritmos.size();k++) {
	    			if (rank[i][j].valor == rank[i][k].valor && !visto[k]) {
	    				sum += rank[i][k].indice;
	    				ig++;
	    				porVisitar.add(new Integer(k));
	    				visto[k] = true;
	    			}
	    		}
	    		sum /= (double)ig;
	    		rank[i][j].indice = sum;
	    		for (k=0; k<porVisitar.size(); k++) {
	    			rank[i][porVisitar.elementAt(k).intValue()].indice = sum;
	    		}
	    	}
	    }

	    /*compute the average ranking for each algorithm*/
	    Rj = new double[algoritmos.size()];
	    for (i=0; i<algoritmos.size(); i++){
	    	Rj[i] = 0;
	    	for (j=0; j<datasets.size(); j++) {
	    		Rj[i] += rank[j][i].indice / ((double)datasets.size());
	    	}
	    }
	    
	    /**FRIEDMAN ALIGNED RANKS PROCEDURE *******************************************************************************/
	    
		meanAR = new double[datasets.size()][algoritmos.size()];
		/*Compute the average performance per algorithm for each data set*/
		for (i=0; i<datasets.size(); i++) {
			sum = 0;
			for (j=0; j<algoritmos.size(); j++) {
				sum += mean[i][j];
			}
			sum /= algoritmos.size();
			for (j=0; j<algoritmos.size(); j++) {
				meanAR[i][j] = mean[i][j] - sum;
			}
		}
		
	    /*We use the pareja structure to compute and order rankings*/
	    ordenAR = new Pareja[datasets.size() * algoritmos.size()];
	    for (i=0; i<datasets.size() * algoritmos.size(); i++) {
	    		ordenAR[i] = new Pareja (i,meanAR[i/algoritmos.size()][i%algoritmos.size()]);
	    }
	    Arrays.sort(ordenAR);
	    
	    /*building of the rankings table per algorithms and data sets*/
	    rankAR = new Pareja[datasets.size() * algoritmos.size()];
	    posicion = 0;
	    for (i=0; i<datasets.size() * algoritmos.size(); i++) {
	    	encontrado = false;
	    	for (k=0; k<algoritmos.size() * datasets.size() && !encontrado; k++) {
	    		if (ordenAR[k].indice == i) {
	    			encontrado = true;
	    			posicion = k+1;
	    		}
	    	}
	    	rankAR[i] = new Pareja(posicion,ordenAR[posicion-1].valor);
	    }
	    
	    /*In the case of having the same performance, the rankings are equal*/
	    visto = new boolean[algoritmos.size()*datasets.size()];
	    porVisitar= new Vector <Integer> ();

	    Arrays.fill(visto,false);
	    for (i=0; i<algoritmos.size()*datasets.size(); i++) {
	    	porVisitar.removeAllElements();
	    	sum = rankAR[i].indice;
	    	visto[i] = true;
	    	ig = 1;
	    	for (j=i+1;j<algoritmos.size()*datasets.size();j++) {
	    		if (rankAR[i].valor == rankAR[j].valor && !visto[j]) {
	    			sum += rankAR[j].indice;
	    			ig++;
	    			porVisitar.add(new Integer(j));
	    			visto[j] = true;
	    		}
	    	}
	    	sum /= (double)ig;
	    	rankAR[i].indice = sum;
	    	for (j=0; j<porVisitar.size(); j++) {
	    		rankAR[porVisitar.elementAt(j).intValue()].indice = sum;
	    	}
	    }
   
	    /*compute the average ranking for each algorithm*/
	    RjAR = new double[algoritmos.size()];
	    for (i=0; i<algoritmos.size(); i++){
	    	RjAR[i] = 0;
	    	for (j=0; j<datasets.size(); j++) {
	    		RjAR[i] += rankAR[j*algoritmos.size() + i].indice / ((double)datasets.size());
	    	}
	    }
	    
	    /** CONTRAST ESTIMATION *******************************************************************************************/
	    CE = new double[algoritmos.size()][algoritmos.size()][datasets.size()];
	    for (i=0; i<algoritmos.size(); i++) {
	    	for (j=i+1; j<algoritmos.size(); j++) {
	    		for (k=0; k<datasets.size(); k++) {
	    			CE[i][j][k] = mean[k][i] - mean[k][j];
	    		}
	    	}
	    }

	    medians = new double[algoritmos.size()][algoritmos.size()];
	    for (i=0; i<algoritmos.size(); i++) {
	    	for (j=i+1; j<algoritmos.size(); j++) {
	    		Arrays.sort(CE[i][j]);
	    		if (CE[i][j].length % 2 == 1) {
	    			medians[i][j] = CE[i][j][datasets.size()/2];
	    		} else {
	    			medians[i][j] = (CE[i][j][datasets.size()/2] + CE[i][j][(datasets.size()/2)-1]) / 2.0;	    			
	    		}
	    	}
	    }
	    
	    estimators = new double[algoritmos.size()];
	    Arrays.fill(estimators, 0);
	    for (i=0; i<algoritmos.size(); i++) {
	    	for (j=0; j<algoritmos.size(); j++) {
		    		estimators[i] += medians[i][j] - medians[j][i];
	    	}
	    	estimators[i] /= algoritmos.size();
	    }
	    
	    /** QUADE TEST ***************************************************************************************************/
	    
	    diffBlocks = new double[datasets.size()];
	    for (i=0; i<datasets.size(); i++) {
	    	min = mean[i][0];
	    	max = mean[i][0];
	    	for (j=1; j<mean[i].length; j++) {
	    		if (mean[i][j] < min){
	    			min = mean[i][j];
	    		} else if (mean[i][j] > max) {
	    			max = mean[i][j];
	    		}
	    	}
	    	diffBlocks[i] = max - min;
	    }
	    
	    /*We use the pareja structure to compute and order rankings*/
	    bOrden = new Pareja[datasets.size()];
	    for (i=0; i<datasets.size(); i++) {
	    	bOrden[i] = new Pareja (i,diffBlocks[i]);
	    }
    	Arrays.sort(bOrden);

	    /*building of the rankings table per algorithms and data sets*/
	    bRank = new Pareja[datasets.size()];
	    posicion = 0;
	    for (i=0; i<datasets.size(); i++){
	    	encontrado = false;
	    	for (j=0; j<datasets.size() && !encontrado; j++) {
	    		if (bOrden[j].indice == i) {
	    			encontrado = true;
	    			posicion = j+1;
	    		}
	    	}
	    	bRank[i] = new Pareja(datasets.size()+1-posicion,bOrden[posicion-1].valor);
	    }

	    /*In the case of having the same performance, the rankings are equal*/
	    visto = new boolean[datasets.size()];
	    porVisitar= new Vector <Integer> ();

	    Arrays.fill(visto,false);
	    for (i=0; i<datasets.size(); i++) {
	    	porVisitar.removeAllElements();
	    	sum = bRank[i].indice;
	    	visto[i] = true;
	    	ig = 1;
	    	for (j=i+1;j<datasets.size();j++) {
	    		if (bRank[i].valor == bRank[j].valor && !visto[j]) {
	    			sum += bRank[j].indice;
	    			ig++;
	    			porVisitar.add(new Integer(j));
	    			visto[j] = true;
	    		}
	    	}
	    	sum /= (double)ig;
	    	bRank[i].indice = sum;
	    	for (j=0; j<porVisitar.size(); j++) {
	    		bRank[porVisitar.elementAt(j).intValue()].indice = sum;
	    	}
	    }

	    /*compute the average ranking for each algorithm*/
	    Sj = new double[algoritmos.size()];
	    SMj = new double[algoritmos.size()];
	    for (i=0; i<algoritmos.size(); i++){
	    	SMj[i] = 0;
	    	for (j=0; j<datasets.size(); j++) {
	    		Sj[i] += ((rank[j][i].indice)-(algoritmos.size()+1)/2)* bRank[j].indice;
	    		SMj[i] += (rank[j][i].indice)* bRank[j].indice / (((double)datasets.size()*(datasets.size()+1))/2.0);
	    	}
	    }
	    
	    /** Print the results of multiple comparison tests ****************************************************************/

	    System.out.println("\\documentclass[a4paper,10pt]{article}\n" +
	    		"\\usepackage{graphicx}\n" +
	    		"\\usepackage{lscape}\n" +
	    		"\\title{Results}\n" +
	    		"\\author{}\n" +
	    		"\\date{\\today}\n" +
	    		"\\begin{document}\n" +
	    		"\\begin{landscape}\n" +
			    "\\oddsidemargin 0in \\topmargin 0in" +
	    		"\\maketitle\n" +
	    		"\\section{Tables of Friedman, Aligned Friedman, Bonferroni-Dunn, Holm, Hochberg and Hommel Tests}");

	    /*Print the average ranking per algorithm for Friedman*/
	    System.out.println("\\begin{table}[!htp]\n" +
	    		"\\centering\n" +
	    		"\\caption{Average Rankings of the algorithms (Friedman)\n}" +
	    		"\\begin{tabular}{c|c}\n" +
	    "Algorithm&Ranking\\\\\n\\hline");
	    for (i=0; i<algoritmos.size();i++) {
	    	System.out.println((String)algoritmos.elementAt(i)+"&"+Rj[i]+"\\\\");
	    }
	    System.out.println("\\end{tabular}\n\\end{table}");

	    /*Compute the Friedman statistic*/
	    termino1 = (12*(double)datasets.size())/((double)algoritmos.size()*((double)algoritmos.size()+1));
	    termino2 = (double)algoritmos.size()*((double)algoritmos.size()+1)*((double)algoritmos.size()+1)/(4.0);
	    for (i=0; i<algoritmos.size();i++) {
	    	sumatoria += Rj[i]*Rj[i];
	    }
	    friedman = (sumatoria - termino2) * termino1;
	    System.out.println("\n\nFriedman statistic (distributed according to chi-square with "+(algoritmos.size()-1)+" degrees of freedom: "+friedman+". ");

        double pFriedman, pIman;
        pFriedman = ChiSq(friedman, (algoritmos.size()-1));

        System.out.print("P-value computed by Friedman Test: " + pFriedman +".\\newline\n\n");
    
        /*Compute the Iman-Davenport statistic*/
	    iman = ((datasets.size()-1)*friedman)/(datasets.size()*(algoritmos.size()-1) - friedman);
	    System.out.println("Iman and Davenport statistic (distributed according to F-distribution with "+(algoritmos.size()-1)+" and "+ (algoritmos.size()-1)*(datasets.size()-1) +" degrees of freedom: "+iman+". ");
        pIman = FishF(iman, (algoritmos.size()-1),(algoritmos.size()-1) * (datasets.size() - 1));
		System.out.print("P-value computed by Iman and Daveport Test: " + pIman +".\\newline\n\n");
	    
	    termino3 = Math.sqrt((double)algoritmos.size()*((double)algoritmos.size()+1)/(6.0*(double)datasets.size()));
	    
	    System.out.println("\n\\newpage\n");
	    

        /*Print the average ranking per algorithm for Aligned Friedman*/
        System.out.println("\\begin{table}[!htp]\n" +
        "\\centering\n" +
        "\\caption{Average Rankings of the algorithms (Aligned Friedman)\n}" +
        "\\begin{tabular}{c|c}\n" +
        "Algorithm&Ranking\\\\\n\\hline");
        for (i=0; i<algoritmos.size();i++) {
          System.out.println((String)algoritmos.elementAt(i)+"&"+RjAR[i]+"\\\\");
        }
        System.out.println("\\end{tabular}\n\\end{table}");


	    /*Compute the Aligned Friedman statistic*/
	    termino1 = (double)algoritmos.size()-1;
	    termino2 = (double)algoritmos.size()*((double)datasets.size()*datasets.size())/4.0;
	    termino2 *= ((double)algoritmos.size()*(double)datasets.size() + 1)*((double)algoritmos.size()*(double)datasets.size() + 1);
	    
	    sumatoria = 0;
	    for (i=0; i<algoritmos.size();i++) {
	    	temporal = 0;
	    	for (j=0; j<datasets.size(); j++) {
	    		temporal += (double)rankAR[j*algoritmos.size()+i].indice;
	    	}
	    	sumatoria += temporal * temporal;
	    }
	    sumatoria /= (double)algoritmos.size();
	    numerador = sumatoria - termino2;
	    numerador *= termino1;
	    
	    termino1 = (double)algoritmos.size()*(double)datasets.size()*((double)algoritmos.size()*(double)datasets.size() + 1)* ((double)algoritmos.size()*(double)datasets.size()*2 + 1);
	    termino1 /= 6;
	    
	    sumatoria = 0;
	    for (i=0; i<datasets.size();i++) {
	    	temporal = 0;
	    	for (j=0; j<algoritmos.size(); j++) {
	    		temporal += (double)rankAR[i*algoritmos.size()+j].indice;
	    	}
	    	sumatoria += temporal * temporal;
	    }
	    denominador = termino1 - sumatoria;
	    
	    friedman = numerador / denominador;
	    System.out.println("\n\nAligned Friedman statistic (distributed according to chi-square with "+(algoritmos.size()-1)+" degrees of freedom: "+friedman+". ");

        pFriedman = ChiSq(friedman, (algoritmos.size()-1));

        System.out.print("P-value computed by Aligned Friedman Test: " + pFriedman +".\\newline\n\n");
        
	    System.out.println("\n\\newpage\n");
        
        
	    /*Print the average ranking per algorithm for Quade*/
	    System.out.println("\\begin{table}[!htp]\n" +
	    		"\\centering\n" +
	    		"\\caption{Average Rankings of the algorithms (Quade)\n}" +
	    		"\\begin{tabular}{c|c}\n" +
	    "Algorithm&Ranking\\\\\n\\hline");
	    for (i=0; i<algoritmos.size();i++) {
	    	System.out.println((String)algoritmos.elementAt(i)+"&"+SMj[i]+"\\\\");
	    }
	    System.out.println("\\end{tabular}\n\\end{table}");
        

	    /*Compute the Quade statistic*/
	    sumatoria = 0;
	    for (i=0; i<algoritmos.size(); i++) {
	    	sumatoria += Sj[i]*Sj[i];
	    }
	    sumatoria /= datasets.size();
	    termino1 = (datasets.size()*(datasets.size()+1)*(2*datasets.size()+1)*algoritmos.size()*(algoritmos.size()+1)*(algoritmos.size()-1)) / 72;
	    iman = ((datasets.size()-1)*sumatoria) / (termino1 - sumatoria);
	    System.out.println("Quade statistic (distributed according to F-distribution with "+(algoritmos.size()-1)+" and "+ (algoritmos.size()-1)*(datasets.size()-1) +" degrees of freedom: "+iman+". ");
        pIman = FishF(iman, (algoritmos.size()-1),(algoritmos.size()-1) * (datasets.size() - 1));
		System.out.print("P-value computed by Quade Test: " + pIman +".\\newline\n\n");

	    System.out.println("\n\\newpage\n");

	    /** PRINT THE CONTRAST ESTIMATION*/
		
        System.out.println("\\begin{table}[!htp]\n\\centering\\tiny\n\\caption{Contrast Estimation}\n" + "\\begin{tabular}{");
        for (i=0; i<algoritmos.size()+1; i++) {
        	System.out.print("|r");
        }
        System.out.print("|}\n\\hline\n" + " ");
        for (i=0; i<algoritmos.size(); i++) {
        	System.out.print("&" + algoritmos.elementAt(i));
        }        
        System.out.println("\\\\\n\\hline");
        for (i=0; i<algoritmos.size(); i++) {
        	System.out.print(algoritmos.elementAt(i));
        	for (j=0; j<algoritmos.size(); j++) {
        		System.out.printf("&%.4g",estimators[i] - estimators[j]);
        	}
            System.out.println("\\\\\n\\hline");
        }

	    System.out.println("\n" + "\\end{tabular}\n" + "\\end{table}");

	    System.out.println("\n\\newpage\n");
        
        
	    /************ COMPARING A CONTROL METHOD *************************************************************************/	    

		/*Compute the unadjusted p_i value for each comparison alpha=0.05*/
	    Pi = new double[algoritmos.size()-1];
	    PiAR = new double[algoritmos.size()-1];
	    PiQ = new double[algoritmos.size()-1];
	    ALPHAiHolm = new double[algoritmos.size()-1];
	    ALPHAiHolland = new double[algoritmos.size()-1];
	    ALPHAiRom = new double[algoritmos.size()-1];
	    ALPHAiFinner = new double[algoritmos.size()-1];
	    ordenAlgoritmosF = new String[algoritmos.size()-1];
	    ordenAlgoritmosAF = new String[algoritmos.size()-1];
	    ordenAlgoritmosQ = new String[algoritmos.size()-1];
	    adjustedRom = new double[algoritmos.size()-1];

	    calcularROM(0.05,ALPHAiRom, adjustedRom);
	    
	    /** USING FRIEDMAN TEST ******************************************************************************************/
	    
	    SE = termino3;
	    vistos = new boolean[algoritmos.size()];
	    rankingRef = 0.0;
	    Arrays.fill(vistos,false);
	    for (i=0; i<algoritmos.size();i++) {
	    	for (j=0;vistos[j]==true;j++);
	    	pos = j;
	    	maxVal = Rj[j];
	    	minVal = Rj[j];
	    	for (j=j+1;j<algoritmos.size();j++) {
	    		if (i > 1) {
	    			if (vistos[j] == false && Rj[j] > maxVal) {
	    				pos = j;
	    				maxVal = Rj[j];
	    			}
	    		} else if (i == 1) {
	    			if (vistos[j] == false && Rj[j] > maxVal) {
	    				pos = j;
	    				maxVal = Rj[j];
	    			}	    			
	    			if (vistos[j] == false && Rj[j] < minVal) {
	    				minVal = Rj[j];
	    			}	    			
	    		} else {
	    			if (vistos[j] == false && Rj[j] < maxVal) {
	    				pos = j;
	    				maxVal = Rj[j];
	    			}
	    		}
	    	}
	    	vistos[pos] = true;
	    	if (i==1) {
	    		diffMax = minVal - rankingRef;
		    	Pm = 2*CDF_Normal.normp((-1)*Math.abs((diffMax)/SE));
	    		ALPHA2Li = (1 - Pm) / (1 - 0.05) * 0.05;
	    	}
	    	if (i==0) {
	    		rankingRef = maxVal;
                System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Holm / Hochberg / Holland / Rom / Finner / Li Table for $\\alpha=0.05$ (FRIEDMAN)}\n" +
               		"\\begin{tabular}{ccccccccc}\n" +
               		"$i$&algorithm&$z=(R_0 - R_i)/SE$&$p$&Holm/Hochberg/Hommel&Holland&Rom&Finner&Li\\\\\n\\hline");
	    	} else {
	    		ALPHAiHolm[i-1] = 0.05/((double)algoritmos.size()-(double)i);
	    		ALPHAiHolland[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/((double)algoritmos.size()-(double)i)));
	    		ALPHAiFinner[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/(((double)algoritmos.size()-1)/(double)i)));
	    		ordenAlgoritmosF[i-1] = new String ((String)algoritmos.elementAt(pos));
	    		
                System.out.println((algoritmos.size()-i) + "&" + algoritmos.elementAt(pos) + "&" +
               		Math.abs((rankingRef-maxVal)/SE) + "&" +
               		2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE)) + 
               		"&" + ALPHAiHolm[i-1] +
               		"&" + ALPHAiHolland[i-1] + 
               		"&" + ALPHAiRom[i-1] +
               		"&" + ALPHAiFinner[i-1] +
               		"&" + ((i==(algoritmos.size()-1))?(0.05):(ALPHA2Li)) + "\\\\");
           		Pi[i-1] = 2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE));
	    	}
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}");
        
	    
	    /*Compute the rejected hypotheses for each test*/
	    
        System.out.println("Bonferroni-Dunn's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)(algoritmos.size()-1)+"$.\n\n");
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (Pi[i] > ALPHAiHolm[i]) {	    		
	    		System.out.println("Holm's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (Pi[i] <= ALPHAiHolm[i]) {	    		
	    		System.out.println("Hochberg's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    otro = true;
	    for (j=algoritmos.size()-1; j>0 && otro; j--) {
	    	otro = false;
	    	for (k=1; k<=j && !otro; k++) {
	    		if (Pi[algoritmos.size()-1-j+k-1] <= 0.05*(double)k/(double)j) {
	    			otro = true;
	    		}
	    	}
	    }
	    if (otro == true) {
	    	System.out.println("Hommel's procedure rejects all hypotheses.\n\n");
	    } else {
	    	j++;
	    	System.out.println("Hommel's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)j+"$.\n\n");
	    }
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (Pi[i] > ALPHAiHolland[i]) {	    		
	    		System.out.println("Holland's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolland[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (Pi[i] <= ALPHAiRom[i]) {	    		
	    		System.out.println("Rom's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiRom[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }	    

	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (Pi[i] > ALPHAiFinner[i]) {	    		
	    		System.out.println("Finner's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiFinner[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }
	    
	    if (Pi[algoritmos.size()-2] < 0.05) {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+0.05+"$.\n\n");
	    } else {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+ALPHA2Li+"$.\n\n");	    	
	    }

	    System.out.println("\n\\newpage\n");

    
	    /** USING ALIGNED FRIEDMAN TEST *******************************************************************************************/
	    
	    SE = Math.sqrt((double)algoritmos.size()*((double)datasets.size()*(double)algoritmos.size()+1)/6.0);
	    vistos = new boolean[algoritmos.size()];
	    rankingRef = 0.0;
	    Arrays.fill(vistos,false);
	    for (i=0; i<algoritmos.size();i++) {
	    	for (j=0;vistos[j]==true;j++);
	    	pos = j;
	    	maxVal = RjAR[j];
	    	minVal = RjAR[j];
	    	for (j=j+1;j<algoritmos.size();j++) {
	    		if (i > 1) {
	    			if (vistos[j] == false && RjAR[j] > maxVal) {
	    				pos = j;
	    				maxVal = RjAR[j];
	    			}
	    		} else if (i == 1) {
	    			if (vistos[j] == false && RjAR[j] > maxVal) {
	    				pos = j;
	    				maxVal = RjAR[j];
	    			}	    			
	    			if (vistos[j] == false && RjAR[j] < minVal) {
	    				minVal = RjAR[j];
	    			}	    			
	    		} else {
	    			if (vistos[j] == false && RjAR[j] < maxVal) {
	    				pos = j;
	    				maxVal = RjAR[j];
	    			}
	    		}
	    	}
	    	vistos[pos] = true;
	    	if (i==1) {
	    		diffMax = minVal - rankingRef;
		    	PmAR = 2*CDF_Normal.normp((-1)*Math.abs((diffMax)/SE));
	    		ALPHA2Li = (1 - PmAR) / (1 - 0.05) * 0.05;
	    	}
	    	if (i==0) {
	    		rankingRef = maxVal;
                System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Holm / Hochberg / Holland / Rom / Finner / Li Table for $\\alpha=0.05$ (ALIGNED FRIEDMAN)}\n" +
               		"\\begin{tabular}{ccccccccc}\n" +
               		"$i$&algorithm&$z=(R_0 - R_i)/SE$&$p$&Holm/Hochberg/Hommel&Holland&Rom&Finner&Li\\\\\n\\hline");
	    	} else {
	    		ALPHAiHolm[i-1] = 0.05/((double)algoritmos.size()-(double)i);
	    		ALPHAiHolland[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/((double)algoritmos.size()-(double)i)));
	    		ALPHAiFinner[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/(((double)algoritmos.size()-1)/(double)i)));
	    		ordenAlgoritmosAF[i-1] = new String ((String)algoritmos.elementAt(pos));
	    		
                System.out.println((algoritmos.size()-i) + "&" + algoritmos.elementAt(pos) + "&" +
               		Math.abs((rankingRef-maxVal)/SE) + "&" +
               		2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE)) + 
               		"&" + ALPHAiHolm[i-1] +
               		"&" + ALPHAiHolland[i-1] + 
               		"&" + ALPHAiRom[i-1] +
               		"&" + ALPHAiFinner[i-1] +
               		"&" + ((i==(algoritmos.size()-1))?(0.05):(ALPHA2Li)) + "\\\\");
           		PiAR[i-1] = 2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE));
	    	}
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}");
        
	    
	    /*Compute the rejected hypotheses for each test*/
	    
        System.out.println("Bonferroni-Dunn's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)(algoritmos.size()-1)+"$.\n\n");
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiAR[i] > ALPHAiHolm[i]) {	    		
	    		System.out.println("Holm's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (PiAR[i] <= ALPHAiHolm[i]) {	    		
	    		System.out.println("Hochberg's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    otro = true;
	    for (j=algoritmos.size()-1; j>0 && otro; j--) {
	    	otro = false;
	    	for (k=1; k<=j && !otro; k++) {
	    		if (PiAR[algoritmos.size()-1-j+k-1] <= 0.05*(double)k/(double)j) {
	    			otro = true;
	    		}
	    	}
	    }
	    if (otro == true) {
	    	System.out.println("Hommel's procedure rejects all hypotheses.\n\n");
	    } else {
	    	j++;
	    	System.out.println("Hommel's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)j+"$.\n\n");
	    }
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiAR[i] > ALPHAiHolland[i]) {	    		
	    		System.out.println("Holland's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolland[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (PiAR[i] <= ALPHAiRom[i]) {	    		
	    		System.out.println("Rom's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiRom[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }	    

	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiAR[i] > ALPHAiFinner[i]) {	    		
	    		System.out.println("Finner's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiFinner[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }
	    
	    if (PiAR[algoritmos.size()-2] < 0.05) {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+0.05+"$.\n\n");
	    } else {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+ALPHA2Li+"$.\n\n");	    	
	    }

	    System.out.println("\n\\newpage\n");

	    /** USING QUADE TEST **********************************************************************************************/
	    
	    SE = Math.sqrt(((double)algoritmos.size()*((double)algoritmos.size()+1)*((double)algoritmos.size()-1)*((double)datasets.size()*2+1))/(18.0*(double)datasets.size()*((double)datasets.size()+1)));
	    vistos = new boolean[algoritmos.size()];
	    rankingRef = 0.0;
	    Arrays.fill(vistos,false);
	    for (i=0; i<algoritmos.size();i++) {
	    	for (j=0;vistos[j]==true;j++);
	    	pos = j;
	    	maxVal = SMj[j];
	    	minVal = SMj[j];
	    	for (j=j+1;j<algoritmos.size();j++) {
	    		if (i > 1) {
	    			if (vistos[j] == false && SMj[j] > maxVal) {
	    				pos = j;
	    				maxVal = SMj[j];
	    			}
	    		} else if (i == 1) {
	    			if (vistos[j] == false && SMj[j] > maxVal) {
	    				pos = j;
	    				maxVal = SMj[j];
	    			}	    			
	    			if (vistos[j] == false && SMj[j] < minVal) {
	    				minVal = SMj[j];
	    			}	    			
	    		} else {
	    			if (vistos[j] == false && SMj[j] < maxVal) {
	    				pos = j;
	    				maxVal = SMj[j];
	    			}
	    		}
	    	}
	    	vistos[pos] = true;
	    	if (i==1) {
	    		diffMax = minVal - rankingRef;
		    	PmQ = 2*CDF_Normal.normp((-1)*Math.abs((diffMax)/SE));
	    		ALPHA2Li = (1 - PmQ) / (1 - 0.05) * 0.05;
	    	}
	    	if (i==0) {
	    		rankingRef = maxVal;
                System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Holm / Hochberg / Holland / Rom / Finner / Li Table for $\\alpha=0.05$ (QUADE)}\n" +
               		"\\begin{tabular}{ccccccccc}\n" +
               		"$i$&algorithm&$z=(R_0 - R_i)/SE$&$p$&Holm/Hochberg/Hommel&Holland&Rom&Finner&Li\\\\\n\\hline");
	    	} else {
	    		ALPHAiHolm[i-1] = 0.05/((double)algoritmos.size()-(double)i);
	    		ALPHAiHolland[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/((double)algoritmos.size()-(double)i)));
	    		ALPHAiFinner[i-1] = 1.0 - Math.pow((1.0 - 0.05),(1.0/(((double)algoritmos.size()-1)/(double)i)));
	    		ordenAlgoritmosQ[i-1] = new String ((String)algoritmos.elementAt(pos));
	    		
                System.out.println((algoritmos.size()-i) + "&" + algoritmos.elementAt(pos) + "&" +
               		Math.abs((rankingRef-maxVal)/SE) + "&" +
               		2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE)) + 
               		"&" + ALPHAiHolm[i-1] +
               		"&" + ALPHAiHolland[i-1] + 
               		"&" + ALPHAiRom[i-1] +
               		"&" + ALPHAiFinner[i-1] +
               		"&" + ((i==(algoritmos.size()-1))?(0.05):(ALPHA2Li)) + "\\\\");
           		PiQ[i-1] = 2*CDF_Normal.normp((-1)*Math.abs((rankingRef-maxVal)/SE));
	    	}
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}");
        
	    
	    /*Compute the rejected hypotheses for each test*/
	    
        System.out.println("Bonferroni-Dunn's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)(algoritmos.size()-1)+"$.\n\n");
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiQ[i] > ALPHAiHolm[i]) {	    		
	    		System.out.println("Holm's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (PiQ[i] <= ALPHAiHolm[i]) {	    		
	    		System.out.println("Hochberg's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolm[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    otro = true;
	    for (j=algoritmos.size()-1; j>0 && otro; j--) {
	    	otro = false;
	    	for (k=1; k<=j && !otro; k++) {
	    		if (PiQ[algoritmos.size()-1-j+k-1] <= 0.05*(double)k/(double)j) {
	    			otro = true;
	    		}
	    	}
	    }
	    if (otro == true) {
	    	System.out.println("Hommel's procedure rejects all hypotheses.\n\n");
	    } else {
	    	j++;
	    	System.out.println("Hommel's procedure rejects those hypotheses that have a p-value $\\le"+0.05/(double)j+"$.\n\n");
	    }
	    
	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiQ[i] > ALPHAiHolland[i]) {	    		
	    		System.out.println("Holland's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiHolland[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }

	    parar = false;
	    for (i=algoritmos.size()-2; i>=0 && !parar; i--) {
	    	if (PiQ[i] <= ALPHAiRom[i]) {	    		
	    		System.out.println("Rom's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiRom[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }	    

	    parar = false;
	    for (i=0; i<algoritmos.size()-1 && !parar; i++) {
	    	if (PiQ[i] > ALPHAiFinner[i]) {	    		
	    		System.out.println("Finner's procedure rejects those hypotheses that have a p-value $\\le"+ALPHAiFinner[i]+"$.\n\n");
	    		parar = true;
	    	}
	    }
	    
	    if (PiQ[algoritmos.size()-2] < 0.05) {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+0.05+"$.\n\n");
	    } else {
	    	System.out.println("Li's procedure rejects those hypotheses that have a p-value $\\le"+ALPHA2Li+"$.\n\n");	    	
	    }

	    System.out.println("\n\\newpage\n");

	    
	    
	    /************ ADJUSTED P-VALUES IN 1xN **************************************************************************/
	    
	    
	    /** FRIEDMAN *****************************************************************************************************/

	    adjustedP = new double[algoritmos.size()-1][8];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][0] = Pi[i] * (double)(algoritmos.size()-1);
	    	adjustedP[i][1] = Pi[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][2] = Pi[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][4] = 1.0 - Math.pow((1.0 - Pi[i]),((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][5] = Pi[i] * adjustedRom[i];
	    	adjustedP[i][6] = 1.0 - Math.pow((1.0 - Pi[i]),((double)(algoritmos.size()-1))/(i+1));
	    	adjustedP[i][7] = Pi[i] / (Pi[i] + 1 - Pm);
	    }
	    
	    for (i=1; i<adjustedP.length; i++) {
	    	if (adjustedP[i][1] < adjustedP[i-1][1])
	    		adjustedP[i][1] = adjustedP[i-1][1];
	    	if (adjustedP[i][4] < adjustedP[i-1][4])
	    		adjustedP[i][4] = adjustedP[i-1][4];
	    	if (adjustedP[i][6] < adjustedP[i-1][6])
	    		adjustedP[i][6] = adjustedP[i-1][6];
	    }
	    for (i=adjustedP.length-2; i>=0; i--) {
	    	if (adjustedP[i][2] > adjustedP[i+1][2])
	    		adjustedP[i][2] = adjustedP[i+1][2];
	    	if (adjustedP[i][5] > adjustedP[i+1][5])
	    		adjustedP[i][5] = adjustedP[i+1][5];
	    }
	    
	    /*Algoritmo que calcula los valores p ajustados para Hommel*/
	    Ci= new double[adjustedP.length+1];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][3] = Pi[i];
	    }
	    for (m=adjustedP.length; m>1; m--) {	    	
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    			Ci[i] = ((double)m*Pi[i-1])/((double)(m+i-adjustedP.length));
	    	}
	    	min = Double.POSITIVE_INFINITY;
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (Ci[i] < min)
	    			min = Ci[i];
	    	}
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (adjustedP[i-1][3] < min)
	    			adjustedP[i-1][3] = min;
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		Ci[i] = Math.min(min, (double)m * Pi[i-1]);
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		if (adjustedP[i-1][3] < Ci[i])
	    			adjustedP[i-1][3] = Ci[i];
	    	}
	    }
	    
        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (FRIEDMAN)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Bonf}$&$p_{Holm}$&$p_{Hoch}$&$p_{Homm}$\\\\\n\\hline");
	    for (i=0; i<Pi.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosF[i] + "&" + Pi[i] +
            		"&" + adjustedP[i][0] +
               		"&" + adjustedP[i][1] +
               		"&" + adjustedP[i][2] +
               		"&" + adjustedP[i][3] +
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");

        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (FRIEDMAN)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Holl}$&$p_{Rom}$&$p_{Finn}$&$p_{Li}$\\\\\n\\hline");
	    for (i=0; i<Pi.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosF[i] + "&" + Pi[i] +
               		"&" + adjustedP[i][4] + 
               		"&" + adjustedP[i][5] + 
               		"&" + adjustedP[i][6] + 
               		"&" + adjustedP[i][7] + 
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");


	    System.out.println("\n\\newpage\n");

	    /** ALIGNED FRIEDMAN *****************************************************************************************************/

	    adjustedP = new double[algoritmos.size()-1][8];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][0] = PiAR[i] * (double)(algoritmos.size()-1);
	    	adjustedP[i][1] = PiAR[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][2] = PiAR[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][4] = 1.0 - Math.pow((1.0 - PiAR[i]),((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][5] = PiAR[i] * adjustedRom[i];
	    	adjustedP[i][6] = 1.0 - Math.pow((1.0 - PiAR[i]),((double)(algoritmos.size()-1))/(i+1));
	    	adjustedP[i][7] = PiAR[i] / (PiAR[i] + 1 - PmAR);
	    }
	    
	    for (i=1; i<adjustedP.length; i++) {
	    	if (adjustedP[i][1] < adjustedP[i-1][1])
	    		adjustedP[i][1] = adjustedP[i-1][1];
	    	if (adjustedP[i][4] < adjustedP[i-1][4])
	    		adjustedP[i][4] = adjustedP[i-1][4];
	    	if (adjustedP[i][6] < adjustedP[i-1][6])
	    		adjustedP[i][6] = adjustedP[i-1][6];
	    }
	    for (i=adjustedP.length-2; i>=0; i--) {
	    	if (adjustedP[i][2] > adjustedP[i+1][2])
	    		adjustedP[i][2] = adjustedP[i+1][2];
	    	if (adjustedP[i][5] > adjustedP[i+1][5])
	    		adjustedP[i][5] = adjustedP[i+1][5];
	    }
	    
	    /*Algoritmo que calcula los valores p ajustados para Hommel*/
	    Ci= new double[adjustedP.length+1];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][3] = PiAR[i];
	    }
	    for (m=adjustedP.length; m>1; m--) {	    	
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    			Ci[i] = ((double)m*PiAR[i-1])/((double)(m+i-adjustedP.length));
	    	}
	    	min = Double.POSITIVE_INFINITY;
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (Ci[i] < min)
	    			min = Ci[i];
	    	}
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (adjustedP[i-1][3] < min)
	    			adjustedP[i-1][3] = min;
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		Ci[i] = Math.min(min, (double)m * PiAR[i-1]);
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		if (adjustedP[i-1][3] < Ci[i])
	    			adjustedP[i-1][3] = Ci[i];
	    	}
	    }
	    
        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (ALIGNED FRIEDMAN)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Bonf}$&$p_{Holm}$&$p_{Hoch}$&$p_{Homm}$\\\\\n\\hline");
	    for (i=0; i<PiAR.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosAF[i] + "&" + PiAR[i] +
            		"&" + adjustedP[i][0] +
               		"&" + adjustedP[i][1] +
               		"&" + adjustedP[i][2] +
               		"&" + adjustedP[i][3] +
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");

        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (ALIGNED FRIEDMAN)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Holl}$&$p_{Rom}$&$p_{Finn}$&$p_{Li}$\\\\\n\\hline");
	    for (i=0; i<PiAR.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosAF[i] + "&" + PiAR[i] +
               		"&" + adjustedP[i][4] + 
               		"&" + adjustedP[i][5] + 
               		"&" + adjustedP[i][6] + 
               		"&" + adjustedP[i][7] + 
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");

	    System.out.println("\n\\newpage\n");
	    
	    /** QUADE *****************************************************************************************************/

	    adjustedP = new double[algoritmos.size()-1][8];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][0] = PiQ[i] * (double)(algoritmos.size()-1);
	    	adjustedP[i][1] = PiQ[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][2] = PiQ[i] * (((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][4] = 1.0 - Math.pow((1.0 - PiQ[i]),((double)(algoritmos.size()-1))-i);
	    	adjustedP[i][5] = PiQ[i] * adjustedRom[i];
	    	adjustedP[i][6] = 1.0 - Math.pow((1.0 - PiQ[i]),((double)(algoritmos.size()-1))/(i+1));
	    	adjustedP[i][7] = PiQ[i] / (PiQ[i] + 1 - PmQ);
	    }
	    
	    for (i=1; i<adjustedP.length; i++) {
	    	if (adjustedP[i][1] < adjustedP[i-1][1])
	    		adjustedP[i][1] = adjustedP[i-1][1];
	    	if (adjustedP[i][4] < adjustedP[i-1][4])
	    		adjustedP[i][4] = adjustedP[i-1][4];
	    	if (adjustedP[i][6] < adjustedP[i-1][6])
	    		adjustedP[i][6] = adjustedP[i-1][6];
	    }
	    for (i=adjustedP.length-2; i>=0; i--) {
	    	if (adjustedP[i][2] > adjustedP[i+1][2])
	    		adjustedP[i][2] = adjustedP[i+1][2];
	    	if (adjustedP[i][5] > adjustedP[i+1][5])
	    		adjustedP[i][5] = adjustedP[i+1][5];
	    }
	    
	    /*Algoritmo que calcula los valores p ajustados para Hommel*/
	    Ci= new double[adjustedP.length+1];
	    for (i=0; i<adjustedP.length; i++) {
	    	adjustedP[i][3] = PiQ[i];
	    }
	    for (m=adjustedP.length; m>1; m--) {	    	
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    			Ci[i] = ((double)m*PiQ[i-1])/((double)(m+i-adjustedP.length));
	    	}
	    	min = Double.POSITIVE_INFINITY;
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (Ci[i] < min)
	    			min = Ci[i];
	    	}
	    	for (i=adjustedP.length; i> (adjustedP.length-m); i--) {
	    		if (adjustedP[i-1][3] < min)
	    			adjustedP[i-1][3] = min;
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		Ci[i] = Math.min(min, (double)m * PiQ[i-1]);
	    	}
	    	for (i=1; i<=(adjustedP.length-m); i++) {
	    		if (adjustedP[i-1][3] < Ci[i])
	    			adjustedP[i-1][3] = Ci[i];
	    	}
	    }
	    
        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (QUADE)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Bonf}$&$p_{Holm}$&$p_{Hoch}$&$p_{Homm}$\\\\\n\\hline");
	    for (i=0; i<PiQ.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosQ[i] + "&" + PiQ[i] +
            		"&" + adjustedP[i][0] +
               		"&" + adjustedP[i][1] +
               		"&" + adjustedP[i][2] +
               		"&" + adjustedP[i][3] +
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");

        System.out.println("\\begin{table}[!htp]\n\\centering\\scriptsize\n\\caption{Adjusted $p$-values (QUADE)}\n" +
           		"\\begin{tabular}{ccccccc}\n" +
           		"i&algorithm&unadjusted $p$&$p_{Holl}$&$p_{Rom}$&$p_{Finn}$&$p_{Li}$\\\\\n\\hline");
	    for (i=0; i<PiQ.length; i++) {	    	
            System.out.println((i+1) + "&" + ordenAlgoritmosQ[i] + "&" + PiQ[i] +
               		"&" + adjustedP[i][4] + 
               		"&" + adjustedP[i][5] + 
               		"&" + adjustedP[i][6] + 
               		"&" + adjustedP[i][7] + 
               		"\\\\");
	    }
	    System.out.println("\\hline\n" + "\\end{tabular}\n" + "\\end{table}\n");

	    System.out.println("\\end{landscape}\\end{document}");  
	    
	}  	
	    
	
	public static void calcularROM(double alpha, double vector[], double adjusted[]) {
		
		int i, j;
		int m;
		double suma1, suma2;
		
		m = vector.length;
		
		vector[m-1] = alpha;
		vector[m-2] = alpha/2.0;
		adjusted[m-1] = 1;
		adjusted[m-2] = 2;
		
		for (i=3; i<=m; i++) {
			suma1 = suma2 = 0;
			for (j=1;j<(i-1);j++) {
				suma1 += Math.pow(alpha, (double)j);
			}
			for (j=1;j<(i-2);j++){
				suma2 += combinatoria(j,i)*Math.pow(vector[m-j-1], (double)(i-j));
			}
			vector[m-i] = (suma1-suma2)/(double)i;
			adjusted[m-i] = vector[m-1] / vector[m-i];
		}		
		
	}



	public static double combinatoria (int m, int n) {

		double result = 1;
		int i;
		
		if (n >= m) {
			for (i=1; i<=m; i++)
				result *= (double)(n-m+i)/(double)i;
		} else {
			result = 0;
		}
		return result;
	}
	
	
	private static double ChiSq(double x, int n) {
        if (n == 1 & x > 1000) {
            return 0;
        }
        if (x > 1000 | n > 1000) {
            double q = ChiSq((x - n) * (x - n) / (2 * n), 1) / 2;
            if (x > n) {
                return q;
            }
            {
                return 1 - q;
            }
        }
        double p = Math.exp( -0.5 * x);
        if ((n % 2) == 1) {
            p = p * Math.sqrt(2 * x / Math.PI);
        }
        double k = n;
        while (k >= 2) {
            p = p * x / k;
            k = k - 2;
        }
        double t = p;
        double a = n;
        while (t > 0.0000000001 * p) {
            a = a + 2;
            t = t * x / a;
            p = p + t;
        }
        return 1 - p;
    }

    private static double FishF(double f, int n1, int n2) {
        double x = n2 / (n1 * f + n2);
        if ((n1 % 2) == 0) {
            return StatCom(1 - x, n2, n1 + n2 - 4, n2 - 2) * Math.pow(x, n2 / 2.0);
        }
        if ((n2 % 2) == 0) {
            return 1 -
                    StatCom(x, n1, n1 + n2 - 4, n1 - 2) *
                    Math.pow(1 - x, n1 / 2.0);
        }
        double th = Math.atan(Math.sqrt(n1 * f / (1.0*n2)));
        double a = th / (Math.PI / 2.0);
        double sth = Math.sin(th);
        double cth = Math.cos(th);
        if (n2 > 1) {
            a = a +
                sth * cth * StatCom(cth * cth, 2, n2 - 3, -1) / (Math.PI / 2.0);
        }
        if (n1 == 1) {
            return 1 - a;
        }
        double c = 4 * StatCom(sth * sth, n2 + 1, n1 + n2 - 4, n2 - 2) * sth *
                   Math.pow(cth, n2) / Math.PI;
        if (n2 == 1) {
            return 1 - a + c / 2.0;
        }
        int k = 2;
        while (k <= (n2 - 1) / 2.0) {
            c = c * k / (k - .5);
            k = k + 1;
        }
        return 1 - a + c;
    }

    private static double StatCom(double q, int i, int j, int b) {
        double zz = 1;
        double z = zz;
        int k = i;
        while (k <= j) {
            zz = zz * q * k / (k - b);
            z = z + zz;
            k = k + 2;
        }
        return z;
    }
	
}

