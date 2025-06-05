from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
import logging

def get_subscriptions_by_mgmt(mgmt: str):
    try:
        credential = DefaultAzureCredential()
        client = ResourceGraphClient(credential)
        query = QueryRequest(
            subscriptions=[],
            management_groups=[mgmt],
            query="""
                ResourceContainers
                | where type == 'microsoft.resources/subscriptions'
                | project subscriptionId = id, displayName = name
            """
        )
        result = client.resources(query)
        return result.data
    except Exception as e:
        logging.error(f"Error fetching subscriptions: {e}")
        return {"error": str(e)}