from fastapi import FastAPI,status
from llama_index.embeddings.sagemaker_endpoint import SageMakerEmbedding
import asyncio
import uvicorn
from weaviate import Client
import os
from llama_index.core import Settings
import dotenv
from pydantic import BaseModel
from utils.indexing import index_confluence_documents
from chainlit.utils import mount_chainlit



dotenv.load_dotenv()


app = FastAPI()


client = Client(os.getenv('WEAVIATE_CLIENT'),startup_period=30)


embed_model = SageMakerEmbedding(
    endpoint_name=os.getenv('SAGEMAKER_ENDPOINT'),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)



# Initialize Embedding model
Settings.embed_model = embed_model



index=None



@app.get("/chat/health",tags=["healthcheck"],summary="Perform a Health Check",
         response_description="Return HTTP Status Code 200 (OK)",
                 status_code=status.HTTP_200_OK,)
def get_health() -> str:    return "OK"
 



class IndexConfluenceInput(BaseModel):
    confluence_url: str
    space_key: str

@app.post("/api/v1/index_confluence_space/")
async def index_confluence_documents_api(input: IndexConfluenceInput):
    """
    Index documents from a specified Confluence space.
    """
    try:
        index_confluence_documents(input.confluence_url, input.space_key)
        return {"message": "Data indexed successfully"}
    except Exception as e:
        return {"error": str(e)}
    

mount_chainlit(app=app, target="chainlit_app.py", path="/chainlit")










'''
if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8100)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
'''