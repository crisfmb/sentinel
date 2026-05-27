"""S3 audit rules for Sentinel."""

import boto3
from botocore.exceptions import ClientError

ALL_USERS_GROUP_URI = "http://acs.amazonaws.com/groups/global/AllUsers"
NO_ENCRYPTION_ERROR_CODE = "ServerSideEncryptionConfigurationNotFoundError"


def find_public_s3_buckets() -> list[str]:
    """Return names of S3 buckets that grant access to AllUsers."""
    s3 = boto3.client("s3")
    response = s3.list_buckets()

    public_buckets: list[str] = []

    for bucket in response["Buckets"]:
        bucket_name = bucket["Name"]
        acl = s3.get_bucket_acl(Bucket=bucket_name)

        for grant in acl["Grants"]:
            grantee = grant["Grantee"]
            if grantee.get("URI") == ALL_USERS_GROUP_URI:
                public_buckets.append(bucket_name)
                break

    return public_buckets


def find_unencrypted_s3_buckets() -> list[str]:
    """Return names of S3 buckets without server-side encryption configured."""
    s3 = boto3.client("s3")
    response = s3.list_buckets()

    unencrypted_buckets: list[str] = []

    for bucket in response["Buckets"]:
        bucket_name = bucket["Name"]
        try:
            s3.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == NO_ENCRYPTION_ERROR_CODE:
                unencrypted_buckets.append(bucket_name)
            else:
                # Anything else (auth denied, throttling, network) is not our
                # signal — let it bubble up so callers can handle it.
                raise

    return unencrypted_buckets
