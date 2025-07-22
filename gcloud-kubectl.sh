#set project
gcloud config set project weaviate-demo-466501

#create cluster and set IAM policy
# 1 . Set IAM policy
gcloud projects add-iam-policy-binding weaviate-demo-466501 --member="user:kittsgnk@gmail.com" --role=roles/container.admin

# 2. Create cluster
gcloud container clusters create-auto weaviate-cluster \
    --location=us-central1

#with only 2 nodes
gcloud container clusters create weaviate-cluster --zone=us-central1 --num-nodes=2

#with autoscaling
gcloud container clusters create weaviate-cluster \
    --zone=us-central1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3


# 2. Get auth for the cluster
# This command configures kubectl to use the credentials for the cluster
gcloud container clusters get-credentials weaviate-cluster --zone=us-central1

# 3. Deploy the app and service
#Note we only need the loadbalancer service for the web app, not the test script
#we do not need a separate service o handle ingress since we are using weaviate cloud client via python
kubectl apply -f weaviate-cloud-deployment.yaml

# Apply the secrets
kubectl apply -f weaviate-secrets.yaml