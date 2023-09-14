from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam,
    aws_kms as kms,
    Stack,
)


class MySqlRDSAurora:
    def __init__(self, stack: Stack, vpc: ec2.Vpc, key_alias: str, **kwargs) -> None:
        db_construct_id = "db1"
        db_instance_type = ec2.InstanceType.of(
            ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.LARGE
        )
        kms_construct_id = "db-kms"

        kms_custom_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "kms:Create*",
                        "kms:Describe*",
                        "kms:Enable*",
                        "kms:List*",
                        "kms:Put*",
                    ],
                    principals=[iam.AccountRootPrincipal()],
                    resources=["*"],
                )
            ]
        )
        db_encryption_key = kms.Key(
            stack, id=kms_construct_id, alias=key_alias, policy=kms_custom_policy
        )

        self.dbcluster: rds.DatabaseCluster = rds.DatabaseCluster(
            stack,
            id=db_construct_id,
            default_database_name="sonar-db",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_04_0
            ),
            writer=rds.ClusterInstance.provisioned(
                id="sonar-writer",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.R6G, ec2.InstanceSize.XLARGE2
                ),
                auto_minor_version_upgrade=True,
                enable_performance_insights=True,
                publicly_accessible=False,
            ),
            readers=[
                rds.ClusterInstance.provisioned(
                    "sonar-reader1", instance_type=db_instance_type
                ),
                rds.ClusterInstance.provisioned(
                    "sonar-reader2", instance_type=db_instance_type
                ),
                rds.ClusterInstance.provisioned(
                    "sonar-reader3", instance_type=db_instance_type
                ),
            ],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                # availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            backup=rds.BackupProps(
                retention=Duration.days(7),
            ),
            storage_encrypted=True,
            storage_encryption_key=db_encryption_key,
        )
