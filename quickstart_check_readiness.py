import weaviate
from weaviate.classes.init import Auth
import os
from dotenv import load_dotenv

#load_dotenv()  # Load environment variables from .env file
load_dotenv(override=True)  # Load environment variables from .env file, allowing overrides

# Best practice: store your credentials in environment variables
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
)

print(client.is_ready())  # Should print: `True`

client.close()  # Free up resources