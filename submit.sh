#!/bin/bash
set -e

# REPLACE WITH YOUR PROJECT ID
PROJECT_ID="distributed-computing-478219"
BUCKET_NAME="msds-694-cohort-14-3" 
NOTEBOOK_PATH=/Users/nikkinaderzad/Desktop/Distributed_gp/Distributed_computing_group_project/notebooks/niki.ipynb
SCRIPT_PATH=/Users/nikkinaderzad/Desktop/Distributed_gp/Distributed_computing_group_project/notebooks/niki.py

# create storage bucket (if needed)
# gcloud storage buckets create gs://$BUCKET_NAME

# convert jupyter notebook to python script
echo "Converting notebook to Python script..."
jupyter nbconvert --to script "$NOTEBOOK_PATH" --output niki

# upload python script to storage bucket
echo "Uploading Python script to bucket..."
gcloud storage cp "$SCRIPT_PATH" gs://$BUCKET_NAME/scripts/niki.py

# create dataproc cluster (check if it already exists)
echo "Creating dataproc cluster..."
if gcloud dataproc clusters describe distributed-cluster-1 --region=us-central1 --project=$PROJECT_ID &>/dev/null; then
    echo "Cluster already exists, skipping creation..."
else
    gcloud dataproc clusters create distributed-cluster-1 \
        --labels=createdinclass=true \
        --region=us-central1 \
        --master-machine-type=n2d-standard-2 \
        --worker-machine-type=n2d-standard-2 \
        --master-boot-disk-type=pd-ssd \
        --master-boot-disk-size=30GB \
        --worker-boot-disk-type=pd-ssd \
        --worker-boot-disk-size=30GB \
        --num-workers=2 \
        --no-address \
        --image-version=2.0-debian10 \
        --optional-components=JUPYTER \
        --project=$PROJECT_ID
fi

# list clusters
gcloud dataproc clusters list --region=us-central1 --project=$PROJECT_ID

# submit python script to cluster
echo "Submitting PySpark job..."
JOB_ID=$(gcloud dataproc jobs submit pyspark gs://$BUCKET_NAME/scripts/niki.py \
    --cluster=distributed-cluster-1 \
    --region=us-central1 \
    --project=$PROJECT_ID \
    --format="value(reference.jobId)" \
    -- --is-local false)

echo "Job submitted with ID: $JOB_ID"

# wait for job to complete
echo "Waiting for job to complete..."
gcloud dataproc jobs wait "$JOB_ID" --region=us-central1 --project=$PROJECT_ID

echo "Job completed!"

# delete cluster, no approval needed
echo "Deleting cluster..."
gcloud dataproc clusters delete distributed-cluster-1 --region=us-central1 --project=$PROJECT_ID --quiet

echo "Done!"
