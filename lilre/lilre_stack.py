from aws_cdk import (
    Stack,
    aws_dynamodb,
    aws_lambda,
    aws_apigateway,
    aws_route53,
    aws_route53_targets,
    aws_certificatemanager as acm,
    aws_s3,
    aws_s3_deployment,
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
        cert = acm.DnsValidatedCertificate(self, "LilReCertificate", domain_name='lilre.link', cleanup_route53_records=True, hosted_zone=zone)
        
        links_api = aws_apigateway.LambdaRestApi(
            self, id='linksapi',
            rest_api_name='LinksAPI',
            handler=handler,
            proxy=False,
            disable_execute_api_endpoint=True,
            domain_name=aws_apigateway.DomainNameOptions(
                domain_name='lilre.link',
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
        
        links_api.root.add_method('GET')
        
        aws_route53.ARecord(
            self, 'LiliReAPIRecord',
            record_name='',
            zone=zone,
            target=aws_route53.RecordTarget.from_alias(aws_route53_targets.ApiGateway(links_api))
        )
        
        site_bucket = aws_s3.Bucket(
            self, 'LilReBucket',
            bucket_name='site.lilre.link',
            public_read_access=True,
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            access_control=aws_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
            website_index_document="index.html",
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        aws_s3_deployment.BucketDeployment(
            self, 'LilReStaticWebsite',
            sources=[aws_s3_deployment.Source.asset('./lilre-site/build')],
            destination_bucket=site_bucket
        )
        
        aws_route53.ARecord(
            self, "LilRESiteRecord",
            record_name='site',
            zone=zone,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.BucketWebsiteTarget(site_bucket)
            )
        )
