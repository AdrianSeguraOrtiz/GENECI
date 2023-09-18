
function [mu_w , SIGMA_w , alfa , beta] = VBM( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta )

    [N G] = size( R ) ;
        B = R'*R ;

  SIGMA_w = inv( g*inv(S_w) + g*B.*( mu_x*(mu_x)' + SIGMA_x ) ) ;    
     mu_w = (SIGMA_w)'*( g*(y)'*R*diag( mu_x ) + g*m_w' )' ; 
     alfa = a + 0.5*( N ) ;
     beta = g*b + 0.5*g*(y)'*y + 0.5*g*(m_w)'*inv( S_w )*m_w - 0.5*(mu_w)'*inv( SIGMA_w )*mu_w ;

return ;

end%function
