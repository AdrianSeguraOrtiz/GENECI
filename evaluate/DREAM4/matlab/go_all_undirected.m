%
% This script demonstrates how to call the function 
% batch_evaluation_undirected().
%
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

%% pick a number:
%% 	1 for size 10
%%  2 for size 100
%%  3 for size 100 multifactorial
sub_challenge_number = 1;

[ AUROC, ...
	AUPR, ...
	P_AUROC, ...
	P_AUPR, ...
	AUROC_PVAL, ...
	AUPR_PVAL, ...
	AUROC_SCORE, ...
	AUPR_SCORE, ...
	SCORE] = batch_evaluation_undirected(sub_challenge_number)

