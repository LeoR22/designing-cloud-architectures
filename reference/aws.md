# AWS service ids

Use these ids in `service`. Frameworks to cite in ADRs: AWS Well-Architected Framework. Check the official documentation before relying on a service you are unsure about.

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
| `aws.lambda` | Short event-driven functions |
| `aws.fargate` | Containers without managing servers |
| `aws.ecs` | Container orchestration, simple setups |
| `aws.eks` | Kubernetes is a requirement |
| `aws.ec2` | Full control of the instance |
| `aws.batch` | Queued batch jobs |

## Storage and databases
| Id | Use when |
|---|---|
| `aws.s3` | Object storage, data lake landing |
| `aws.efs` | Shared file system |
| `aws.aurora` | Relational, high availability |
| `aws.rds` | Managed relational engines |
| `aws.dynamodb` | Key-value at scale |
| `aws.redshift` | Data warehouse |
| `aws.elasticache` | Caching |
| `aws.opensearch` | Search and log analytics |

## Integration and streaming
| Id | Use when |
|---|---|
| `aws.apigateway` | Public or private APIs |
| `aws.sqs` | Queues |
| `aws.sns` | Fan-out notifications |
| `aws.eventbridge` | Event bus and scheduling |
| `aws.stepfunctions` | Workflow orchestration |
| `aws.kinesis` | Streaming ingestion |
| `aws.msk` | Managed Kafka |
| `aws.appflow` | SaaS to AWS data transfer |
| `aws.dms` | Database migration and CDC |

## Analytics and ML
| Id | Use when |
|---|---|
| `aws.glue` | ETL and data catalog |
| `aws.athena` | SQL over S3 |
| `aws.emr` | Spark and Hadoop clusters |
| `aws.sagemaker` | Train and host models |
| `aws.bedrock` | Foundation model access |
| `aws.quicksight` | Dashboards |

## Security
| Id | Use when |
|---|---|
| `aws.iam` | Identities and permissions |
| `aws.kms` | Encryption keys |
| `aws.secretsmanager` | Secrets rotation |
| `aws.cognito` | App user identity |
| `aws.waf` | Web application firewall |
| `aws.guardduty` | Threat detection |
| `aws.securityhub` | Findings aggregation |
| `aws.cloudtrail` | API audit log |

## Network and edge
| Id | Use when |
|---|---|
| `aws.vpc` | Network boundary |
| `aws.alb` | HTTP load balancing |
| `aws.cloudfront` | CDN |
| `aws.route53` | DNS and failover routing |

## Operations and recovery
| Id | Use when |
|---|---|
| `aws.cloudwatch` | Metrics, logs, alarms |
| `aws.backup` | Centralized backups |
| `aws.config` | Configuration compliance |
