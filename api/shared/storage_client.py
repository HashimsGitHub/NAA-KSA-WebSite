"""
NUST KSA Alumni Portal

Shared Azure Storage Client

Author: Hashim Hilal
"""

import json
import os
from pathlib import Path

from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient


class StorageClient:
    """
    Singleton storage client.

    Provides access to Azure Tables and Azure Blob Storage.
    """

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()

        return cls._instance

    def _initialise(self):

        connection_string = self._get_connection_string()

        self.table_service = TableServiceClient.from_connection_string(
            connection_string
        )

        self.blob_service = BlobServiceClient.from_connection_string(
            connection_string
        )

    # ----------------------------------------------------------
    # Connection String
    # ----------------------------------------------------------

    def _get_connection_string(self):

        # Azure Functions / Static Web Apps

        connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if connection:
            return connection

        # Local Development

        settings = Path(__file__).parents[1] / "local.settings.json"

        if settings.exists():

            with open(settings, "r") as f:
                config = json.load(f)

            return config["Values"]["AZURE_STORAGE_CONNECTION_STRING"]

        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING not found."
        )

    # ----------------------------------------------------------
    # Tables
    # ----------------------------------------------------------

    def table(self, table_name):

        return self.table_service.get_table_client(table_name)

    # ----------------------------------------------------------
    # Blob Containers
    # ----------------------------------------------------------

    def container(self, container_name):

        return self.blob_service.get_container_client(container_name)
