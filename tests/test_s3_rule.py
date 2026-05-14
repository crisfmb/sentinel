"""Tests for S3 audit rules."""

import boto3
import pytest
from moto import mock_aws

from app.rules.s3 import ALL_USERS_GROUP_URI, find_public_s3_buckets


@pytest.fixture
def s3_client():
    """Yield a mocked S3 client. All AWS calls in the test are intercepted."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


def _make_public(s3_client, bucket_name: str, permission: str = "READ") -> None:
    """Helper: create a bucket and grant the given permission to AllUsers."""
    s3_client.create_bucket(Bucket=bucket_name)
    s3_client.put_bucket_acl(
        Bucket=bucket_name,
        AccessControlPolicy={
            "Owner": s3_client.get_bucket_acl(Bucket=bucket_name)["Owner"],
            "Grants": [
                {
                    "Grantee": {"Type": "Group", "URI": ALL_USERS_GROUP_URI},
                    "Permission": permission,
                }
            ],
        },
    )


def test_empty_account_returns_empty_list(s3_client):
    assert find_public_s3_buckets() == []


def test_private_bucket_not_flagged(s3_client):
    s3_client.create_bucket(Bucket="private-bucket")
    assert find_public_s3_buckets() == []


def test_public_bucket_is_flagged(s3_client):
    _make_public(s3_client, "public-bucket")
    assert find_public_s3_buckets() == ["public-bucket"]


def test_mixed_buckets_only_public_returned(s3_client):
    s3_client.create_bucket(Bucket="private-1")
    _make_public(s3_client, "public-1")
    s3_client.create_bucket(Bucket="private-2")
    _make_public(s3_client, "public-2")

    result = find_public_s3_buckets()

    assert sorted(result) == ["public-1", "public-2"]


def test_bucket_with_multiple_public_grants_appears_once(s3_client):
    """A bucket granting both READ and WRITE to AllUsers should appear once."""
    s3_client.create_bucket(Bucket="double-grant")
    s3_client.put_bucket_acl(
        Bucket="double-grant",
        AccessControlPolicy={
            "Owner": s3_client.get_bucket_acl(Bucket="double-grant")["Owner"],
            "Grants": [
                {
                    "Grantee": {"Type": "Group", "URI": ALL_USERS_GROUP_URI},
                    "Permission": "READ",
                },
                {
                    "Grantee": {"Type": "Group", "URI": ALL_USERS_GROUP_URI},
                    "Permission": "WRITE",
                },
            ],
        },
    )

    result = find_public_s3_buckets()

    assert result == ["double-grant"]
