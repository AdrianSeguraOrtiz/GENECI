%
% This function produces the UNDIRECTED DREAM4 scores for a batch of five networks
% (including he overall score for the sub-challenge)
%
% See go_all.m for an exmaple of how to call it.
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

function [ AUROC, ...
	AUPR, ...
	P_AUROC, ...
	P_AUPR, ...
	AUROC_PVAL, ...
	AUPR_PVAL, ...
	AUROC_SCORE, ...
	AUPR_SCORE, ...
	SCORE] = batch_evaluation_undirected(sub_challenge_number)

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% PARAMS

%% pick a number:
%% 	1 for size 10
%%  2 for size 100
%%  3 for size 100 multifactorial
ii = sub_challenge_number;

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% PATHS

%% number of nodes
N_all = [ 10 100 100 ];

% where the gold standards are located
GOLDDIRS = {'../INPUT/gold_standards_undirected/10/' ...
			'../INPUT/gold_standards_undirected/100/' ...
			'../INPUT/gold_standards_undirected/100_multifactorial/'};

%% where the predictions are located
INDIRS = {'../INPUT/my_predictions/10/',...
		  '../INPUT/my_predictions/100/',...
		  '../INPUT/my_predictions/100_multifactorial/'};

%% where the prob densities are located
PDFDIR = '../INPUT/probability_densities_undirected/';
PDF_ROOTS = {'pdf_size10_', 'pdf_size100_', 'pdf_size100_multifactorial_'};

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

N = N_all(ii);
INDIR = INDIRS{ii};
GOLDDIR = GOLDDIRS{ii};
PDF_ROOT = PDF_ROOTS{ii};

files = directory_list(INDIR);

%% for each file
for fi = 1:length(files)

	file = [ INDIR files{fi} ];
	disp([ '  ' files{fi} ])

	%% figure out the name of the network
	if ii<3
		network_name = figure_out_network_name(file);
	else
		network_name = figure_out_network_name(file,3);
	end
	NAMES{fi} = strrep(network_name,'_','\_');

	%% figure out the name of the gold standard
	goldfile = [ GOLDDIR 'DREAM4_GoldStandardUndirected_InSilico_' network_name '.tsv' ];

	%% load gold standard
	gold_data = load_dream_network(goldfile);

	%% load predictions
	test_data = load_dream_network(file);

	%% convert testdata to undirected format
	test_data_undirected = directed_2_undirected_predictions(test_data,N);

	%% fetch the probability density function
	pdffile = [ PDFDIR PDF_ROOT num2str(fi) ];
	pdf_data = load(pdffile);

	%% calculate performance metrics
	[aupr auroc prec rec tpr fpr p_auroc p_aupr] = DREAM4_Challenge2_Evaluation(test_data_undirected, gold_data, pdf_data);

		%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

		%% remember
		AUPR(fi) = aupr;
		AUROC(fi) = auroc;
		P_AUROC(fi) = p_auroc;
		P_AUPR(fi) = p_aupr;
		PREC{fi} = prec;
		REC{fi} = rec;
		TPR{fi} = tpr;
		FPR{fi} = fpr;

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% overall scores
AUROC_SCORE = -mean(log10(P_AUROC));
AUPR_SCORE = -mean(log10(P_AUPR));
AUROC_PVAL = 10.^-AUROC_SCORE;
AUPR_PVAL = 10.^-AUPR_SCORE;
SCORE = 1/2 * (AUROC_SCORE + AUPR_SCORE);

%% show something on screen
%AUROC
%AUPR
%P_AUROC
%P_AUPR
%AUROC_PVAL
%AUPR_PVAL
%AUROC_SCORE
%AUPR_SCORE
%SCORE

