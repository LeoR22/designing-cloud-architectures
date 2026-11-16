# Azure service ids

Use these ids in `service`. Framework to cite in ADRs: Azure Well-Architected Framework. The Microsoft Learn documentation is the source to confirm a service before relying on it.

## Contents
- Compute and containers
- Storage and databases
- Integration and streaming
- Analytics and ML
- Security
- Network and edge
- Operations and recovery

## Compute and containers
| Id | Use when |
|---|---|
| `azure.functions` | Short event-driven functions |
| `azure.containerapps` | Containers without managing servers |
| `azure.appservice` | Web apps and APIs |
| `azure.aks` | Kubernetes is a requirement |
| `azure.vm` | Full control of the machine |
| `azure.batch` | Queued batch jobs |

## Storage and databases
| Id | Use when |
|---|---|
| `azure.blobstorage` | Object storage, data lake landing |
| `azure.datalakegen2` | Hierarchical data lake storage |
| `azure.sqldatabase` | Managed relational, SQL Server family |
| `azure.postgresql` | Managed PostgreSQL |
| `azure.cosmosdb` | Multi-model, globally distributed |
| `azure.synapse` | Data warehouse and analytics |
| `azure.redis` | Caching |

## Integration and streaming
| Id | Use when |
|---|---|
| `azure.apim` | API management |
| `azure.servicebus` | Queues and topics |
| `azure.eventgrid` | Event routing |
| `azure.eventhubs` | Streaming ingestion, Kafka-compatible |
| `azure.logicapps` | Workflow orchestration |
| `azure.datafactory` | ETL and data movement |

## Analytics and ML
| Id | Use when |
|---|---|
| `azure.databricks` | Spark and lakehouse |
| `azure.machinelearning` | Train and host models |
| `azure.powerbi` | Dashboards |

## Security
| Id | Use when |
|---|---|
| `azure.entra` | Identities and access (Microsoft Entra ID) |
| `azure.keyvault` | Keys and secrets |
| `azure.defender` | Threat protection (Microsoft Defender for Cloud) |
| `azure.sentinel` | SIEM and incident response |
| `azure.firewall` | Network firewall |

## Network and edge
| Id | Use when |
|---|---|
| `azure.vnet` | Network boundary |
| `azure.frontdoor` | Global entry point, CDN and WAF |
| `azure.appgateway` | Regional HTTP load balancing |
| `azure.dns` | DNS |

## Operations and recovery
| Id | Use when |
|---|---|
| `azure.monitor` | Metrics, logs and alerts |
| `azure.backup` | Backups |
| `azure.siterecovery` | Disaster recovery replication |
