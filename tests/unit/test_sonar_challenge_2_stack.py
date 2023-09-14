import aws_cdk as core
import aws_cdk.assertions as assertions

from sonar_challenge_2.sonar_challenge_2_stack import SonarChallenge2Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in sonar_challenge_2/sonar_challenge_2_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SonarChallenge2Stack(app, "sonar-challenge-2")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
