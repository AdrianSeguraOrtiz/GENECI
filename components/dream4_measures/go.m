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

%% predictions to be evaluated
testfile = './inferred_networks/dream4_010_05_exp/ea_consensus/final_list.csv';

%% the gold standard that corresponds to the testfile
goldfile = './evaluate/DREAM4/INPUT/gold_standards/10/DREAM4_GoldStandard_InSilico_Size10_5.tsv';

%% precomputed probability density that corresponds to the testfile
pdffile = './evaluate/DREAM4/INPUT/probability_densities/pdf_size10_5.mat';

%% load gold standard
gold_data = load_dream_network(goldfile);

%% load predictions
test_data = load_dream_network(testfile);

%% load probability density function
pdf_data = load(pdffile);

%% calculate performance metrics
[aupr auroc prec rec tpr fpr p_auroc p_aupr] = DREAM4_Challenge2_Evaluation(test_data, gold_data, pdf_data);

%% print results
disp(aupr)
disp(auroc)

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
saveas(gcf,'evaluation.png')

