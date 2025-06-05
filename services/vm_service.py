from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.monitor.query import MetricsQueryClient, MetricAggregationType
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.advisor import AdvisorManagementClient
from azure.mgmt.policyinsights.models import QueryOptions
import datetime
import logging
from collections import defaultdict

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


def get_vm_policy_compliance_handler(subscription_id: str):
    try:
        credential = DefaultAzureCredential()

        # Get all VMs in the subscription
        resource_client = ResourceManagementClient(credential, subscription_id)
        vms = list(resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'"))

        policy_client = PolicyInsightsClient(credential, subscription_id)

                # Prepare result as a dict grouped by resourceId
        grouped_results = defaultdict(list)

        for vm in vms:
            resource_id = vm.id

            # Fetch policy states for each VM
            query_results = policy_client.policy_states.list_query_results_for_resource(
                policy_states_resource="latest",
                resource_id=resource_id,
                query_options=QueryOptions(top=1000)
            )

            for state in query_results:
                grouped_results[resource_id].append({
                    "policyAssignment": state.policy_assignment_name,
                    "policyDefinition": state.policy_definition_name,
                    "complianceState": state.compliance_state,
                    "timestamp": state.timestamp.isoformat() if state.timestamp else None
                })

        # Convert to list of dicts
        final_result = [
            {
                "resourceId": resource_id,
                "policies": policies
            }
            for resource_id, policies in grouped_results.items()
        ]

        return final_result
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return {"error": str(e)}


def get_vm_advisor_recommendations_handler(subscription_id: str):
    logging.info(f"Fetching Advisor recommendations for subscription: {subscription_id}")

    try:
        credential = DefaultAzureCredential()
        advisor_client = AdvisorManagementClient(credential, subscription_id)

        # Fetch all recommendations in the subscription
        recommendations = advisor_client.recommendations.list()

        grouped = defaultdict(list)

        for rec in recommendations:
            resource_id = rec.resource_metadata.resource_id if rec.resource_metadata else None

            if resource_id and "Microsoft.Compute/virtualMachines" in resource_id:
                grouped[resource_id].append({
                    "recommendationName": rec.name,
                    "category": rec.category if rec.category else None,
                    "impact": rec.impact if rec.impact else None,
                    "risk": rec.risk if rec.risk else None,
                    "shortDescription": rec.short_description.problem if rec.short_description else None,
                    "remediation": rec.short_description.solution if rec.short_description else None
                })

        # Format as list of objects
        final_result = [
            {
                "resourceId": resource_id,
                "recommendations": recommendations
            }
            for resource_id, recommendations in grouped.items()
        ]

        return final_result

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return {"error": str(e)}
    
def get_vm_metrics_summary_handler(
    subscription_id: str,
    lookback_hours: int
):
    logging.info(f"Fetching CPU and memory metrics for subscription: {subscription_id}")

    try:
        credential = DefaultAzureCredential()

        # Initialize clients
        resource_client = ResourceManagementClient(credential, subscription_id)
        metrics_client = MetricsQueryClient(credential)

        # Time range
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(hours=lookback_hours)

        vms = list(resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'"))

        results = []

        for vm in vms:
            resource_id = vm.id

            response = metrics_client.query_resource(
                resource_id,
                metric_names=["Percentage CPU", "Available Memory Bytes"],
                timespan=(start_time, end_time),
                aggregations=[
                    MetricAggregationType.AVERAGE,
                    MetricAggregationType.MINIMUM,
                    MetricAggregationType.MAXIMUM
                ]
            )

            metrics = {m.name: m for m in response.metrics}

            vm_result = {
                "resourceId": resource_id,
                "cpu": {},
                "memory": {}
            }

            if "Percentage CPU" in metrics:
                timeseries = metrics["Percentage CPU"].timeseries[0].data
                vm_result["cpu"] = {
                    "average": _safe_metric_avg(timeseries, "average"),
                    "min": _safe_metric_avg(timeseries, "minimum"),
                    "max": _safe_metric_avg(timeseries, "maximum")
                }

            if "Available Memory Bytes" in metrics:
                timeseries = metrics["Available Memory Bytes"].timeseries[0].data
                vm_result["memory"] = {
                    "average": _safe_metric_avg(timeseries, "average"),
                    "min": _safe_metric_avg(timeseries, "minimum"),
                    "max": _safe_metric_avg(timeseries, "maximum")
                }

            results.append(vm_result)

        return results

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return {"error": str(e)}


def _safe_metric_avg(data_points, field):
    values = [getattr(dp, field) for dp in data_points if getattr(dp, field) is not None]
    return round(sum(values) / len(values), 2) if values else None



def get_vm_metrics_timeseries_handler(
    subscription_id: str,
    lookback_hours: int
):
    logging.info(f"Fetching time series for CPU and memory for subscription: {subscription_id}")

    try:
        credential = DefaultAzureCredential()

        resource_client = ResourceManagementClient(credential, subscription_id)
        metrics_client = MetricsQueryClient(credential)

        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(hours=lookback_hours)

        vms = list(resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'"))

        results = []

        for vm in vms:
            resource_id = vm.id

            response = metrics_client.query_resource(
                resource_id,
                metric_names=["Percentage CPU", "Available Memory Bytes"],
                timespan=(start_time, end_time),
                granularity=datetime.timedelta(minutes=5),
                aggregations=["Average"]
            )

            vm_metrics = {
                "resourceId": resource_id,
                "metrics": []
            }

            for metric in response.metrics:
                metric_data = {
                    "name": metric.name,
                    "unit": metric.unit,  # FIXED HERE
                    "timeSeries": []
                }

                for ts in metric.timeseries:
                    for dp in ts.data:
                        metric_data["timeSeries"].append({
                            "timestamp": dp.timestamp.isoformat(),
                            "average": dp.average
                        })

                vm_metrics["metrics"].append(metric_data)

            results.append(vm_metrics)

        return results

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return {"error": str(e)}