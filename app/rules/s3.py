"""S3 audit rules for Sentinel."""

import boto3

ALL_USERS_GROUP_URI = "http://acs.amazonaws.com/groups/global/AllUsers"


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
