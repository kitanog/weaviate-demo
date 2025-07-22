import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Poka-yoke: Always override environment variables to ensure latest values
load_dotenv(override=True)

class WeaviateService:
    """
    Service class for managing Weaviate operations with proper error handling
    and connection management following v4 client patterns.
    """
    
    def __init__(self):
        """Initialize Weaviate service with environment validation"""
        # Poka-yoke: Validate required environment variables exist
        self.required_env_vars = ["WEAVIATE_URL", "WEAVIATE_API_KEY", "COHERE_API_KEY", "OPENAI_API_KEY"]
        self._validate_environment()
        
        # Store credentials for connection reuse
        self.weaviate_url = os.environ["WEAVIATE_URL"]
        self.weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
        self.cohere_api_key = os.environ["COHERE_API_KEY"]
        self.openai_api_key = os.environ["OPENAI_API_KEY"]
        
        self.client = None
        self.collection_name = "Catalog"

    def _validate_environment(self) -> None:
        """Validate that all required environment variables are present"""
        missing_vars = [var for var in self.required_env_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

    def connect(self) -> weaviate.WeaviateClient:
        """
        Establish connection to Weaviate Cloud using v4 client
        Returns the client instance for method chaining
        """
        try:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=Auth.api_key(self.weaviate_api_key),
                headers={
                    "X-OpenAI-Api-Key": self.openai_api_key,
                    "X-Cohere-Api-Key": self.cohere_api_key
                }
            )
            print("✅ Successfully connected to Weaviate Cloud")
            return self.client
        except Exception as e:
            print(f"❌ Failed to connect to Weaviate Cloud: {e}")
            raise

    def create_collection(self) -> bool:
        """
        Create the Catalog collection with v4 syntax and error handling
        Returns True if successful, False otherwise
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            # Poka-yoke: Check if collection already exists and recreate
            if self.client.collections.exists(self.collection_name):
                print(f"⚠️ Collection '{self.collection_name}' already exists. Deleting and recreating...")
                self.client.collections.delete(self.collection_name)
            
            # Create collection with OpenAI vectorizer and proper schema
            collection = self.client.collections.create(
                name=self.collection_name,
                description="EcomMax product catalog for semantic search operations",
                vector_config=Configure.Vectors.text2vec_openai(
                    model="text-embedding-3-small",
                    dimensions=1536
                ),
                generative_config=Configure.Generative.openai(
                    model="gpt-3.5-turbo"
                ),  # Enable RAG capabilities, can be configured further to tune the model
                properties=[
                    Property(name="product_id", data_type=DataType.TEXT, description="Unique product identifier"),
                    Property(name="name", data_type=DataType.TEXT, description="Product name for search"),
                    Property(name="description", data_type=DataType.TEXT, description="Detailed product description"),
                    Property(name="category", data_type=DataType.TEXT, description="Product category classification"),
                    Property(name="price", data_type=DataType.NUMBER, description="Product price in USD"),
                    Property(name="brand", data_type=DataType.TEXT, description="Product brand identifier"),
                    Property(name="tags", data_type=DataType.TEXT_ARRAY, description="Product tags for filtering")
                ]
            )
            print(f"✅ {self.collection_name} collection created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            return False

    def add_products(self, products: List[Dict[str, Any]]) -> bool:
        """
        Add product data using v4 batch insert with validation
        Args:
            products: List of product dictionaries with required schema
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            catalog = self.client.collections.get(self.collection_name)
            
            # Poka-yoke: Validate product schema before insertion
            required_fields = {"product_id", "name", "description", "category", "price", "brand", "tags"}
            
            # Use v4 batch insert for optimal performance
            with catalog.batch.dynamic() as batch:
                for i, product in enumerate(products):
                    # Validate each product has required fields
                    missing_fields = required_fields - set(product.keys())
                    if missing_fields:
                        print(f"⚠️ Skipping product {i}: missing fields {missing_fields}")
                        continue
                        
                    batch.add_object(
                        properties={
                            "product_id": str(product["product_id"]),
                            "name": str(product["name"]),
                            "description": str(product["description"]),
                            "category": str(product["category"]),
                            "price": float(product["price"]),
                            "brand": str(product["brand"]),
                            "tags": product["tags"] if isinstance(product["tags"], list) else []
                        }
                    )
            
            # Poka-yoke: Verify data insertion was successful
            total_objects = catalog.aggregate.over_all(total_count=True)
            print(f"✅ Products added successfully. Total objects: {total_objects.total_count}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding products: {e}")
            return False

    def hybrid_search(self, query: str, limit: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and keyword search
        Args:
            query: Search query string
            limit: Maximum number of results to return
            alpha: Balance between vector (0.0) and keyword (1.0) search
        Returns:
            List of search results with metadata
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            catalog = self.client.collections.get(self.collection_name)
            
            response = catalog.query.hybrid(
                query=query,
                alpha=alpha,  # Balance between vector and keyword search
                limit=limit,
                return_metadata=MetadataQuery(score=True, explain_score=True)
            )
            
            # Format results for consistent API response
            results = []
            for obj in response.objects:
                results.append({
                    "product_id": obj.properties.get("product_id"),
                    "name": obj.properties.get("name"),
                    "description": obj.properties.get("description"),
                    "category": obj.properties.get("category"),
                    "price": obj.properties.get("price"),
                    "brand": obj.properties.get("brand"),
                    "tags": obj.properties.get("tags", []),
                    "score": obj.metadata.score if obj.metadata else None,
                    "explain_score": obj.metadata.explain_score if obj.metadata else None
                })
                
            return results
            
        except Exception as e:
            print(f"❌ Error in hybrid search: {e}")
            return []

    def keyword_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search using v4 syntax
        Args:
            query: Search query string
            limit: Maximum number of results to return
        Returns:
            List of search results with BM25 scores
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            catalog = self.client.collections.get(self.collection_name)
            
            response = catalog.query.bm25(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(score=True)
            )
            
            # Format results for consistent API response, could have made this a single function but kept separate for clarity
            results = []
            for obj in response.objects:
                results.append({
                    "product_id": obj.properties.get("product_id"),
                    "name": obj.properties.get("name"),
                    "description": obj.properties.get("description"),
                    "category": obj.properties.get("category"),
                    "price": obj.properties.get("price"),
                    "brand": obj.properties.get("brand"),
                    "tags": obj.properties.get("tags", []),
                    "score": obj.metadata.score if obj.metadata else None
                })
                
            return results
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []

    def vector_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform pure vector similarity search using v4 syntax
        Args:
            query: Search query string
            limit: Maximum number of results to return
        Returns:
            List of search results with vector distances
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            catalog = self.client.collections.get(self.collection_name)
            
            response = catalog.query.near_text(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )
            
            # Format results for consistent API response, could have made this a single function but kept separate for clarity
            results = []
            for obj in response.objects:
                results.append({
                    "product_id": obj.properties.get("product_id"),
                    "name": obj.properties.get("name"),
                    "description": obj.properties.get("description"),
                    "category": obj.properties.get("category"),
                    "price": obj.properties.get("price"),
                    "brand": obj.properties.get("brand"),
                    "tags": obj.properties.get("tags", []),
                    "distance": obj.metadata.distance if obj.metadata else None
                })
                
            return results
            
        except Exception as e:
            print(f"❌ Error in vector search: {e}")
            return []

    def rag_search(self, query: str, limit: int = 3, prompt_template: str = None) -> List[Dict[str, Any]]:
        """
        Perform RAG (Retrieval Augmented Generation) using v4 syntax
        Args:
            query: Search query string
            limit: Maximum number of results to return
            prompt_template: Custom prompt template for generation
        Returns:
            List of search results with generated content
        """
        try:
            if not self.client:
                raise ValueError("Client not connected. Call connect() first.")
                
            catalog = self.client.collections.get(self.collection_name)
            
            ##test
            # print the catalog object for testing purposes
            # print(f"\nCatalog object: {catalog}\n")
            # Default prompt template if none provided
            if not prompt_template:
                prompt_template = f"Describe this specific product and explain why it would be good for: {query}"
            
            response = catalog.generate.near_text(
                query=query,
                limit=limit,
                single_prompt=prompt_template, #changed from single_prompt to grouped_task
                return_metadata=MetadataQuery(distance=True)
            )
            
            # Format results for consistent API response, could have made this a single function but kept separate for clarity
            results = []
            for obj in response.objects:
                results.append({
                    "product_id": obj.properties.get("product_id"),
                    "name": obj.properties.get("name"),
                    "description": obj.properties.get("description"),
                    "category": obj.properties.get("category"),
                    "price": obj.properties.get("price"),
                    "brand": obj.properties.get("brand"),
                    "tags": obj.properties.get("tags", []),
                    "generated_content": obj.generated,
                    "distance": obj.metadata.distance if obj.metadata else None
                })
                
            return results
            
        except Exception as e:
            print(f"❌ Error in RAG search: {e}")
            return []

    def close(self) -> None:
        """Close the Weaviate client connection safely"""
        if self.client:
            try:
                self.client.close()
                print("🔌 Weaviate connection closed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Error closing connection: {e}")
            finally:
                self.client = None

    def __enter__(self):
        """Context manager entry - establish connection"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.close()

# Sample data for testing purposes - kept for backward compatibility
DEFAULT_SAMPLE_PRODUCTS = [
    {
        "product_id": "prod-001",
        "name": "Wireless Bluetooth Headphones",
        "description": "Premium noise-cancelling wireless headphones with 30-hour battery life. Perfect for music lovers and professionals.",
        "category": "Electronics",
        "price": 199.99,
        "brand": "AudioTech",
        "tags": ["wireless", "bluetooth", "noise-cancelling", "premium"]
    },
    {
        "product_id": "prod-002", 
        "name": "Ergonomic Office Chair",
        "description": "Comfortable ergonomic office chair with lumbar support and adjustable height. Ideal for long work sessions.",
        "category": "Furniture",
        "price": 349.99,
        "brand": "ErgoDesk",
        "tags": ["ergonomic", "office", "comfortable", "adjustable"]
    },
    {
        "product_id": "prod-003",
        "name": "Smart Fitness Watch", 
        "description": "Advanced fitness tracking watch with heart rate monitor, GPS, and waterproof design for active lifestyles.",
        "category": "Wearables",
        "price": 299.99,
        "brand": "FitTech",
        "tags": ["fitness", "smartwatch", "waterproof", "gps"]
    }
]


def main():
    """
    Main execution function demonstrating service usage with detailed results
    This is kept for backward compatibility and testing
    """
    try:
        # Use context manager for proper resource management
        with WeaviateService() as service:
            # Setup collection and add sample data
            if service.create_collection():
                if service.add_products(DEFAULT_SAMPLE_PRODUCTS):
                    
                    # Test all search capabilities
                    test_query = "comfortable headphones for work"
                    print(f"\n🔍 Testing searches for: '{test_query}'")
                    print("=" * 60)
                    
                    # Hybrid search test
                    print("\n📊 HYBRID SEARCH RESULTS:")
                    print("-" * 40)
                    hybrid_results = service.hybrid_search(test_query)
                    print(f"Found {len(hybrid_results)} results")
                    
                    for i, result in enumerate(hybrid_results, 1):
                        print(f"\n{i}. {result['name']} (${result['price']:.2f})")
                        print(f"   Category: {result['category']} | Brand: {result['brand']}")
                        print(f"   Score: {result.get('score', 'N/A')}")
                        print(f"   Description: {result['description'][:100]}...")
                        if result.get('tags'):
                            print(f"   Tags: {', '.join(result['tags'])}")
                    
                    # Keyword search test
                    print("\n\n📝 KEYWORD SEARCH RESULTS:")
                    print("-" * 40)
                    keyword_results = service.keyword_search(test_query)
                    print(f"Found {len(keyword_results)} results")
                    
                    for i, result in enumerate(keyword_results, 1):
                        print(f"\n{i}. {result['name']} (${result['price']:.2f})")
                        print(f"   Category: {result['category']} | Brand: {result['brand']}")
                        print(f"   Score: {result.get('score', 'N/A')}")
                        print(f"   Description: {result['description'][:100]}...")
                    
                    # Vector search test
                    print("\n\n🧠 VECTOR SEARCH RESULTS:")
                    print("-" * 40)
                    vector_results = service.vector_search(test_query)
                    print(f"Found {len(vector_results)} results")
                    
                    for i, result in enumerate(vector_results, 1):
                        print(f"\n{i}. {result['name']} (${result['price']:.2f})")
                        print(f"   Category: {result['category']} | Brand: {result['brand']}")
                        print(f"   Distance: {result.get('distance', 'N/A')}")
                        print(f"   Description: {result['description'][:100]}...")
                    
                    # RAG search test
                    print("\n\n🤖 RAG SEARCH RESULTS:")
                    print("-" * 40)
                    rag_results = service.rag_search(test_query)
                    print(f"Found {len(rag_results)} results")
                    
                    for i, result in enumerate(rag_results, 1):
                        print(f"\n{i}. {result['name']} (${result['price']:.2f})")
                        print(f"   Category: {result['category']} | Brand: {result['brand']}")
                        print(f"   Distance: {result.get('distance', 'N/A')}")
                        print(f"   Description: {result['description'][:100]}...")
                        if result.get('generated_content'):
                            print(f"   🤖 AI Generated: {result['generated_content'][:150]}...")
                        else:
                            print(f"   🤖 AI Generated: No content generated")
                    
                    # Summary comparison
                    print("\n\n📈 SEARCH COMPARISON SUMMARY:")
                    print("=" * 60)
                    print(f"Hybrid Search:  {len(hybrid_results)} results")
                    print(f"Keyword Search: {len(keyword_results)} results") 
                    print(f"Vector Search:  {len(vector_results)} results")
                    print(f"RAG Search:     {len(rag_results)} results")
                    
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()