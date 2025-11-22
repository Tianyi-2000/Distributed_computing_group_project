# set project to distributed
gcloud config set project distributed-computing-478219

# create bucket msds-694-cohort-14-<project_group_Number>
gcloud storage buckets create gs://msds-694-cohort-14-3

# upload data to bucket
gcloud storage cp ../data/processed/merged/num_2020.csv gs://msds-694-cohort-14-3/data/num_2020.csv
gcloud storage cp ../data/processed/merged/pre_2020.csv gs://msds-694-cohort-14-3/data/pre_2020.csv
gcloud storage cp ../data/processed/merged/sub_2020.csv gs://msds-694-cohort-14-3/data/sub_2020.csv
gcloud storage cp ../data/processed/merged/tag_2020.csv gs://msds-694-cohort-14-3/data/tag_2020.csv

# create role groupproject with bucket object reader writer and dataproc admin
gcloud iam roles create groupproject --project=distributed-computing-478219 --title="Group Project Power Users"

# add permissions to role
gcloud iam roles update groupproject --project=distributed-computing-478219 --add-permissions="resourcemanager.projects.get,storage.buckets.list,storage.objects.get,storage.objects.list,storage.objects.create,storage.objects.delete,dataproc.clusters.create,dataproc.clusters.delete,dataproc.clusters.get,dataproc.clusters.update,dataproc.jobs.create,dataproc.jobs.get,dataproc.jobs.list"


# invite users to project
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:igomeza5@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
# chrisjd409@gmail.com
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:chrisjd409@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
# paul.nsn@gmail.com
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:paul.nsn@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
# bostonabautista@gmail.com
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:bostonabautista@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
# alexluous@gmail.com
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:alexluous@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
# Naderzadnikki@gmail.com
gcloud projects add-iam-policy-binding distributed-computing-478219 --member="user:naderzadnikki@gmail.com" --role="projects/distributed-computing-478219/roles/groupproject"
