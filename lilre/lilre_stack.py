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
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_events,
    aws_events_targets,
    Duration,
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

        # Create the identity global secondary index
        link_table.add_global_secondary_index(
            read_capacity=1,
            write_capacity=1,
            index_name='identity-index',
            projection_type=aws_dynamodb.ProjectionType.ALL,
            partition_key=aws_dynamodb.Attribute(name='identity_hash', type=aws_dynamodb.AttributeType.STRING)
        )
        
        # Create lambda that will call the dynamodb table
        handler = aws_lambda.Function(
            self, "HandleRequest",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            architecture=aws_lambda.Architecture.ARM_64,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('./lambdas/api_lambda')
        )
        
        # Give the lambda access to our table
        link_table.grant_read_write_data(handler)
        
        zone = aws_route53.HostedZone.from_lookup(self, 'lilre.link', domain_name='lilre.link')
        root_cert = acm.DnsValidatedCertificate(self, "LilReAPICertificate", domain_name='lilre.link', cleanup_route53_records=True, hosted_zone=zone)
        site_cert = acm.Certificate(
            self, 'LilReSiteCertificate', domain_name='site.lilre.link', 
            validation=acm.CertificateValidation.from_dns(hosted_zone=zone)
        )
        
        # Create the api gateway object
        links_api = aws_apigateway.LambdaRestApi(
            self, id='linksapi',
            rest_api_name='LinksAPI',
            handler=handler,
            proxy=False,
            disable_execute_api_endpoint=True,
            domain_name=aws_apigateway.DomainNameOptions(
                domain_name='lilre.link',
                certificate=root_cert,
                security_policy=aws_apigateway.SecurityPolicy.TLS_1_2,
                endpoint_type=aws_apigateway.EndpointType.EDGE
            ),
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=['https://site.lilre.link']
                #allow_origins=['*']
            )
        )
        # Create the /link and link/id routes
        link_resource = links_api.root.add_resource('link')
        link_with_id = link_resource.add_resource('{id}')
        link_resource.add_method('POST')
        link_with_id.add_method('GET')
        link_with_id.add_method('DELETE')
        
        # Create the /id route
        id_resource = links_api.root.add_resource('{id}')
        id_resource.add_method('GET')
        
        # Reroute user to the main page
        links_api.root.add_method('GET')

        # Get all of the user's links
        userlinks = links_api.root.add_resource('userlinks')
        userlinks.add_method('GET')

        # Give the API it's record on the Domain
        aws_route53.ARecord(
            self, 'LiliReAPIRecord',
            record_name='',
            zone=zone,
            target=aws_route53.RecordTarget.from_alias(aws_route53_targets.ApiGateway(links_api))
        )

        # Create the bucket where the page resides
        site_bucket = aws_s3.Bucket(
            self, 'LilReBucket',
            bucket_name='site.lilre.link',
            auto_delete_objects=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create the bucket deployment object (to deploy the react app)
        aws_s3_deployment.BucketDeployment(
            self, 'LilReStaticWebsite',
            sources=[aws_s3_deployment.Source.asset('./lilre-site/build')],
            destination_bucket=site_bucket
        )
        
        # Give create the CloudFront identity and give it access to the bucket
        origin_access = aws_cloudfront.OriginAccessIdentity(self, 'LileReAccessIdentity')
        site_bucket.grant_read(origin_access)

        # Create the CloudFront Distrubution
        distribution = aws_cloudfront.Distribution(
            self, 'LilReDistribution',
            default_root_object='index.html',
            default_behavior={
                'origin': aws_cloudfront_origins.S3Origin(site_bucket, origin_access_identity=origin_access),
                'viewer_protocol_policy': aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            },
            certificate=site_cert,
            minimum_protocol_version=aws_cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            domain_names=['site.lilre.link']
        )

        # Give the CloudFront Distribution it's record
        aws_route53.ARecord(
            self, 'LilRESiteRecord',
            record_name='site',
            zone=zone,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(distribution)
            )
        )

        # Setup Anti-Entropy
        antientropy_function = aws_lambda.Function(
            self, "lilre_anti_entropy_function",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            architecture=aws_lambda.Architecture.ARM_64,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('./lambdas/anti_entropy')
        )
        link_table.grant_read_write_data(antientropy_function)
        antientropy_rule = aws_events.Rule(
            self, 'lilre_antientropy_rule',
            schedule=aws_events.Schedule.rate(Duration.days(7))
        )
        antientropy_rule.add_target(
            aws_events_targets.LambdaFunction(antientropy_function)
        )
