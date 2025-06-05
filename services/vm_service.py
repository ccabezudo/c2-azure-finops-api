from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.monitor.query import MetricsQueryClient, MetricAggregationType
import datetime
import logging

def get_virtual_machines_handler(subscription_id: str):
    try:
        credential = DefaultAzureCredential()
        graph_client = ResourceGraphClient(credential)
        query = QueryRequest(
            subscriptions=[subscription_id],
            query="""
                resources
                | where type == "microsoft.compute/virtualmachines"
                | extend VMSize = tostring(properties.hardwareProfile.vmSize)
                | extend Cores = toint(extract("([0-9]+)", 1, VMSize))
                | extend HybridBenefitCost = iff(Cores >= 8, 8 * 2.70, Cores * 2.70),
                         NoHybridCost = Cores * 13.75
                | extend PowerState = properties.extended.instanceView.powerState.code
                | project VMName = name, ResourceGroup = resourceGroup, VMSize, Cores,
                          OperatingSystem = properties.storageProfile.osDisk.osType,
                          HybridBenefitStatus = coalesce(tostring(properties.licenseType), "None"),
                          HybridBenefitCost, NoHybridCost, PowerState,
                          ApplyHybridBenefitCommand = strcat(
                              "az vm update --resource-group ", resourceGroup, " --name ", name, " --set licenseType=Windows_Server"
                          ),
                          tags
                | order by VMName asc
            """
        )
        result = graph_client.resources(query)
        return result.data
    except Exception as e:
        logging.error(f"Error fetching VMs: {e}")
        return {"error": str(e)}
    

def get_vm_runtime_hours_handler(subscription_id: str, lookback_days: int):
    try:
        credential = DefaultAzureCredential()
        resource_client = ResourceManagementClient(credential, subscription_id)
        metrics_client = MetricsQueryClient(credential)
        vms = resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'")
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(days=lookback_days)
        results = []

        for vm in vms:
            resource_id = vm.id
            response = metrics_client.query_resource(
                resource_id,
                metric_names=["VmAvailabilityMetric"],
                timespan=(start_time, end_time),
                granularity=datetime.timedelta(hours=1),
                aggregations=[MetricAggregationType.AVERAGE],
            )
            runtime_hours = 0
            if response.metrics:
                for ts in response.metrics[0].timeseries:
                    for dp in ts.data:
                        if dp.average == 1:
                            runtime_hours += 1
            results.append({"resourceId": resource_id, "runtimeHours": runtime_hours})

        return results
    except Exception as e:
        logging.error(f"Error fetching runtime hours: {e}")
        return {"error": str(e)}
