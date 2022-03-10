function test_data_undirected = directed_2_undirected_predictions(test_data,N)
%% test data is an edge list ranked from high to low confidence
%% N is the number of nodes in the network

D = sparse(N,N,0);
E = test_data(:,1:2);	%% edgelist
R = 1:size(E,1);		%% rank (low to high)
for k = 1:size(E,1)
	i = E(k,1);
	j = E(k,2);
	r = R(k);
	D(i,j) = r;			%% add link denoted by rank
end

%% take the smallest rank greater than zero as the 
%% undirected rank
count = 0;
for i = 1:N
	for j = (i+1):N		%% upper triangular
		count = count + 1;
		r_ij = D(i,j);
		r_ji = D(j,i);
		if (r_ij > 0) & (r_ji > 0)
 			%% they are both greater than zero
			if r_ij < r_ji
				E_undirected(count,:) = [ i j r_ij ];
			else
				E_undirected(count,:) = [ i j r_ji ];
			end
		elseif r_ij > 0
			E_undirected(count,:) = [ i j r_ij ];
		else
			E_undirected(count,:) = [ i j r_ji ];
		end
	end
end

%% finally, sort the edge list to produce the prediction
R = E_undirected(:,3);		%% ranks
idx = find(R);				%% just the nonzero ranks
E_nonzero_rank = E_undirected(idx,:);
R_nonzero = R(idx);
[ temp myorder ] = sort(R_nonzero);
test_data_undirected = E_nonzero_rank(myorder,:);
