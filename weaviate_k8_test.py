import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Poka-yoke: Always override environment variables to ensure latest values
load_dotenv(override=True)

# Poka-yoke: Validate required environment variables exist
required_env_vars = ["WEAVIATE_URL", "WEAVIATE_API_KEY", "COHERE_API_KEY", "OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

# Get credentials from environment
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
cohere_api_key = os.environ["COHERE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

# Sample ecommerce catalog data
sample_products = [
    {
        "product_id": "prod-001",
        "name": "Wireless Bluetooth Headphones",
        "description": "Premium noise-cancelling wireless headphones with 30-hour battery life. Perfect for music lovers and professionals.",
        "category": "Electronics",
        "price": 199.99,
        "brand": "AudioTech",
        "tags": ["wireless", "bluetooth", "noise-cancelling", "premium"],
        "specifications": {
            "battery_life": "30 hours",
            "connectivity": "Bluetooth 5.0",
            "weight": "250g"
        }
    },
    {
        "product_id": "prod-002", 
        "name": "Ergonomic Office Chair",
        "description": "Comfortable ergonomic office chair with lumbar support and adjustable height. Ideal for long work sessions.",
        "category": "Furniture",
        "price": 349.99,
        "brand": "ErgoDesk",
        "tags": ["ergonomic", "office", "comfortable", "adjustable"],
        "specifications": {
            "material": "Mesh and leather",
            "weight_capacity": "120kg",
            "adjustable_height": "Yes"
        }
    },
    {
        "product_id": "prod-003",
        "name": "Smart Fitness Watch", 
        "description": "Advanced fitness tracking watch with heart rate monitor, GPS, and waterproof design for active lifestyles.",
        "category": "Wearables",
        "price": 299.99,
        "brand": "FitTech",
        "tags": ["fitness", "smartwatch", "waterproof", "gps"],
        "specifications": {
            "battery_life": "7 days",
            "water_resistance": "50m",
            "sensors": "Heart rate, GPS, accelerometer"
        }
    }
]

def connect_to_weaviate():
    """Connect to Weaviate Cloud using v4 client"""
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={
                "X-OpenAI-Api-Key": openai_api_key,
                "X-Cohere-Api-Key": cohere_api_key
            }
        )
        print("✅ Successfully connected to Weaviate Cloud")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Weaviate Cloud: {e}")
        raise

def create_catalog_collection(client):
    """Create the Catalog collection with proper v4 syntax"""
    try:
        # Poka-yoke: Check if collection already exists
        if client.collections.exists("Catalog"):
            print("⚠️ Collection 'Catalog' already exists. Deleting and recreating...")
            client.collections.delete("Catalog")
        
        # Create collection with OpenAI vectorizer
        collection = client.collections.create(
            name="Catalog",
            description="EcomMax product catalog for semantic search",
            vectorizer_config=Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
                dimensions=1536
            ),
            generative_config=Configure.Generative.openai(),  # For RAG capabilities
            properties=[
                Property(name="product_id", data_type=DataType.TEXT, description="Unique product identifier"),
                Property(name="name", data_type=DataType.TEXT, description="Product name"),
                Property(name="description", data_type=DataType.TEXT, description="Product description"),
                Property(name="category", data_type=DataType.TEXT, description="Product category"),
                Property(name="price", data_type=DataType.NUMBER, description="Product price in USD"),
                Property(name="brand", data_type=DataType.TEXT, description="Product brand"),
                Property(name="tags", data_type=DataType.TEXT_ARRAY, description="Product tags")
            ]
        )
        print("✅ Catalog collection created successfully")
        return collection
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        raise

def add_sample_data(client):
    """Add sample product data using v4 batch insert"""
    try:
        catalog = client.collections.get("Catalog")
        
        # Poka-yoke: Use batch insert for efficiency
        with catalog.batch.dynamic() as batch:
            for product in sample_products:
                batch.add_object(
                    properties={
                        "product_id": product["product_id"],
                        "name": product["name"],
                        "description": product["description"],
                        "category": product["category"],
                        "price": product["price"],
                        "brand": product["brand"],
                        "tags": product["tags"]
                    }
                )
        
        print("✅ Sample data added successfully")
        
        # Poka-yoke: Verify data was inserted
        total_objects = catalog.aggregate.over_all(total_count=True)
        print(f"📊 Total objects in collection: {total_objects.total_count}")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        raise

def hybrid_search_example(client, query: str):
    """Perform hybrid search using v4 syntax"""
    try:
        catalog = client.collections.get("Catalog")
        
        response = catalog.query.hybrid(
            query=query,
            alpha=0.5,  # Balance between vector and keyword search
            limit=5,
            return_metadata=MetadataQuery(score=True, explain_score=True)
        )
        
        print(f"\n🔍 Hybrid Search Results for: '{query}'")
        print("-" * 50)
        
        if response.objects:
            for i, obj in enumerate(response.objects, 1):
                print(f"{i}. {obj.properties['name']} ({obj.properties['category']})")
                print(f"   Price: ${obj.properties['price']}")
                print(f"   Score: {obj.metadata.score:.4f}")
                print(f"   Description: {obj.properties['description'][:100]}...")
                print()
        else:
            print("No results found")
            
    except Exception as e:
        print(f"❌ Error in hybrid search: {e}")

def keyword_search_example(client, query: str):
    """Perform BM25 keyword search using v4 syntax"""
    try:
        catalog = client.collections.get("Catalog")
        
        response = catalog.query.bm25(
            query=query,
            limit=5,
            return_metadata=MetadataQuery(score=True)
        )
        
        print(f"\n🔤 Keyword Search Results for: '{query}'")
        print("-" * 50)
        
        if response.objects:
            for i, obj in enumerate(response.objects, 1):
                print(f"{i}. {obj.properties['name']} ({obj.properties['category']})")
                print(f"   Price: ${obj.properties['price']}")
                print(f"   Score: {obj.metadata.score:.4f}")
                print()
        else:
            print("No results found")
            
    except Exception as e:
        print(f"❌ Error in keyword search: {e}")

def vector_search_example(client, query: str):
    """Perform pure vector search using v4 syntax"""
    try:
        catalog = client.collections.get("Catalog")
        
        response = catalog.query.near_text(
            query=query,
            limit=5,
            return_metadata=MetadataQuery(distance=True)
        )
        
        print(f"\n🧠 Vector Search Results for: '{query}'")
        print("-" * 50)
        
        if response.objects:
            for i, obj in enumerate(response.objects, 1):
                print(f"{i}. {obj.properties['name']} ({obj.properties['category']})")
                print(f"   Price: ${obj.properties['price']}")
                print(f"   Distance: {obj.metadata.distance:.4f}")
                print()
        else:
            print("No results found")
            
    except Exception as e:
        print(f"❌ Error in vector search: {e}")

def rag_example(client, query: str):
    """Perform RAG (Retrieval Augmented Generation) using v4 syntax"""
    try:
        catalog = client.collections.get("Catalog")
        
        response = catalog.generate.near_text(
            query=query,
            limit=3,
            single_prompt=f"Describe this product and explain why it would be good for: {query}",
            return_metadata=MetadataQuery(distance=True)
        )
        
        print(f"\n🤖 RAG Results for: '{query}'")
        print("-" * 50)
        
        if response.objects:
            for i, obj in enumerate(response.objects, 1):
                print(f"{i}. {obj.properties['name']}")
                print(f"   Generated Response: {obj.generated}")
                print(f"   Distance: {obj.metadata.distance:.4f}")
                print()
        else:
            print("No results found")
            
    except Exception as e:
        print(f"❌ Error in RAG search: {e}")

def main():
    """Main execution function with proper error handling"""
    client = None
    try:
        # Connect to Weaviate Cloud
        client = connect_to_weaviate()
        
        # Setup initial collection and data
        create_catalog_collection(client)
        add_sample_data(client)
        
        # Test different search capabilities
        test_query = "comfortable headphones for work"
        
        hybrid_search_example(client, test_query)
        keyword_search_example(client, test_query)
        vector_search_example(client, test_query)
        rag_example(client, test_query)
        
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        # Poka-yoke: Always close connection
        if client:
            client.close()
            print("🔌 Connection closed")

if __name__ == "__main__":
    main()