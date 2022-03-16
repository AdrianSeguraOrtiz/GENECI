function P = probability(X,Y,x)
% P(X>=x)

dx = X(2)-X(1);
P = sum( double(X>=x) .* Y * dx );
