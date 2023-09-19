#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import aws_ecs as ecs

from sonar_challenge_2.sonar_challenge_2_stack import SonarChallengeStack


app = cdk.App()
SonarChallengeStack(
    app,
    "SonarChallengeStack",
    vpc_cidr="10.0.0.0/16",
    vpc_name="sonar-vpc",
    azs_for_subnets=["us-east-1a", "us-east-1b", "us-east-1c"],
    db_name="sonardb",
    kms_key_alias="sonar-db-encrypt-key-6",
    db_backup_bucket="sonar-db-backup",
    cluster_name="sonar-cluster",
    service_name="sonar-fargate-service",
    alb_name="sonar-alb",
    asg_name="sonar-asg",
    asg_desired_capacity=3,
    container_name="podinfo",
    container_image=ecs.ContainerImage.from_registry(
        "docker.io/stefanprodan/podinfo:latest"
    ),
    task_cpu=512,  # vCPU
    task_memory=1024,  # in Mibs
    container_port=9898,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)
# If you don't specify 'env', this stack will be environment-agnostic.
# Account/Region-dependent features and context lookups will not work,
# but a single synthesized template can be deployed anywhere.

# Uncomment the next line to specialize this stack for the AWS Account
# and Region that are implied by the current CLI configuration.


# Uncomment the next line if you know exactly what Account and Region you
# want to deploy the stack to. */

# env=cdk.Environment(account='123456789012', region='us-east-1'),

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
app.synth()
