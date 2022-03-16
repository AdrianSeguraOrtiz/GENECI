#!/bin/bash
module load matlab/R2011b
matlab -nodisplay -nosplash -nodesktop -r "run('./go_all_undirected.m');exit;" | tail -n +11
