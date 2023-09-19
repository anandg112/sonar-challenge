from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elb,
    aws_ecs_patterns as ecs_patterns,
    aws_autoscaling as autoscaling,
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
        container_name: str,
        image_name: str,
        container_port: int,
        cpu_used: int,
        memory_used: int,
        asg_name: str,
        asg_instance_type: str,
        asg_machine_image: str,
        asg_desired_capacity: int,
    ) -> None:
        cluster_id = "ecscluster"
        service_id = "fargateservice"
        task_definition_id = "taskdefinition"
        container_id = "webapp"
        asg_id = "asg"

        cluster = ecs.Cluster(stack, id=cluster_id, cluster_name=cluster_name, vpc=vpc)
        task_definition = ecs.FargateTaskDefinition(stack, task_definition_id)
        task_definition.add_container(
            container_id,
            container_name=container_name,
            image=image_name,
            port_mappings=[ecs.PortMapping(container_port=container_port)],
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            stack,
            id=service_id,
            service_name=service_name,
            cluster=cluster,  # Required
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cpu=cpu_used,  # Default is 256
            desired_count=3,  # Default is 1
            memory_limit_mib=memory_used,  # Default is 512
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

        app_asg = autoscaling.AutoScalingGroup(
            stack,
            id=asg_id,
            vpc=vpc,
            instance_type=asg_instance_type,
            machine_image=asg_machine_image,
            associate_public_ip_address=False,
            auto_scaling_group_name=asg_name,
            desired_capacity=asg_desired_capacity,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )
        app_asg.add_security_group(security_group=app_security_group)
