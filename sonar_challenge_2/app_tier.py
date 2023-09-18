from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elb,
    aws_ecs_patterns as ecs_patterns,
)


class AppServices:
    def __init__(
        self,
        stack: Stack,
        vpc: ec2.Vpc,
        cluster_name: str,
        service_name: str,
        alb_name: str,
        app_security_group: ec2.SecurityGroup,
        target_protocol: elb.ApplicationProtocol.HTTP,
        container_port: int,
        imageName: ecs.ContainerImage.from_registry(""),
    ) -> None:
        cluster_id = "sonarcluster"
        service_id = "fargateservice"
        task_definition_id = "taskdefinition"
        container_id = "webapp"
        cluster = ecs.Cluster(stack, id=cluster_id, cluster_name=cluster_name, vpc=vpc)
        task_definition = ecs.FargateTaskDefinition(stack, task_definition_id)
        task_definition.add_container(
            container_id,
            container_name="podinfo",
            image=imageName,
            port_mappings=[ecs.PortMapping(container_port=container_port)],
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            stack,
            id=service_id,
            service_name=service_name,
            cluster=cluster,  # Required
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cpu=512,  # Default is 256
            desired_count=3,  # Default is 1
            # task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            # image=ecs.ContainerImage.from_registry(
            #     "docker.io/stefanprodan/podinfo:latest"
            # )
            # ),
            memory_limit_mib=1024,  # Default is 512
            public_load_balancer=True,  # Default is True
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            load_balancer_name=alb_name,
            security_groups=[app_security_group],
            target_protocol=target_protocol,
            task_definition=task_definition,
        )

        fargate_service.target_group.configure_health_check(path="/healthz")
