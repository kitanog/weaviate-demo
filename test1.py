import weaviate
import requests, json
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property
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

# Get server metadata
meta = client.get_meta()
print("Server metadata:", meta)

# The modules section will show enabled vectorizers
if 'modules' in meta:
    print("Enabled modules:", meta['modules'])

'''
I see: text2vec-weaviate, so I'm not surr why the error occurs.
https://weaviate-python-client.readthedocs.io/en/stable/weaviate.classes.html#weaviate.classes.config.Vectorizers.TEXT2VEC_WEAVIATE

Enabled modules: {'backup-gcs': {'bucketName': 'weaviate-wcs-prod-cust-us-west3-workloads-backups', 'rootName': '19e60e83-bc56-4c71-a4a3-85438311b666'}, 'generative-anthropic': {'documentationHref': 'https://docs.anthropic.com/en/api/getting-started', 'name': 'Generative Search - Anthropic'}, 'generative-anyscale': {'documentationHref': 'https://docs.anyscale.com/endpoints/overview', 'name': 'Generative Search - Anyscale'}, 'generative-aws': {'documentationHref': 'https://docs.aws.amazon.com/bedrock/latest/APIReference/welcome.html', 'name': 'Generative Search - AWS'}, 'generative-cohere': {'documentationHref': 'https://docs.cohere.com/reference/chat', 'name': 'Generative Search - Cohere'}, 'generative-databricks': {'documentationHref': 'https://docs.databricks.com/en/machine-learning/foundation-models/api-reference.html#completion-task', 'name': 'Generative Search - Databricks'}, 'generative-friendliai': {'documentationHref': 'https://docs.friendli.ai/openapi/create-chat-completions', 'name': 'Generative Search - FriendliAI'}, 'generative-google': {'documentationHref': 'https://cloud.google.com/vertex-ai/docs/generative-ai/chat/test-chat-prompts', 'name': 'Generative Search - Google'}, 'generative-mistral': {'documentationHref': 'https://docs.mistral.ai/api/', 'name': 'Generative Search - Mistral'}, 'generative-nvidia': {'documentationHref': 'https://docs.api.nvidia.com/nim/reference/llm-apis', 'name': 'Generative Search - NVIDIA'}, 'generative-octoai': {'documentationHref': 'https://octo.ai/docs/text-gen-solution/getting-started', 'name': 'Generative Search - OctoAI (deprecated)'}, 'generative-ollama': {'documentationHref': 'https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion', 'name': 'Generative Search - Ollama'}, 'generative-openai': {'documentationHref': 'https://platform.openai.com/docs/api-reference/completions', 'name': 'Generative Search - OpenAI'}, 'generative-xai': {'documentationHref': 'https://docs.x.ai/docs/overview', 'name': 'Generative Search - xAI'}, 'multi2multivec-jinaai': {'documentationHref': 'https://jina.ai/embeddings/', 'name': 'JinaAI CLIP Multivec Module'}, 'multi2vec-cohere': {'documentationHref': 'https://docs.cohere.ai/embedding-wiki/', 'name': 'Cohere Module'}, 'multi2vec-google': {'documentationHref': 'https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-multimodal-embeddings', 'name': 'Google Multimodal Module'}, 'multi2vec-jinaai': {'documentationHref': 'https://jina.ai/embeddings/', 'name': 'JinaAI CLIP Module'}, 'multi2vec-nvidia': {'documentationHref': 'https://docs.api.nvidia.com/nim/reference/retrieval-apis', 'name': 'NVIDIA CLIP Module'}, 'multi2vec-voyageai': {'documentationHref': 'https://docs.voyageai.com/docs/multimodal-embeddings', 'name': 'VoyageAI Multi Modal Module'}, 
'qna-openai': {'documentationHref': 'https://platform.openai.com/docs/api-reference/completions', 'name': 'OpenAI Question & Answering Module'}, 'ref2vec-centroid': {}, 'reranker-cohere': {'documentationHref': 'https://txt.cohere.com/rerank/', 'name': 'Reranker - Cohere'}, 'reranker-jinaai': {'documentationHref': 'https://jina.ai/reranker', 'name': 'Reranker - Jinaai'}, 'reranker-nvidia': {'documentationHref': 'https://docs.api.nvidia.com/nim/reference/retrieval-apis', 'name': 'Reranker - NVIDIA'}, 'reranker-voyageai': {'documentationHref': 'https://docs.voyageai.com/reference/reranker-api', 'name': 'Reranker - VoyageAI'}, 'text2multivec-jinaai': {'documentationHref': 'https://jina.ai/embeddings/', 'name': 'JinaAI Multivec Module'}, 'text2vec-aws': {'documentationHref': 'https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html', 'name': 'AWS Module'}, 'text2vec-cohere': {'documentationHref': 'https://docs.cohere.ai/embedding-wiki/', 'name': 'Cohere Module'}, 'text2vec-databricks': {'documentationHref': 'https://docs.databricks.com/en/machine-learning/foundation-models/api-reference.html#embedding-task', 'name': 'Databricks Foundation Models Module - Embeddings'}, 'text2vec-google': {'documentationHref': 'https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings', 'name': 'Google Module'}, 'text2vec-huggingface': {'documentationHref': 'https://huggingface.co/docs/api-inference/detailed_parameters#feature-extraction-task', 'name': 'Hugging Face Module'}, 'text2vec-jinaai': {'documentationHref': 'https://jina.ai/embeddings/', 'name': 'JinaAI Module'}, 'text2vec-mistral': {'documentationHref': 'https://docs.mistral.ai/api/#operation/createEmbedding', 'name': 'Mistral Module'}, 'text2vec-nvidia': {'documentationHref': 'https://docs.api.nvidia.com/nim/reference/retrieval-apis', 'name': 'NVIDIA Module'}, 'text2vec-octoai': {'documentationHref': 'https://octo.ai/docs/text-gen-solution/getting-started', 'name': 'OctoAI Module (deprecated)'}, 'text2vec-ollama': {'documentationHref': 'https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings', 'name': 'Ollama Module'}, 'text2vec-openai': {'documentationHref': 'https://platform.openai.com/docs/guides/embeddings/what-are-embeddings', 'name': 'OpenAI Module'}, 'text2vec-voyageai': {'documentationHref': 'https://docs.voyageai.com/docs/embeddings', 'name': 'VoyageAI Module'}, 'text2vec-weaviate': {'documentationHref': 'https://api.embedding.weaviate.io', 'name': 'Weaviate Embedding Module'}}
'''
# # Clean up first (optional)
# if client.collections.exists("Question"):
#     client.collections.delete("Question")



# questions = client.collections.create(
#     name="Question",
#     vector_config=Configure.Vectors.text2vec_ollama(),
#     generative_config=Configure.Generative.cohere(),  # Configure the Ollama embedding model
# )

# resp = requests.get(
#     "https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json"
# )
# data = json.loads(resp.text)

# with questions.batch.dynamic() as batch:
#     for d in data:
#         batch.add_object(
#             {
#                 "answer": d["Answer"],
#                 "question": d["Question"],
#                 "category": d["Category"],
#             }
#         )
#         if batch.number_errors > 10:
#             print("Batch import stopped due to excessive errors.")
#             break

# failed_objects = questions.batch.failed_objects
# if failed_objects:
#     print(f"Number of failed imports: {len(failed_objects)}")
#     print(f"First failed object: {failed_objects[0]}")

# response = questions.query.near_text(query="biology", limit=2)

# for obj in response.objects:
#     print(json.dumps(obj.properties, indent=2))

client.close()  # Free up resources