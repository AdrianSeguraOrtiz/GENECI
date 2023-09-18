# Create Matlab Dockerfile
cd components/infer_network/LOCPCACMI/
matlab -nodisplay -nodesktop -r "run build.m"

# Copy R required script
cp locpcacmi_code/loc-PCA-CMI_pc_cluster.R adriansegura99/geneci_infer-network_locpcacmidocker/loc-PCA-CMI_pc_cluster.R

# Modify for user permissions
cd adriansegura99/geneci_infer-network_locpcacmidocker 
sed -i '4,8d' Dockerfile

# Get binary file path
binaryFile=$(sed '4q;d' Dockerfile | cut -d \" -f 2)
sed -i '4d' Dockerfile

# Add R instalation
cat >> Dockerfile <<- EOM
RUN apt-get update && apt-get install -y \
   r-base \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

# CRAN packages
RUN R -e "install.packages('readr', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('R.matlab', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('Matrix', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('remotes', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('reshape2', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('fdrtool', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('gtools', repos='http://cran.us.r-project.org')"

# Github package
RUN R -e "remotes::install_github('wyguo/RLowPC')"
EOM

# Create entrypoint script
cat > main.sh <<- EOM
Rscript /usr/bin/mlrtapp/loc-PCA-CMI_pc_cluster.R \$1 
$binaryFile tmp/.X11-unix/tmp.mat \$1 \$2
EOM

# Copy R and main script to workdir
cat >> Dockerfile <<- EOM
COPY loc-PCA-CMI_pc_cluster.R /usr/bin/mlrtapp/loc-PCA-CMI_pc_cluster.R
COPY main.sh /usr/bin/mlrtapp/main.sh
ENTRYPOINT ["bash", "/usr/bin/mlrtapp/main.sh"]
EOM

docker build -t adriansegura99/geneci_infer-network_locpcacmi . 
cd ../../../../../