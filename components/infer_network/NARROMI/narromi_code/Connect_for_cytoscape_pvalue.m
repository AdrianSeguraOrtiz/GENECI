 
% Turn the G, Gval,Gsig into a table with four column,first and second
% column are gene pairs interaction, third column is interaction strenghness and forth
% comlumn is significance/p-value.

function [table]=Connect_for_cytoscape_pvalue(G,Gval,Gsig,name_TF,name_gene)

[row,col,val]=find(G~=0);
AA=[row,col,val];
AA_first=AA(:,1);
AA_second=AA(:,2);

n=size(AA,1);
 AA_first_1=cell(1,n);AA_second_1=cell(1,n);AA_third_1=cell(1,n);AA_forth_1=cell(1,n);
% AA_second_1=[];
for i=1:n
    AA_first_1(i)=name_TF(AA_first(i));
    AA_second_1(i)=name_gene(AA_second(i));
    AA_third_1(i)=num2cell(Gval(AA_first(i),AA_second(i)));
    AA_forth_1(i)=num2cell(Gsig(AA_first(i),AA_second(i)));
end
A_first=AA_first_1';
A_second=AA_second_1';
A_third=AA_third_1';
A_forth=AA_forth_1';

% A_third=num2cell(A_third);
% A_forth=num2cell(A_forth);
table=[A_first,A_second,A_third,A_forth];

end


