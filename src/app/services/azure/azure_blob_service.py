from azure.storage.blob import BlobServiceClient, ContentSettings
from uuid import uuid4
from datetime import datetime
from app.core.config import settings
import os

class AzureBlobService:
    def __init__(self):
        self.connection_string = settings.azure_storage_blob_connection_string
        self.container_name = settings.azure_storage_container

        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )

        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )

    def upload_file(self, file_path: str, filename: str, content_type: str):
        blob_name = f"{uuid4()}_{filename}"
        blob_client = self.container_client.get_blob_client(blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )

        return {
            "blob_name": blob_name,
            "blob_url": blob_client.url,
            "uploaded_at": datetime.utcnow(),
        }
    
    def download_file(self, blob_name: str, download_path: str):
        """
        Download a file from Azure Blob Storage.

        :param blob_name: The name of the blob in Azure.
        :param download_path: Local path where the file will be saved.
        """
        blob_client = self.container_client.get_blob_client(blob_name)

        # Ensure the local directory exists
        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        with open(download_path, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())

        return {
            "downloaded_at": datetime.utcnow(),
            "local_path": download_path,
        }    
    

# azure_service = AzureBlobService()

# # Example: download a blob
# result = azure_service.download_file(
#     blob_name="3b9280c5-4944-40bc-947a-e73f2cb1bbc2_UAEU Hourly sheet June 2025-1.pdf",
#     download_path="/home/aiuser/Downloads/downloaded_file.pdf"
# )

# print(result)    