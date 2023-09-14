from aws_cdk import aws_s3 as s3, Stack, RemovalPolicy


class S3Bucket:
    def __init__(self, stack: Stack, name: str, **kwargs) -> None:
        bucket_id = "bucket"
        s3.Bucket(
            stack,
            id=bucket_id,
            bucket_name=name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
