set -e

# create dir if not exists

# rm
rm -rf ./data/processed/q1/*
rm -rf ./data/processed/q2/*
rm -rf ./data/processed/q3/*
rm -rf ./data/processed/q4/*

mkdir -p ./data/raw
mkdir -p ./data/processed/q1
mkdir -p ./data/processed/q2
mkdir -p ./data/processed/q3
mkdir -p ./data/processed/q4

unzip ./data/raw/2020q1.zip -d ./data/processed/q1/ 
unzip ./data/raw/2020q2.zip -d ./data/processed/q2/
unzip ./data/raw/2020q3.zip -d ./data/processed/q3/
unzip ./data/raw/2020q4.zip -d ./data/processed/q4/

# for each quarter, convert TSV to CSV
for quarter in q1 q2 q3 q4; do
    cd ./data/processed/${quarter}/
    for file in ./*.txt; do
        python3 -c "import csv, sys; csv.writer(sys.stdout).writerows(csv.reader(sys.stdin, delimiter='\t'))" < "${file}" > "${file%.txt}.csv"
    done
    cd ../../../
done


# merge all num.csv files into one, exclude the header rows if not the first file
mkdir -p ./data/processed/merged
output_file=./data/processed/merged/num_2020.csv
first_file=true
for quarter in q1; do
    for file in ./data/processed/${quarter}/num.csv; do
        if [ "$first_file" = true ]; then
            cat "${file}" >> "${output_file}"
            first_file=false
        else
            tail -n +2 "${file}" >> "${output_file}"
        fi
    done
done
