function plotPosteriors(data,obsTimes,exprMean,exprVar,promState,TSidx,geneidx)
%function
%plotPosteriors(data,obsTimes,exprMean,exprVar,promState,TSidx,geneidx)
%
% Plot modelling results for one gene in one time series.
%
%- data: 1-by-S cell array, where S is the number of perturbation time
%series, containing the observed gene expression levels.
%- obsTimes: 1-by-S cell array containing the observation time points.
%- exprMean: means of gene expressions over time interval [0,N], where N is
%the highest time point.
%- exprVar: variances of gene expressions over [0,N].
%- promState: promoter states over [0,N].
%- TSidx: index of a time series
%- geneidx: index of a gene
%
% data and obsTimes are inputs of function jump3().
% exprMean, exprVar and promState are outputs of function jump3().

m = exprMean{TSidx}(geneidx,:);
c = exprVar(geneidx,:);
q = promState{TSidx}(geneidx,:);
o = obsTimes{TSidx};
d = data{TSidx}(geneidx,:);

nStep = length(m)-1;
t=0:nStep;

v1 = m - sqrt(c);
v2 = m + sqrt(c);

subplot(2,1,1)
hold on
fill([t, t(end:-1:1)],[v1,v2(end:-1:1)], 'b','facecolor',[1 0 0] ,'facealpha', 0.25,'linestyle','no');
plot(t,m,'b','linewidth',2,'color',[1 0 0]);
plot(o,d,'black.','MarkerSize',20)
xlim([0 nStep])
title('Gene expression');

subplot(2,1,2)
plot(t,q,'black','linewidth',2)
axis([0 nStep -0.1 1.1])
xfig = xlabel('time');
set(xfig,'FontSize',12);
title('Promoter state');