
function [ F ] = LOWERBOUND( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta )

   [N G] = size( R ) ;
       B = R'*R ;
       A = B.*( mu_x*(mu_x)' + SIGMA_x ) ;
         
   F1 = 0.5*( log( det(SIGMA_x) ) - log( det( S_x ) ) + G - (mu_x - m_x)'*inv( S_x )*(mu_x - m_x) - trace( inv(S_x)*SIGMA_x ) ) ;
   F2 = 0.5*( log( det(SIGMA_w) ) - log( det(g*S_w) ) + G - (mu_w - m_w)'*inv( S_w )*(mu_w - m_w)*g*alfa/beta - trace( g*inv(S_w)*SIGMA_w ) ) ;
   F3 = 0.5*alfa/beta*( -g*(y'*y) + 2*g*y'*R*diag(mu_x)*mu_w - g*mu_w'*A*mu_w + 2*(beta - g*b) )  ;
   F4 = 0.5*( -N*log(2*pi) + N*log(g) + 2*(alfa - a - N/2)*( log(beta) - psi(alfa) ) - g*trace(A*SIGMA_w) - alfa*log( beta ) -a*log( g*b ) + gammaln( a ) - gammaln( alfa ) ) ;

   F = F1 + F2 + F3 + F4 ;

return ;

end%function
