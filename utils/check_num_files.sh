for network_folder in ../template/*
do

    filename=$(basename $network_folder)
    exp_file="$network_folder/$filename.csv"
    lines=$(wc -l < $exp_file)
    num_files=$(ls $network_folder/lists | wc -l)

    if [ $lines -lt 25 ]
    then
        if [ $num_files != 26 ]
        then
            echo "0-25: $filename $num_files"
        fi
    fi

    if [ $lines -gt 25 ] && [ $lines -lt 110 ]
    then
        if [ $num_files != 25 ]
        then
            echo "25-110: $filename $num_files"
        fi
    fi

    if [ $lines -gt 110 ] && [ $lines -lt 250 ]
    then
        if [ $num_files != 20 ]
        then
            echo "110-250: $filename $num_files"
        fi
    fi

    if [ $lines -gt 250 ] && [ $lines -lt 2000 ]
    then
        if [ $num_files != 13 ]
        then
            echo "250-2000: $filename $num_files"
        fi
    fi

    if [ $lines -gt 2000 ]
    then
        if [ $num_files != 11 ]
        then
            echo "2000-...: $filename $num_files"
        fi
    fi
done

