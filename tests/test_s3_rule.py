"""Tests for S3 audit rules."""

from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from app.rules.s3 import (
    ALL_USERS_GROUP_URI,
    find_public_s3_buckets,
    find_unencrypted_s3_buckets,
)


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


def _make_encrypted_bucket(s3_client, bucket_name: str) -> None:
    """Helper: create a bucket and apply default SSE-S3 (AES256) encryption."""
    s3_client.create_bucket(Bucket=bucket_name)
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )


# --- find_public_s3_buckets tests ---


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


# --- find_unencrypted_s3_buckets tests ---


def test_unencrypted_empty_account_returns_empty_list(s3_client):
    assert find_unencrypted_s3_buckets() == []


def test_encrypted_bucket_not_flagged(s3_client):
    _make_encrypted_bucket(s3_client, "encrypted-bucket")
    assert find_unencrypted_s3_buckets() == []


def test_unencrypted_bucket_is_flagged(s3_client):
    s3_client.create_bucket(Bucket="unencrypted-bucket")
    assert find_unencrypted_s3_buckets() == ["unencrypted-bucket"]


def test_unencrypted_mixed_only_unencrypted_returned(s3_client):
    _make_encrypted_bucket(s3_client, "encrypted-1")
    s3_client.create_bucket(Bucket="unencrypted-1")
    _make_encrypted_bucket(s3_client, "encrypted-2")
    s3_client.create_bucket(Bucket="unencrypted-2")

    result = find_unencrypted_s3_buckets()

    assert sorted(result) == ["unencrypted-1", "unencrypted-2"]


def test_unrelated_client_error_propagates():
    """Errors other than missing-encryption code must not be swallowed."""
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {"Buckets": [{"Name": "some-bucket"}]}
    mock_client.get_bucket_encryption.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Denied"}},
        operation_name="GetBucketEncryption",
    )

    with patch("app.rules.s3.boto3.client", return_value=mock_client):
        with pytest.raises(ClientError) as exc_info:
            find_unencrypted_s3_buckets()

    assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
