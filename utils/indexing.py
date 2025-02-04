from llama_index.vector_stores.weaviate import WeaviateVectorStore
from weaviate.exceptions import AuthenticationFailedException
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext
from llama_index.core import Document
from fastapi import  HTTPException
from weaviate import Client
from llama_index.readers.confluence import ConfluenceReader
import os 
import dotenv


dotenv.load_dotenv()

client = Client(os.getenv('WEAVIATE_CLIENT'))




    


def process_documents(documents):
    global index 

    # Process each document
    parser = SimpleNodeParser.from_defaults(chunk_size=1024)
    nodes = parser.get_nodes_from_documents(documents=documents)

    try:
        vector_store = WeaviateVectorStore(
            weaviate_client=client, index_name=os.getenv("index_name")
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex(nodes, storage_context=storage_context)
    except AuthenticationFailedException:
        raise HTTPException(status_code=500, detail="Connection to Weaviate failed")



def index_confluence_documents(confluence_url, space_key):
    global index
    try:
        # Set up Confluence Reader with provided URL
        reader = ConfluenceReader(base_url=confluence_url)

        # Load documents from the specified space key
        documents = reader.load_data(space_key=space_key)

        # Process and index documents
        process_documents(documents)
        
        # Setup vector store and index
        vector_store = WeaviateVectorStore(
            weaviate_client=client, index_name=os.getenv("index_name")
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        print("Data indexed successfully")
    except Exception as e:
        print("ERROR:", str(e))




