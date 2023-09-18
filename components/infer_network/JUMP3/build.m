res = compiler.build.standaloneApplication('jump3_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_jump3','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit