import aws_cdk as core
import aws_cdk.assertions as assertions

from lilre.lilre_stack import LilreStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lilre/lilre_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LilreStack(app, "lilre")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
