
function [mu_x , SIGMA_x] = VBE( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta )

     [N G] = size( R ) ;
         B = R'*R ;

   SIGMA_x = inv( inv(S_x) + g*B.*( (alfa/beta)*mu_w*(mu_w)' + SIGMA_w ) ) ;
      mu_x = (SIGMA_x)'*( ( g*alfa/beta )*(y)'*R*diag( mu_w ) + (m_x)'*inv(S_x) )' ;

return ;
          
end%function
