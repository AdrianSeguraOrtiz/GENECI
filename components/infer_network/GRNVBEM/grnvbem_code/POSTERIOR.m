function [p] = POSTERIOR( m_x,SIGMA_x )

   G = length( m_x ) ;
   p_1 = nan(G,1) ;
   p_0 = nan(G,1) ;
   p = nan(G,1) ;
   
   for j = 1:G
    % p( x_i(j)=1 )
      p_1(j) = inv( 2*pi*sqrt( SIGMA_x(j,j) ) )*exp( -inv( 2*SIGMA_x(j,j) )*( ( 1 - m_x(j) )^2 ) ) ; 
    % p( x_i(j)=0 )
      p_0(j) = inv( 2*pi*sqrt( SIGMA_x(j,j) ) )*exp( -inv( 2*SIGMA_x(j,j) )*( ( 0 - m_x(j) )^2 ) ) ; 
    % p( x_i(j)=1 ) normalised
      p(j) = p_1(j)/( p_1(j)+p_0(j) ) ;
   end%for(i)
  
   return ;

end%function
