#!/usr/bin/env python3
"""
Simple Weaviate Collection Migration Script
==========================================
Migrates data from "Question" collection to "QuestionNew" collection
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
    source = client.collections.get("Question")
    source_count = len(source)
    print(f"Found {source_count} objects in 'Question' collection")
    
    # Delete target collection if it exists
    """
    Looks like there is a naming convention that QuestionNew
    does not follow so i will remove the hyphen and use
    "QuestionNew" instead.
    """
    if client.collections.exists("QuestionNew"):
        client.collections.delete("QuestionNew")
        print("Deleted existing 'QuestionNew' collection")
    
    # Create new collection with Cohere vectorizer
    client.collections.create(
        name="QuestionNew",
        properties=[
            Property(name="question", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
            Property(name="answer", data_type=DataType.TEXT),
        ],
        vector_config=Configure.Vectors.text2vec_cohere(
            model="embed-multilingual-v3.0"
        ),
        generative_config=Configure.Generative.cohere()
    )
    print("Created 'QuestionNew' collection with Cohere vectorizer")
    
    # Get target collection
    target = client.collections.get("QuestionNew")
    
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