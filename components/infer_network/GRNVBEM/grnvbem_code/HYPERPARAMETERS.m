%% DESCRIPTION OF THE INPUT VARIABLES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% Performance
% ===========
% <0>  model, the name of the linear approach to use. Any of the next
%      strings 'AR1' or 'AR1MA1'.
% <1>  cl, the VBEM convergence limit. A real number in (0,1) specifing the
%      convergence limit the at wich the converge criteria should stop. The
%      convergence criterion is calculated as the relative difference of
%      the lower-bound between two consecutive iterations of the VBEM. It
%      is higly recommended to use a value lower than one. By default, we
%      use: cl = 1e-10 . To speed up the execution for higher datasets, use
%      a higher value.
%
% Data
% ====
% <2>  Y, gene expression time-series data. A Gx(N+1) real matrix with the
%      fold change of G genes measured at (N+1) time points.
% <3>  i, the gene of interest. Index of the row at which the gene of
%      interest is in the matrix Y.
%
% Priors
% ======
% <4>  m_x, mean of x. A Gx1 real vector with the mean of the probability
%      of x, the variable describing the network topology of the gene of
%      inerest. To set this prior with using objective knowledge, set it as
%      m_x(j)=1 when you are completly sure that the j-th gene is a parent
%      of the current gene and m_x(j)=0 oterwise. When there is no prior
%      knowledge, a subjective prior is set by using: m_x=0.5*ones(G,1). 
% <5>  S_x, the covariance matrix, a GxG real matrix, of variable x.
%      When there is no prior knowledge, a subjective prior is set by
%      using: S_x=0.25*ones(G,1).
% <6>  m_x, mean of w. A Gx1 real vector with the mean of the probability
%      of w, the variable describing the weights of the GRN of the gene of
%      interest. When there is no prior knowledge, a subjective prior is
%      set by using: m_w=zeros(G,1).
% <7>  S_W, the covariance matrix, a GxG real matrix, of variable w. When
%      there is no prior knowledge, a subjective prior is set by using
%      S_w=ones(G,1).
% <8>  a, the scale hyperparameter that models the spreadness of the
%      variance of the noise. When there is no prior knowledge, a
%      subjective prior is set by using a=2.
% <9>  b, the shape hyperparameter that shifts the mode of prior of the
%      variance of the noise. A common practice to not to care about this
%      hyperparameter is to set it up as b=1/a.

%% MAIN FUNCTION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta ] = HYPERPARAMETERS( model , cl , Y , i , m_x , S_x , m_w , S_w , a , b )

 % Variables initialization % % % % % % % % % % % % % % % % % % % % % % % %
   F_old = 0 ;
   F_new = 1 ;
       y = Y(i,2:end)' ;
       N = size( y,1 ) ;
       T = eye(N,N+1) ;
       R = T*Y' ;
       counter = 0 ;
 % Posterior hyperpameters initialization % % % % % % % % % % % % % % % % %
      mu_x = m_x ;
   SIGMA_x = S_x ;
       mu_w = m_w ;
   SIGMA_w = S_w ;
      alfa = b ;
      beta = a ;
      if strcmp(model,'AR1MA1')
          toggle = 1 ;
      else
          toggle = 0 ;
      end%if
 % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % %

 while ( abs( (F_old-F_new)/F_old ) > cl )
     
   counter = counter + 1 ;
 % Updating the lower bound % % % % % % % % % % % % % % % % % % % % % % % %
   F_old = F_new ;
 % Hyperparameters learning rules % % % % % % % % % % % % % % % % % % % % %
   g = inv( 1 + toggle*(mu_x.^2)'*(mu_w.^2) ) ;
   [mu_x  , SIGMA_x] = VBE( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta ) ;
   g = inv( 1 + toggle*(mu_x.^2)'*(mu_w.^2) ) ;
   [mu_w , SIGMA_w , alfa , beta] = VBM( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta ) ;
   g = inv( 1 + toggle*(mu_x.^2)'*(mu_w.^2) ) ;
   F_new = LOWERBOUND( y , R , g , m_x , S_x , m_w , S_w , a , b , mu_x , SIGMA_x , mu_w , SIGMA_w , alfa , beta ) ;
 % % % % % % % % % % % % % % % % % % % % % % %

 end%while
 
 disp( strjoin( {'  VBEM converges after',num2str(counter),'iteractions'} ) ) ;
 
 return ;

end%function
