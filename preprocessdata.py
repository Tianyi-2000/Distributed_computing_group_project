import os

import pandas as pd

print("Starting data preprocessing...")
num_files = [
    "./data/processed/q1/num.csv",
    "./data/processed/q1/pre.csv",
    "./data/processed/q1/sub.csv",
    "./data/processed/q1/tag.csv",
    "./data/processed/q2/num.csv",
    "./data/processed/q2/pre.csv",
    "./data/processed/q2/sub.csv",
    "./data/processed/q2/tag.csv",
    "./data/processed/q3/num.csv",
    "./data/processed/q3/pre.csv",
    "./data/processed/q3/sub.csv",
    "./data/processed/q3/tag.csv",
    "./data/processed/q4/num.csv",
    "./data/processed/q4/pre.csv",
    "./data/processed/q4/sub.csv",
    "./data/processed/q4/tag.csv",
]


for file in num_files:
    df = pd.read_csv(file)
    quarter = file.split("/")[3]
    df["quarter"] = quarter
    df["year"] = 2020
    df.to_csv(file, index=False)

# create merged directory if it doesn't exist


os.makedirs("./data/processed/merged", exist_ok=True)


# merge q1, q2, q3, q4 files into single files
for prefix in ["num", "pre", "sub", "tag"]:
    all_dfs = []
    for quarter in ["q1", "q2", "q3", "q4"]:
        file = f"./data/processed/{quarter}/{prefix}.csv"
        df = pd.read_csv(file)
        all_dfs.append(df)
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(f"./data/processed/merged/{prefix}_2020.csv", index=False)
