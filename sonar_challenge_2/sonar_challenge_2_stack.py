from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_ecs as ecs,
)
from constructs import Construct
from sonar_challenge_2.app_tier import AppServices
from sonar_challenge_2.db_tier import MySqlRDSAurora

class SonarChallengeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_name = "sonar-vpc"
        vpc_cidr = "10.0.0.0/16"
        vpc_id = "vpc1"

        self.sonar_vpc = ec2.Vpc(
            self,
            id=vpc_id,
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
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3,
                    subnets=[
                        ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
                    ],
                )
            },
        )

        # Security Group for Load Balancer and allow inbound HTTP traffic from Internet
        alb_security_group = ec2.SecurityGroup(
            self, "SONAR-ALB-SG", vpc=self.sonar_vpc, allow_all_outbound=True
        )
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(80)
        )

        # Security Group for App TIER and allow inbound HTTP traffic from Load Balancer only
        app_security_group = ec2.SecurityGroup(
            self, "SONAR-APP-SG", vpc=self.sonar_vpc, allow_all_outbound=True
        )
        app_security_group.add_ingress_rule(
            alb_security_group, connection=ec2.Port.tcp(80)
        )

        # Security Group for RDS and allow inbound traffic from App EC2 only
        rds_security_group: ec2.SecurityGroup = ec2.SecurityGroup(
            self, "SONAR-RDS-SG", vpc=self.sonar_vpc, allow_all_outbound=True
        )
        rds_security_group.add_ingress_rule(
            app_security_group, connection=ec2.Port.tcp(3306)
        )

        # Create a MySQL RDS-Aurora tier
        MySqlRDSAurora(
            stack=self,
            vpc=self.sonar_vpc,
            host_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.LARGE),
            db_name="sonardb",
            key_alias="sonar-db-encrypt-key-4",
            db_backup_bucket_name="sonar-db-backup",
            db_security_group=rds_security_group,
        )

        AppServices(
            stack=self,
            vpc=self.sonar_vpc,
            cluster_name="sonar-cluster",
            service_name="sonar-fargate-service",
            alb_name="sonar-alb",
            app_security_group=app_security_group,
            target_protocol=elb.ApplicationProtocol.HTTP,
            imageName=ecs.ContainerImage.from_registry(
                "docker.io/stefanprodan/podinfo:latest"
            ),
            container_port=9898,
        )
