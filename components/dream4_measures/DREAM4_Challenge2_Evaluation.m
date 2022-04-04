%
% This function produces the DREAM4 scores for one network.
%
% See go.m for an example of how to call it.
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

function [AUC AUROC prec rec tpr fpr p_auroc p_aupr] = score_prediction(test_data, gold_data, pdf_data)

T = size(gold_data,1);							% Total potential edges n(n-1)
P = sum(gold_data(:,3));						% Positives
N = T-P;										% Negatives
L = size(test_data,1); 							% Length of prediction list

%% append ranks to testdata
test_data(:,4) = 1:size(test_data,1);			% rank (small to large) 	-- used by our algorithm

%% order the edgelist for test the same as the edgelist for gold
gold = gold_data(:,3);		% this is the reference
test = zeros(T,1);			% build this
for k = 1:size(test_data,1)
	
	i = test_data(k,1);
	j = test_data(k,2);
	val = test_data(k,4);
	
	%% find the insertion point
	idx = find(sum((gold_data(:,1:2) == repmat([i j], size(gold_data,1), 1))')'==2);
	if isempty(idx) 
		error('ERROR: Did not find this edge in the gold standard network'); 
	end

	%% insert
	test(idx) = val;
end

%% counters
k=0;
Ak=0;
TPk=0;
FPk=0;

%% Scan through the ranked list of positive predictions.
%% Record if each is a TP or a FP
while(k<L)
	
	k = k+1;

	%% index of the kth predicted edge
	idx = find(test==k);
	
	if gold(idx)
		%% the edge IS present in the gold standard

		%% increment TPk
		TPk = TPk + 1;
		
		%% update area under precision-recall curve
        if(k==1)
            delta=1/P;
        else
            delta=(1-FPk*log(k/(k-1)))/P;
        end
        Ak = Ak + delta;

	else
		%% the edge is NOT present in the gold standard
		
		%% icrement FPk
		FPk = FPk + 1;

		%% do NOT update area under P-R
	end

	%% remember
	rec(k) = TPk/P;
	prec(k) = TPk/k;
	tpr(k) = rec(k);
	fpr(k) = FPk/N;

end

%% Done with the positive predictions.

%% If the number of predictions (L) is less than the total possible edges (T),
%% we assume that they would achieve the accuracy of the null model (random guessing).

TPL=TPk;

%% rho
if L < T
    rh = (P-TPL)/(T-L);
else
    rh = 0;
end

%% recall at L
if L>0
    recL = rec(L);
else
    recL = 0;
end

%% the remaining positives would eventually be predicted
while TPk < P
    k = k + 1;
    TPk = TPk + 1;
    rec(k) = TPk/P;
    if ((rec(k)-recL)*P + L * rh) ~= 0
        prec(k) = rh * P * rec(k)/((rec(k)-recL)*P + L * rh); 
    else
        prec(k) = 0;
    end
    tpr(k) = rec(k);
    FPk = TPk * (1-prec(k))/prec(k);
    fpr(k) = FPk/N;
end

%% update the area under the P-R curve
%% rh = (P-TPk)/(T-L);  % BP: I removed this line because it is an error in logic to redefine this here.
AL = Ak;
if ~isnan(rh) && rh ~= 0 && L ~= 0
    AUC = AL + rh * (1-recL) + rh * (recL - L * rh / P) * log((L * rh + P * (1-recL) )/(L *rh));
elseif(L==0)
    AUC = P/T;
else 
    AUC = Ak;
end

% Integrate area under ROC
lc = fpr(1) * tpr(1) /2;
for n=1:L+P-TPL-1
    lc = lc + (fpr(n+1)+fpr(n)) * (tpr(n+1)-tpr(n)) / 2;
end
AUROC = 1 - lc;


%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% calculate pvals
auroc = AUROC;
aupr = AUC;
p_auroc = probability(pdf_data.auroc_X, pdf_data.auroc_Y, auroc);
p_aupr = probability (pdf_data.aupr_X,  pdf_data.aupr_Y,  aupr);

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%% show plots
%figure(1)
%subplot(2,2,1)
%plot(fpr,tpr)
%title('ROC')
%xlabel('FPR')
%ylabel('TPR')
%subplot(2,2,2)
%plot(rec,prec)
%title('P-R')
%xlabel('Recall')
%ylabel('Precision')

