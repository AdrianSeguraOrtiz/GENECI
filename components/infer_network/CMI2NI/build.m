res = compiler.build.standaloneApplication('cmi2ni_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_cmi2ni','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit