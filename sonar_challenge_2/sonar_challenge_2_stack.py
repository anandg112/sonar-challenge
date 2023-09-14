from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct
from sonar_challenge_2.db_tier import MySqlRDSAurora
from sonar_challenge_2.s3 import S3Bucket


class SonarChallenge2Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_name = "AppVpc"
        vpc_cidr = "10.0.0.0/16"
        vpc_construct_id = "vpc1"

        self.sonar_vpc = ec2.Vpc(
            self,
            id=vpc_construct_id,
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=3,
            nat_gateways=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC, name="Public", cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Compute",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    name="RDS",
                    cidr_mask=24,
                ),
            ],
        )

        # Create a MySQL RDS-Aurora tier
        dbTierRDS = MySqlRDSAurora(
            stack=self, vpc=self.sonar_vpc, key_alias="sonar-db-encrypt-key"
        )

        # Storage tier, create S3 bucket
        s3Tier = S3Bucket(stack=self, name="sonar-app-bucket-123")
