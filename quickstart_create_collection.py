import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
import os
from dotenv import load_dotenv

#load_dotenv()  # Load environment variables from .env file
load_dotenv(override=True)  # Load environment variables from .env file, allowing overrides

# Best practice: store your credentials in environment variables
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(weaviate_api_key),             # Replace with your Weaviate Cloud key
)
# client status check
print("\n\n\n")
print(client.is_ready())  # Should print: `True`
print("\n\n\n")

# Clean up first 
if client.collections.exists("Question"):
    client.collections.delete("Question")

#NOTE: There is a problem with the vector_config in the original code,
# I had to use text2vec_ollama instead of text2vec_weaviate
#text2vec_weaviate fails with the error:
'''
https://weaviate-python-client.readthedocs.io/en/stable/weaviate.classes.html#weaviate.classes.config.Vectorizers.TEXT2VEC_WEAVIATE

weaviate.exceptions.UnexpectedStatusCodeError: 
Collection may not have been created properly.! 
Unexpected status code: 422, with response body: 
{'error': [{'message': "module 'text2vec-weaviate': invalid properties: didn't find a single property which is of type string or text and is not excluded from indexing. 
In addition the class name is excluded from vectorization as well, meaning that it cannot be used to determine the vector position. To fix this, set 'vectorizeClassName' to true if the class name is contextionary-valid. Alternatively add at least contextionary-valid text/string property which is not excluded from indexing"}]}.
'''
#Adding properties resolved the issue

# questions = client.collections.create(
#     name="Question",
#     vector_config=Configure.Vectors.text2vec_weaviate(), # Configure the Weaviate Embeddings integration
#     generative_config=Configure.Generative.cohere(),           # Configure the Cohere generative AI integration
# )

questions = client.collections.create(
    name="Question",
    properties=[
        Property(name="question", data_type=DataType.TEXT),  # Required for vectorization
        Property(name="category", data_type=DataType.TEXT),
        Property(name="answer", data_type=DataType.TEXT),
    ],
    vector_config=Configure.Vectors.text2vec_weaviate(),
    generative_config=Configure.Generative.cohere()
)
client.close()  # Free up resources