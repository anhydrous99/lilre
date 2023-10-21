from aws_cdk import (
    Stack,
    aws_dynamodb,
    aws_lambda,
    aws_apigateway,
    aws_route53,
    aws_route53_targets,
    aws_certificatemanager as acm,
    RemovalPolicy
)
from constructs import Construct

class LilreStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create link dynamodb table
        link_table = aws_dynamodb.Table(
            self, 'LinkTable', 
            table_name='Links', 
            read_capacity=1, 
            write_capacity=1, 
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=aws_dynamodb.Attribute(name='id', type=aws_dynamodb.AttributeType.STRING)
        )
        
        # Create lambda that will call the dynamodb table
        handler = aws_lambda.Function(
            self, "HandleRequest",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            architecture=aws_lambda.Architecture.ARM_64,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('./lambda')
        )
        
        # Give the lambda access to our table
        link_table.grant_read_write_data(handler)
        
        zone = aws_route53.HostedZone.from_lookup(self, 'lilre.link', domain_name='lilre.link')
        cert = acm.DnsValidatedCertificate(self, "LilReCertificate", domain_name='api.lilre.link', cleanup_route53_records=True, hosted_zone=zone)
        
        links_api = aws_apigateway.LambdaRestApi(
            self, id='linksapi',
            rest_api_name='LinksAPI',
            handler=handler,
            proxy=False,
            disable_execute_api_endpoint=True,
            domain_name=aws_apigateway.DomainNameOptions(
                domain_name='api.lilre.link',
                certificate=cert,
                security_policy=aws_apigateway.SecurityPolicy.TLS_1_2,
                endpoint_type=aws_apigateway.EndpointType.EDGE
            )
        )
        link_resource = links_api.root.add_resource('link')
        link_with_id = link_resource.add_resource('{id}')
        link_resource.add_method('POST')
        link_with_id.add_method('GET')
        
        id_resource = links_api.root.add_resource('{id}')
        id_resource.add_method('GET')
        
        aws_route53.ARecord(
            self, 'LiliReAPIRecord',
            record_name='api',
            zone=zone,
            target=aws_route53.RecordTarget.from_alias(aws_route53_targets.ApiGateway(links_api))
        )
