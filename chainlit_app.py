from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine.condense_plus_context import CondensePlusContextChatEngine
from llama_index.embeddings.sagemaker_endpoint import SageMakerEmbedding
from llama_index.llms.ollama import Ollama
import dotenv
import os
from weaviate import Client
import chainlit as cl
from chainlit.step import StepDict
import chainlit.data as cl_data
from chainlit.types import (
    PageInfo,
    PaginatedResponse,
    Pagination,
    ThreadDict,
    ThreadFilter,
)
import boto3
import pickle
from literalai.helper import utc_now
from typing import Dict, List, Optional
from botocore.exceptions import NoCredentialsError, ClientError
import uuid

dotenv.load_dotenv()

# Initialize LLM and embedding models
llm = Ollama(base_url=os.getenv("LLM_ENDPOINT"), model="mistral:7b-instruct-v0.3-q6_K")
embed_model = SageMakerEmbedding(
    endpoint_name=os.getenv("SAGEMAKER_ENDPOINT"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

client = Client(os.getenv("WEAVIATE_CLIENT"))

Settings.llm = llm
Settings.embed_model = embed_model
Settings.context_window = 4096

# AWS S3 Setup
s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
THREAD_HISTORY_S3_PATH = os.getenv("THREAD_HISTORY_S3_PATH")
THREAD_HISTORY_PICKLE_PATH = "./thread_history.pkl"

# Initialize thread history
thread_history = []
deleted_thread_ids = []
now = utc_now()


def download_pickle_from_s3():
    """Download thread history from S3."""
    try:
        s3_client.download_file(S3_BUCKET_NAME, THREAD_HISTORY_S3_PATH, THREAD_HISTORY_PICKLE_PATH)
        print("Thread history loaded from S3")
    except ClientError as e:
        print(f"Failed to download thread history from S3: {e}")
    except FileNotFoundError:
        print("No thread history file found on S3, starting fresh.")


def validate_thread_history():
    """Validate thread history to ensure all threads have an 'id' field."""
    global thread_history
    if thread_history:
        thread_history = [
            thread for thread in thread_history if "id" in thread
        ]
        print(f"Validated thread history: {len(thread_history)} valid threads.")


# Load thread history
download_pickle_from_s3()

if THREAD_HISTORY_PICKLE_PATH and os.path.exists(THREAD_HISTORY_PICKLE_PATH):
    with open(THREAD_HISTORY_PICKLE_PATH, "rb") as f:
        thread_history = pickle.load(f)
    validate_thread_history()
else:
    print("Starting with an empty thread history.")


async def save_thread_history():
    """Save thread history to local file and upload to S3."""
    global thread_history
    if THREAD_HISTORY_PICKLE_PATH:
        # Validate thread history before saving
        valid_thread_history = [
            thread for thread in thread_history if "id" in thread
        ]
        with open(THREAD_HISTORY_PICKLE_PATH, "wb") as out_file:
            pickle.dump(valid_thread_history, out_file)
        print("Validated and saved thread history locally.")

        # Upload the file to S3
        try:
            s3_client.upload_file(THREAD_HISTORY_PICKLE_PATH, S3_BUCKET_NAME, THREAD_HISTORY_S3_PATH)
            print("Thread history uploaded to S3")
        except (NoCredentialsError, ClientError) as e:
            print(f"Failed to upload thread history to S3: {e}")


class TestDataLayer(cl_data.BaseDataLayer):
    async def get_user(self, identifier: str):
        print("GET_USER TRIGGERED")
        return cl.PersistedUser(id="test", createdAt=now, identifier=identifier)

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        thread = next((t for t in thread_history if t["id"] == thread_id), None)
        if thread:
            if name:
                thread["name"] = name
            if metadata:
                thread["metadata"] = metadata
            if tags:
                thread["tags"] = tags
        else:
            thread_history.append(
                {
                    "id": thread_id or str(uuid.uuid4()),  # Ensure unique ID
                    "name": name,
                    "metadata": metadata,
                    "tags": tags,
                    "createdAt": utc_now(),
                    "userId": user_id,
                    "userIdentifier": "admin",
                    "steps": [],
                }
            )

    async def create_step(self, step_dict: StepDict):
        cl.user_session.set(
            "create_step_counter", cl.user_session.get("create_step_counter") + 1
        )
        thread = next(
            (t for t in thread_history if t["id"] == step_dict.get("threadId")), None
        )
        if thread:
            thread["steps"].append(step_dict)

    async def get_thread_author(self, thread_id: str):
        return "admin"

    async def list_threads(self, pagination: Pagination, filters: ThreadFilter) -> PaginatedResponse[ThreadDict]:
        valid_threads = [
            t for t in thread_history if t.get("id") not in deleted_thread_ids
        ]
        return PaginatedResponse(
            data=valid_threads,
            pageInfo=PageInfo(hasNextPage=False, startCursor=None, endCursor=None),
        )

    async def get_thread(self, thread_id: str):
        thread = next((t for t in thread_history if t["id"] == thread_id), None)
        if not thread:
            return None
        thread["steps"] = sorted(thread["steps"], key=lambda x: x["createdAt"])
        return thread

    async def delete_thread(self, thread_id: str):
        deleted_thread_ids.append(thread_id)


cl_data._data_layer = TestDataLayer()


async def send_count():
    create_step_counter = cl.user_session.get("create_step_counter")
    await cl.Message(f"Create step counter: {create_step_counter}").send()


@cl.on_chat_start
async def main():
    print("CHAT STARTED")
    cl.user_session.set("create_step_counter", 0)
    await cl.Message("Hello, How Can I assist you Today!").send()
    setup_engine()


@cl.on_message
async def handle_message(message: cl.Message):
    print("MESSAGE HANDLED")
    
    # Define a set of common greetings
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}
    
    # Normalize input to lowercase for comparison
    user_message = message.content.strip().lower()
    
    # Check if the message is a greeting
    if any(greeting in user_message for greeting in greetings):
        # Send a friendly response for a greeting
        await cl.Message("Hello! How can I assist you today?").send()
        return
    
    # If the message is not a greeting, proceed with the LLM response
    chat_engine = cl.user_session.get("chat_engine")
    msg = cl.Message(content="", author="Assistant")
    async with cl.Step(type="tool", name="LLM") as step:
        step.output = "Thinking..."
    res = await cl.make_async(chat_engine.stream_chat)(message.content)
    for token in res.response_gen:
        await msg.stream_token(token)
    await msg.send()
    
    # Save the thread history
    await save_thread_history()



@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("CHAT RESUMED")
    setup_engine()


def setup_engine():
    memory = cl.user_session.get("memory")
    vector_store = WeaviateVectorStore(
        weaviate_client=client, index_name=os.getenv("index_name")
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever()
    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=retriever, memory=memory, Verbose=True
    )
    cl.user_session.set("chat_engine", chat_engine)
