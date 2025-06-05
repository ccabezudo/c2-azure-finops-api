from azure.identity import DefaultAzureCredential
from azure.mgmt.managementgroups import ManagementGroupsAPI
import logging

def get_child_management_groups_handler(mgmt: str = None):
    try:
        credential = DefaultAzureCredential()
        client = ManagementGroupsAPI(credential)
        parent_id = mgmt or "root"
        result = client.entities.list(group_name=parent_id)

        return [
            {
                "id": item.id,
                "name": item.name,
                "displayName": item.display_name,
                "type": item.type
            }
            for item in result
            if item.type == "Microsoft.Management/managementGroups"
        ]
    except Exception as e:
        logging.error(f"Error fetching child management groups: {e}")
        return {"error": str(e)}
