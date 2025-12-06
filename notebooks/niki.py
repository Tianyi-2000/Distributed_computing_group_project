#!/usr/bin/env python
# coding: utf-8

# ## Niki Naderzad
# ## Group 3
# ## Group Assignment Task 3

# In[ ]:


import argparse
import os

from pyspark.sql import SparkSession

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--is-local",
    type=str,
    default="true",
    help="Whether running in local mode",
)
args, unknown = parser.parse_known_args()
is_local = args.is_local.lower() == "true"

print(f"Is local environment: {is_local}")

# Build SparkSession with conditional configuration
if is_local:
    adc_path = os.path.expanduser(
        "~/.config/gcloud/application_default_credentials.json"
    )
    gcs_connector_jar_path = "../gcs-connector-hadoop3-latest.jar"
    if not os.path.exists(gcs_connector_jar_path):
        raise FileNotFoundError(
            f"GCS connector JAR not found at {gcs_connector_jar_path}"
        )

    sparkgcp = (
        SparkSession.builder.appName("LocalGCS")
        .config("spark.driver.host", "localhost")
        .config(
            "spark.jars",
            gcs_connector_jar_path,
        )
        .config(
            "spark.hadoop.google.cloud.auth.service.account.enable", "true"
        )
        .config(
            "spark.hadoop.google.cloud.auth.service.account.json.keyfile",
            adc_path,
        )
        .config(
            "spark.hadoop.fs.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem",
        )
        .config(
            "spark.hadoop.fs.AbstractFileSystem.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS",
        )
        .getOrCreate()
    )
else:
    sparkgcp = SparkSession.builder.appName("GCSCluster").getOrCreate()

sc = sparkgcp.sparkContext
sc.setLogLevel("ERROR")

print("Connected to Spark cluster!")
print(f"Spark Version: {sc.version}")
print(f"Master: {sc.master}")
print(f"App ID: {sc.applicationId}")


# In[2]:


if is_local:
    prefix = "../data/processed/merged"
else:
    prefix = "gs://msds-694-cohort-14-3/data"

num_csv_path = f"{prefix}/num_2020.csv"
pre_csv_path = f"{prefix}/pre_2020.csv"
sub_csv_path = f"{prefix}/sub_2020.csv"
tag_csv_path = f"{prefix}/tag_2020.csv"

print(f"Num CSV path: {num_csv_path}")
print(f"Pre CSV path: {pre_csv_path}")
print(f"Sub CSV path: {sub_csv_path}")
print(f"Tag CSV path: {tag_csv_path}")

num_rdd = sc.textFile(num_csv_path)
pre_rdd = sc.textFile(pre_csv_path)
sub_rdd = sc.textFile(sub_csv_path)
tag_rdd = sc.textFile(tag_csv_path)

# print size of each RDD
print(f"Num RDD size: {num_rdd.count()}")
print(f"Pre RDD size: {pre_rdd.count()}")
print(f"Sub RDD size: {sub_rdd.count()}")
print(f"Tag RDD size: {tag_rdd.count()}")


# **Do companies with strong operating cashflow also show higher profitability, and does this change for different industries?**
# 
# Compute correlation between operating cash flow and net income. Look at how
# this relationship differs in various industries to see if there are some of them
# that don’t have correlation between profitability and cash flow. Identify
# outliers in both profitability and cash flow.
# 

# ### Create a 5000-line subset from NUM (in memory)
# 
# In this cell, I take the first 5,000 lines of the large NUM RDD.  
# This satisfies the assignment requirement of creating a smaller “subset” dataset.
# 
# Instead of writing this subset out to a local CSV file (which would not be visible to Dataproc),
# I keep the subset in memory by turning the list of lines back into an RDD with `sc.parallelize`.
# This way the exact same notebook works both on my laptop and on the Dataproc cluster, and I
# can still explore the smaller subset in later cells using `num_subset_rdd`.

# In[3]:


subset_size = 5000

num_subset_lines = num_rdd.take(subset_size)
print("Subset size (lines taken from num_2020.csv):", len(num_subset_lines))

num_subset_rdd = sc.parallelize(num_subset_lines)
print("num_subset_rdd count:", num_subset_rdd.count())


# ### Clean and split the subset and SUB files
# 
# Here I remove the header row from the subset file and from the SUB file.  
# Then I split every line by commas so I can access each column individually.
# 
# The NUM file contains numeric financial values like operating cashflow and net income.  
# The SUB file contains company-level metadata, including the SIC industry codes.

# In[4]:


num_header = num_rdd.first()
sub_header = sub_rdd.first()

num_subset_data = num_subset_rdd.filter(lambda line: line != num_header)
sub_data = sub_rdd.filter(lambda line: line != sub_header)

num_subset_split = num_subset_data.map(lambda line: line.split(","))
sub_split = sub_data.map(lambda line: line.split(","))

print("Example NUM subset row:", num_subset_split.first())
print("Example SUB row:", sub_split.first())


# ### Define the financial tags we care about
# 
# In this cell, I define the specific GAAP tags related to operating cash flow and profitability.  
# These tags appear in the NUM file and help me filter the dataset down to only the rows that are relevant to my research question.
# 
# I also create a small helper function (safe_float) that safely converts strings into floats so that bad values do not crash the notebook.

# In[ ]:


ocf_tags = [
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
]

profit_tags = [
    "NetIncomeLoss",
    "OperatingIncomeLoss",
]


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


# ### Filter the subset for operating cashflow and profitability rows
# 
# Here I:
# 1. Filter the subset NUM data to keep only rows where the `tag` is one of the operating cashflow or profitability tags.  
# 2. Extract the numeric value from the appropriate column.  
# 3. Quickly preview a few rows to make sure the filtering looks reasonable.

# In[ ]:


filtered = num_subset_split.filter(
    lambda cols: cols[1] in ocf_tags or cols[1] in profit_tags
)

tag_values = filtered.map(lambda cols: (cols[1], safe_float(cols[8]))).filter(
    lambda x: x[1] is not None
)

print("Example filtered rows from subset:")
for row in tag_values.take(10):
    print(row)


# ### Summarize the subset to get average financial values
# 1. Map each tag to a `(value, 1)` pair  
# 2. Reduce by key to get the total sum and count for each tag  
# 3. Compute the average value for each financial metric   

# In[ ]:


mapped = tag_values.map(lambda x: (x[0], (x[1], 1)))
reduced = mapped.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))
averages = reduced.map(lambda x: (x[0], x[1][0] / x[1][1]))

print(
    "Average values for operating cash flow and profitability tags (subset):"
)
for tag, avg_val in averages.collect():
    print(tag, avg_val)


# ### Prepare the full NUM and SUB datasets for the full analysis
# In this cell, I remove the header rows from the full NUM and SUB files and split each line by commas.  
# This prepares the full dataset so I can build a complete analysis that addresses my research question
# using all available company-year observations.

# In[8]:


num_data = num_rdd.filter(lambda line: line != num_header)
sub_data = sub_rdd.filter(lambda line: line != sub_header)

num_split = num_data.map(lambda line: line.split(","))
sub_split = sub_data.map(lambda line: line.split(","))

print("Full NUM example row:", num_split.first())
print("Full SUB example row:", sub_split.first())


# ### Extract operating cash flow and profitability rows from the full dataset
# 
# For each row, I pull out:
# - the filing ID (adsh)
# - the fiscal year (derived from the date)
# - the tag (which tells me whether it is operating cashflow or profitability)
# - the numeric value
# 
# I then filter to keep only the operating cashflow and profitability tags so I can build firm-year metrics.

# In[ ]:


num_filtered_full = num_split.filter(
    lambda cols: cols[1] in ocf_tags or cols[1] in profit_tags
)

num_tag_year_full = num_filtered_full.map(
    lambda cols: (
        (cols[0], cols[3][:4], cols[1]),
        safe_float(cols[8]),
    )
).filter(lambda x: x[1] is not None)

print("Sample (adsh, year, tag, value) rows from full NUM:")
for row in num_tag_year_full.take(10):
    print(row)


# ### Build firm-year operating cashflow and profitability metrics
# 
# 1. Separate the NUM rows into operating cashflow vs. profitability using the tag lists.  
# 2. For each group, aggregate values by (adsh, year) to get firm-year totals.  
# 3. Join the two RDDs so that each firm-year has both operating cashflow and profitability side by side.

# In[ ]:


ocf_records_full = num_tag_year_full.filter(lambda x: x[0][2] in ocf_tags)
profit_records_full = num_tag_year_full.filter(
    lambda x: x[0][2] in profit_tags
)

ocf_firm_year_full = ocf_records_full.map(
    lambda x: ((x[0][0], x[0][1]), x[1])
).reduceByKey(lambda a, b: a + b)

profit_firm_year_full = profit_records_full.map(
    lambda x: ((x[0][0], x[0][1]), x[1])
).reduceByKey(lambda a, b: a + b)

print("Sample firm-year OCF:", ocf_firm_year_full.take(5))
print("Sample firm-year Profit:", profit_firm_year_full.take(5))

firm_year_metrics = ocf_firm_year_full.join(profit_firm_year_full)

print("Sample firm-year OCF + Profit rows:")
for row in firm_year_metrics.take(10):
    print(row)


# ### Join operating cashflow and profitability per firm-year
# - a total operating cash flow value, and  
# - a total profitability value.

# In[11]:


firm_year_metrics = ocf_firm_year_full.join(profit_firm_year_full)
print("Sample firm-year OCF + Profit rows:")
for row in firm_year_metrics.take(10):
    print(row)


# ### Attach SIC industry codes from SUB
# - extract (adsh, sic) pairs from SUB,  
# - re-key the firm-year metrics by adsh, and  
# - join them together.
# 
# This uses an RDD join on adsh instead of any pre-merged CSV file, which makes the
# analysis portable to Dataproc because it only relies on the original SEC files in GCS.

# In[ ]:


adsh_sic = sub_split.map(lambda cols: (cols[0], cols[3])).filter(
    lambda x: x[1] not in ("", None, "NA")
)

print("Sample (adsh, sic) pairs:", adsh_sic.take(5))

firm_year_by_adsh = firm_year_metrics.map(
    lambda x: (x[0][0], (x[0][1], x[1][0], x[1][1]))
)

joined_full = firm_year_by_adsh.join(adsh_sic)

print("Sample rows with industry:", joined_full.take(10))


# ### Compute average operating cashflow and profitability by industry-year
# 
# For each (sic, year) combination:
# - sum all operating cashflow values  
# - sum all profitability values  
# - count how many firm-years are included  
# - compute the average operating cashflow and average profitability for that industry and year.
# 
# This directly answers my question about how these two metrics move together across different industries.
# 

# In[ ]:


industry_year_pairs = joined_full.map(
    lambda x: (
        (x[1][1], x[1][0][0]),
        (x[1][0][1], x[1][0][2], 1),
    )
)

industry_year_agg = industry_year_pairs.reduceByKey(
    lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2])
)

industry_year_avg = industry_year_agg.map(
    lambda x: (
        x[0],  # (sic, year)
        (x[1][0] / x[1][2], x[1][1] / x[1][2]),
    )
)

industry_year_avg_sorted = industry_year_avg.sortBy(
    lambda x: (x[0][1], x[0][0])
)


# In[ ]:


print("Industry-Year Average Operating Cash Flow & Profitability:\n")
for key, vals in industry_year_avg_sorted.take(50):
    sic, year = key
    avg_ocf, avg_profit = vals
    print(
        f"SIC {sic}, Year {year} Avg OCF = {avg_ocf:.2f}, Avg Profit = {avg_profit:.2f}"
    )


# ### Final Answer
# 
# My question was whether companies with strong operating cashflow also show higher profitability, and how this looks across different industries.
# 
# After building firm-year totals for operating cashflow and profitability, joining them with SIC industry codes, and averaging by (industry, year), the results mostly show a positive relationship industries and years with higher operating cashflow generally also have higher profitability.
# 
# There are a few exceptions where operating cashflow is positive but profitability is low or negative, which appear to be outliers or industry-specific situations. Overall, the trend is there, but the strength of the relationship changes depending on the industry.

# In[ ]:


import matplotlib.pyplot as plt
import numpy as np

sample = industry_year_avg_sorted.take(500)

avg_ocf_vals = [abs(vals[0]) + 1 for (_, vals) in sample]
avg_profit_vals = [abs(vals[1]) + 1 for (_, vals) in sample]

plt.figure(figsize=(8, 6))
plt.scatter(avg_ocf_vals, avg_profit_vals, alpha=0.6)
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Average Operating Cash Flow (log scale)")
plt.ylabel("Average Profit (log scale)")
plt.title("OCF vs Profit Across Industry-Year Observations (Log-Scaled)")
plt.grid(True)
plt.show()

