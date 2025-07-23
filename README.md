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