%
% This script demonstrates how to call the function 
% DREAM4_Challenge2_Evaluation().
%
% Gustavo A. Stolovitzky, Ph.D.
% Adj. Assoc Prof of Biomed Informatics, Columbia Univ
% Mngr, Func Genomics & Sys Biology, IBM  Research
% P.O.Box 218 					Office :  (914) 945-1292
% Yorktown Heights, NY 10598 	Fax     :  (914) 945-4217
% http://www.research.ibm.com/people/g/gustavo
% http://domino.research.ibm.com/comm/research_projects.nsf/pages/fungen.index.html 
% gustavo@us.ibm.com
%
% Robert Prill, Ph.D.
% Postdoctoral Researcher
% Computational Biology Center, IBM Research
% P.O.Box 218
% Yorktown Heights, NY 10598 	
% Office :  914-945-1377
% http://domino.research.ibm.com/comm/research_people.nsf/pages/rjprill.index.html
% rjprill@us.ibm.com
%

clear all

%% number of nodes, needed by directed_2_undirected_predictions()
N = 10;

%% predictions to be evaluated
testfile = '../INPUT/my_predictions/10/DREAM4_Example_InSilico_Size10_1.txt';

%% the gold standard that corresponds to the testfile
goldfile = '../INPUT/gold_standards_undirected/10/DREAM4_GoldStandardUndirected_InSilico_Size10_1.tsv';

%% precomputed probability density that corresponds to the testfile
pdffile = '../INPUT/probability_densities_undirected/pdf_size10_1.mat';

%% load gold standard
gold_data = load_dream_network(goldfile);

%% load predictions
test_data = load_dream_network(testfile);

%% convert testdata to undirected format
test_data_undirected = directed_2_undirected_predictions(test_data,N);

%% load probability density function
pdf_data = load(pdffile);

%% calculate performance metrics
[aupr auroc prec rec tpr fpr p_auroc p_aupr] = DREAM4_Challenge2_Evaluation(test_data_undirected, gold_data, pdf_data);

%% show plots
figure(1)
subplot(2,2,1)
plot(fpr,tpr)
title('ROC')
xlabel('FPR')
ylabel('TPR')
subplot(2,2,2)
plot(rec,prec)
title('P-R')
xlabel('Recall')
ylabel('Precision')

