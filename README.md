# Weaviate Demo

A little demonstration application showcasing Weaviate vector database capabilities with multiple AI model integrations including OpenAI, Cohere.

## Purpose

This project demonstrates the power of Weaviate as a vector database for semantic search, retrieval-augmented generation (RAG), and AI-powered applications. It showcases integration with multiple AI providers.

## Architecture

```yaml
# Project Structure DSL
project:
  name: "weaviate-demo"
  type: "vector-database-application"
  
  components:
    - weaviate_core:
        description: "Vector database engine"
        capabilities: ["semantic_search", "hybrid_search", "vector_search", "vector_storage"]
    
    - ai_integrations:
        openai: "GPT models and embeddings"
        cohere: "Command models and embeddings" 
        weaviate_embeddings: "Built-in embedding service"
    
    - modules:
        vectorizers: ["text2vec-weaviate", "text2vec-cohere"]
        generators: ["openai", "cohere"]

  deployment:
    method: "docker and k8"
```

## Really Quick Start

### Prerequisites

Before getting started, ensure you have the following installed and configured:

- **Docker & Docker Compose**: [Installation Guide](https://docs.docker.com/get-docker/)
- **API Keys**: Obtain API keys from your chosen providers
- Python >= 3.11

### Building from Source

```bash
# Clone the repository (make sure you are in a folder tou want to be in - I make this mistake a lot)
git clone https://github.com/kitanog/weaviate-demo.git
cd weaviate-demo
```

### Using Python
```bash
#You can just run the python file with sample data and printed outputs
python weaviate_k8_test
#OR for the web app:
uvicorn weaviate_k8_web:app --reload

```

### Using Pre-built Docker Image

The easiest way to get started is using our pre-built Docker image:

```bash
# Pull the latest image
docker pull kiitangnk/weaviate-search-app:linux

# Run with required environment variables
docker run -d \
  --name weaviate-demo \
  -p 8080:8080 \
  -p 50051:50051 \
  -e WEAVIATE_URL="http://localhost:8080" \
  -e WEAVIATE_API_KEY="your-api-key-here" \
  -e ENABLE_API_BASED_MODULES="true" \
  -e ENABLE_MODULES="text2vec_weaviate,text2vec-ollama,generative-ollama" \
  -e OPENAI_API_KEY="your-openai-key" \
  -e COHERE_API_KEY="your-cohere-key" \
  kiitangnk/weaviate-search-app:linux
```

### Using K8
Just follow the steps as is
```bash
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

gcloud container clusters create weaviate-cluster-b \
    --zone=us-central1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3

gcloud container clusters create weaviate-cluster-b \
    --zone=us-central1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3

# 3. Get auth for the cluster
# This command configures kubectl to use the credentials for the cluster
gcloud container clusters get-credentials weaviate-cluster --zone=us-central1
gcloud container clusters get-credentials weaviate-cluster-a --zone=us-central1
gcloud container clusters get-credentials weaviate-cluster-b --zone=us-central1

# 4. Deploy the app and service in a SPECIFIC CLUSTER
#Note we only need the loadbalancer service for the web app, not the test script
#we do not need a separate service o handle ingress since we are using weaviate cloud client via python
kubectl apply -f weaviate-cloud-deployment.yaml

# Switch to cluster A context and apply the deployment
kubectl config use-context weaviate-cluster-a
kubectl apply -f weaviate-cloud-deployment-clust-a.yaml

# Switch to cluster B context and apply the deployment
kubectl config use-context weaviate-cluster-a
kubectl apply -f weaviate-cloud-deployment-clust-b.yaml


# Apply the secrets
kubectl apply -f weaviate-secrets.yaml

# 5. get the status of the deployment
# This command checks the status of the deployment
 kubectl get all -n weaviate-namespace
kubectl get deployments -n weaviate-namespace
#get the status of the pods
kubectl get pods -n weaviate-namespace

#logs:
kubectl logs weaviate-app-### -n weaviate-namespace

#CLEANUP - Delete the deployment
kubectl delete deployment weaviate-app -n weaviate-namespace
#delete the service
kubectl delete service weaviate-app -n weaviate-namespace

#delete the cluster
gcloud container clusters delete weaviate-cluster --zone=us-central1
gcloud container clusters delete weaviate-cluster-a --zone=us-central1
gcloud container clusters delete weaviate-cluster-b --zone=us-central1
```

### Environment File Setup

Create a `.env` file in your project root:

```bash
# .env file
# Copy this template and fill in your actual API keys

# Weaviate Configuration
WEAVIATE_URL=
WEAVIATE_API_KEY=
ENABLE_API_BASED_MODULES="true"
ENABLE_MODULES="text2vec_weaviate,text2vec-ollama,generative-ollama"
#model API keys
OPENAI_API_KEY=""
COHERE_API_KEY=""

```


## Development

### Building from Source

```bash
# Clone the repository (make sure you are in a folder tou want to be in - I make this mistake a lot)
git clone https://github.com/kitanog/weaviate-demo.git
cd weaviate-demo

# Build the Docker image
docker build -t weaviate-search-app:local .

# Run locally built image
docker run -d \
  --name weaviate-demo-local \
  -p 8080:8080 \
  --env-file .env \
  weaviate-search-app:local
```

### Project Structure

```
weaviate-demo/
├── weaviatecont/          # Main application code
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-service orchestration
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Health Check Endpoints

- **Readiness**: `GET /v1/.well-known/ready`
- **Liveness**: `GET /v1/.well-known/live`
- **Schema**: `GET /v1/schema`

## 📚 Additional Resources

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Cohere API Documentation](https://docs.cohere.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request


---

**Built with my time**