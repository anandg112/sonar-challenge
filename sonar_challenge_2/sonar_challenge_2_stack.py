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
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc_cidr: str,
        vpc_name: str,
        azs_for_subnets: list[str],
        db_name: str,
        kms_key_alias: str,
        db_backup_bucket: str,
        cluster_name: str,
        service_name: str,
        alb_name: str,
        asg_name: str,
        asg_desired_capacity: int,
        container_name: str,
        container_image: str,
        container_port: int,
        task_cpu: int,
        task_memory: int,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc_id = "vpc1"

        self.sonar_vpc = ec2.Vpc(
            self,
            id=vpc_id,
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            availability_zones=azs_for_subnets,
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
            db_name=db_name,
            key_alias=kms_key_alias,
            db_backup_bucket_name=db_backup_bucket,
            db_security_group=rds_security_group,
        )

        AppServices(
            stack=self,
            vpc=self.sonar_vpc,
            cluster_name=cluster_name,
            service_name=service_name,
            alb_name=alb_name,
            app_security_group=app_security_group,
            target_protocol=elb.ApplicationProtocol.HTTP,
            image_name=container_image,
            container_name=container_name,
            container_port=container_port,
            cpu_used=task_cpu,
            memory_used=task_memory,
            asg_name=asg_name,
            asg_desired_capacity=asg_desired_capacity,
            asg_machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            asg_instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.LARGE
            ),
        )
