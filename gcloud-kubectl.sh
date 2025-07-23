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

gcloud container clusters create weaviate-cluster-a\
    --zone=us-central1 \
    --context=weaviate-cluster-a \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3

gcloud container clusters create weaviate-cluster-b \
    --zone=us-central1-a \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3

# 3. Get auth for the cluster
# This command configures kubectl to use the credentials for the cluster
gcloud container clusters get-credentials weaviate-cluster --zone=us-central1
gcloud container clusters get-credentials weaviate-cluster-a --zone=us-central1
gcloud container clusters get-credentials weaviate-cluster-b --zone=us-central1-a

# 4. Deploy the app and service in a SPECIFIC CLUSTER
#Note we only need the loadbalancer service for the web app, not the test script
#we do not need a separate service o handle ingress since we are using weaviate cloud client via python
kubectl apply -f weaviate-cloud-deployment.yaml

# Switch to cluster A context and apply the deployment
kubectl config use-context gke_weaviate-demo-466501_us-central1_weaviate-cluster-a
kubectl apply -f weaviate-cloud-deployment-clust-a.yaml

# Switch to cluster B context and apply the deployment
kubectl config use-context gke_weaviate-demo-466501_us-central1-a_weaviate-cluster-b
kubectl apply -f weaviate-cloud-deployment-clust-b.yaml


# Apply the secrets
kubectl apply -f weaviate-secrets.yaml

# 5. get the status of the deployment
##Get contexts:
kubectl config get-contexts
kubectl config view
kubectl config view --context=your-context-name

##can alternatively use the following command to set the context
kubectl config set-context prod_context --namespace=prod_namespace --cluster=my_cluster --user=prod_user

# This command checks the status of the deployment
kubectl get all -n weaviate-namespace
kubectl get deployments -n weaviate-namespace
#get the status of the pods
kubectl get pods -n weaviate-namespace

#debugging and logs:
kubectl logs weaviate-app-### -n weaviate-namespace
#shows more details about the pod and any errors
kubectl describe pod weaviate-app-### -n weaviate-namespace
#restart deployment:
kubectl rollout restart deployment/weaviate-app -n weaviate-namespace

#CLEANUP - Delete the deployment
kubectl delete deployment weaviate-app -n weaviate-namespace
#delete the service
kubectl delete service weaviate-app-service -n weaviate-namespace

#delete the cluster
gcloud container clusters delete weaviate-cluster --zone=us-central1
gcloud container clusters delete weaviate-cluster-a --zone=us-central1
gcloud container clusters delete weaviate-cluster-b --zone=us-central1-a
