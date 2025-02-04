from typing import Optional
from chainlit.logger import logger
import chainlit.data as cl_data
from chainlit.data.storage_clients import S3StorageClient




class CustomDataLayer(cl_data.BaseDataLayer):
    #implement all functions from cl_data.BaseDataLayer





#cl_data._data_layer = CustomDataLayer()