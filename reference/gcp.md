# GCP service ids

Use these ids in `service`. Framework to cite in ADRs: Google Cloud Architecture Framework. Check the official documentation before relying on a service you are unsure about.

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
| `gcp.functions` | Short event-driven functions |
| `gcp.cloudrun` | Containers without managing servers |
| `gcp.gke` | Kubernetes is a requirement |
| `gcp.computeengine` | Full control of the instance |
| `gcp.batch` | Queued batch jobs |

## Storage and databases
| Id | Use when |
|---|---|
| `gcp.gcs` | Object storage, data lake landing |
| `gcp.cloudsql` | Managed relational engines |
| `gcp.alloydb` | PostgreSQL-compatible, high performance |
| `gcp.spanner` | Global relational consistency |
| `gcp.firestore` | Document store |
| `gcp.bigtable` | Wide-column at scale |
| `gcp.bigquery` | Data warehouse |
| `gcp.memorystore` | Caching |

## Integration and streaming
| Id | Use when |
|---|---|
| `gcp.apigateway` | APIs in front of functions and services |
| `gcp.pubsub` | Messaging and streaming ingestion |
| `gcp.eventarc` | Event routing |
| `gcp.workflows` | Workflow orchestration |
| `gcp.composer` | Managed Airflow |
| `gcp.dataflow` | Batch and stream pipelines |
| `gcp.datastream` | Database CDC |

## Analytics and ML
| Id | Use when |
|---|---|
| `gcp.dataproc` | Spark and Hadoop clusters |
| `gcp.vertexai` | Train, host and call models |
| `gcp.looker` | Dashboards |

## Security
| Id | Use when |
|---|---|
| `gcp.iam` | Identities and permissions |
| `gcp.kms` | Encryption keys |
| `gcp.secretmanager` | Secrets |
| `gcp.cloudarmor` | Web application firewall |
| `gcp.scc` | Threat detection and findings (Security Command Center) |
| `gcp.auditlogs` | API audit log |

## Network and edge
| Id | Use when |
|---|---|
| `gcp.vpc` | Network boundary |
| `gcp.loadbalancing` | Load balancing |
| `gcp.cdn` | CDN |
| `gcp.clouddns` | DNS |

## Operations and recovery
| Id | Use when |
|---|---|
| `gcp.monitoring` | Metrics and alerts |
| `gcp.logging` | Centralized logs |
| `gcp.backupdr` | Backup and disaster recovery |
