#!/usr/bin/env python3
"""
Simple Weaviate Collection Migration Script
==========================================
Migrates data from "Question" collection to "CatalogNew" collection
and switches vectorizer from OpenAI to Cohere.
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]   
cohere_api_key = os.environ["COHERE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

def extract_properties_from_collection(collection):
    """Extract properties from an existing collection dynamically"""
    config = collection.config.get()
    # print(config)
    properties = []
    
    for prop in config.properties:
        properties.append(
            Property(
                name=prop.name,
                data_type=prop.data_type,
                description=getattr(prop, 'description', f"Property: {prop.name}")
            )
        )
    
    return properties


def migrate_collection():
    """Simple migration function"""
    
    # Connect to Weaviate Cloud
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers={"X-Cohere-Api-Key": cohere_api_key,
                 "X-OpenAI-Api-Key": openai_api_key
                 }
    )
    
    print("Connected to Weaviate")
    
    # Get source collection #could do some error checking here, but keeping it simple
    source = client.collections.get("Catalog")
    source_count = len(source)
    print(f"Found {source_count} objects in {source.name} collection")
    
    # Get properties schema from source collection dynamically
    source_properties = extract_properties_from_collection(source)
    print(f"Extracted {len(source_properties)} properties from source collection:")
    for prop in source_properties:
        print(f"  - {prop.name}") #

    # Delete target collection if it exists
    """
    Looks like there is a naming convention that Catalog-New
    does not follow so i will remove the hyphen and use
    "CatalogNew" instead.
    """
    if client.collections.exists("CatalogNew"):
        client.collections.delete("CatalogNew")
        print("Deleted existing 'CatalogNew' collection")
    
    # Create new collection with Cohere vectorizer
    client.collections.create(
        name="CatalogNew",
        properties=source_properties,
        vector_config=Configure.Vectors.text2vec_cohere(
            model="embed-multilingual-v3.0"
        ),
        generative_config=Configure.Generative.cohere()
    )
    
    # Get target collection
    target = client.collections.get("CatalogNew")

    print(f"Created {target.name} collection with text2vec-cohere vectorizer")
    
    # Migrate data in batches
    print("Starting migration...")
    migrated = 0
    
    with target.batch.fixed_size(batch_size=100) as batch:
        for obj in source.iterator():
            batch.add_object(
                properties=obj.properties,
                uuid=obj.uuid
            )
            migrated += 1
            
            if migrated % 100 == 0:
                print(f"   Migrated {migrated}/{source_count} objects...")
    
    # Verify migration
    target_count = len(target)
    print(f"Migration complete! {target_count}/{source_count} objects migrated")
    
    if target_count == source_count:
        print("Migration successful!")
    else:
        print("Some objects may not have migrated properly")
    
    client.close()

if __name__ == "__main__":
    migrate_collection()