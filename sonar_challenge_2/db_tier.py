from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam,
    aws_kms as kms,
    aws_s3 as s3,
    RemovalPolicy,
    Stack,
)


class MySqlRDSAurora:
    def __init__(
        self,
        stack: Stack,
        vpc: ec2.Vpc,
        key_alias: str,
        db_backup_bucket_name: str,
        host_type: str,
        db_name: str,
        db_security_group: ec2.SecurityGroup,
        **kwargs
    ) -> None:
        db_id = "sonardb"
        bucket_id = "sonarbucket"
        kms_id = "db-kms"

        kms_custom_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "kms:Create*",
                        "kms:Describe*",
                        "kms:Enable*",
                        "kms:List*",
                        "kms:Put*",
                        "kms:DisableKey",
                        "kms:ScheduleKeyDeletion",
                    ],
                    principals=[iam.AccountRootPrincipal()],
                    resources=["*"],
                )
            ]
        )
        db_encryption_key = kms.Key(
            stack, id=kms_id, alias=key_alias, policy=kms_custom_policy
        )

        db_backup: s3.Bucket = s3.Bucket(
            stack,
            id=bucket_id,
            bucket_name=db_backup_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.db_cluster: rds.DatabaseCluster = rds.DatabaseCluster(
            stack,
            id=db_id,
            default_database_name=db_name,
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_04_0
            ),
            writer=rds.ClusterInstance.provisioned(
                id="sonar-writer",
                instance_type=host_type,
                auto_minor_version_upgrade=True,
                enable_performance_insights=False,  # T3.large does not support performance insights
                publicly_accessible=False,
            ),
            readers=[
                rds.ClusterInstance.provisioned(
                    "sonar-reader1", instance_type=host_type
                ),
                rds.ClusterInstance.provisioned(
                    "sonar-reader2", instance_type=host_type
                ),
                rds.ClusterInstance.provisioned(
                    "sonar-reader3", instance_type=host_type
                ),
            ],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            backup=rds.BackupProps(
                retention=Duration.days(7),
            ),
            storage_encrypted=True,
            storage_encryption_key=db_encryption_key,
            s3_export_buckets=[db_backup],
            security_groups=[db_security_group],
        )
