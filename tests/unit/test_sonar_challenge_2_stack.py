import aws_cdk.assertions as assertions
import aws_cdk as cdk
from aws_cdk import aws_ecs as ecs
from sonar_challenge_2.sonar_challenge_2_stack import SonarChallengeStack


# example tests. To run these tests, uncomment this file along with the example
# resource in sonar_challenge_2/sonar_challenge_2_stack.py


def test_rds_cluster_created():
    app = cdk.App()
    test_stack = SonarChallengeStack(
        app,
        "SonarChallengeTestStack",
        vpc_cidr="10.0.0.0/16",
        vpc_name="sonar-test-vpc",
        azs_for_subnets=["us-east-1a", "us-east-1b", "us-east-1c"],
        db_name="sonardb",
        kms_key_alias="sonar-db-encrypt-key-6",
        db_backup_bucket="sonar-db-backup",
        cluster_name="sonar-test-cluster",
        service_name="sonar-test-fargate-service",
        alb_name="sonar-test-alb",
        asg_name="sonar-test-asg",
        asg_desired_capacity=3,
        container_name="test-podinfo",
        container_image=ecs.ContainerImage.from_registry(
            "docker.io/stefanprodan/podinfo:latest"
        ),
        task_cpu=512,  # vCPU
        task_memory=1024,  # in Mibs
        container_port=9898,
    )

    template = assertions.Template.from_stack(test_stack)

    template.has_resource_properties(
        "AWS::RDS::DBCluster", {"EngineVersion": "8.0.mysql_aurora.3.04.0"}
    )

    template.has_resource_properties("AWS::RDS::DBCluster", {"StorageEncrypted": True})
