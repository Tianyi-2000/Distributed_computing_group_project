# set project to distributed
gcloud config set project distributed-computing-478219

# create bucket msds-694-cohort-14-<project_group_Number>
gcloud storage buckets create gs://msds-694-cohort-14-3

# upload data to bucket
gcloud storage cp ../data/processed/merged/num_2020.csv gs://msds-694-cohort-14-3/data/num_2020.csv
gcloud storage cp ../data/processed/merged/pre_2020.csv gs://msds-694-cohort-14-3/data/pre_2020.csv
gcloud storage cp ../data/processed/merged/sub_2020.csv gs://msds-694-cohort-14-3/data/sub_2020.csv
gcloud storage cp ../data/processed/merged/tag_2020.csv gs://msds-694-cohort-14-3/data/tag_2020.csv
