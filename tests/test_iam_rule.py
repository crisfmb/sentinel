"""Tests for IAM audit rules."""

import boto3
import pytest
from moto import mock_aws

from app.rules.iam import find_users_without_mfa


@pytest.fixture
def iam_client():
    """Yield a mocked IAM client. All AWS calls in the test are intercepted."""
    with mock_aws():
        yield boto3.client("iam", region_name="us-east-1")


def _make_user_with_mfa(iam_client, user_name: str) -> None:
    """Helper: create an IAM user and attach an enabled virtual MFA device."""
    iam_client.create_user(UserName=user_name)
    device = iam_client.create_virtual_mfa_device(
        VirtualMFADeviceName=f"{user_name}-mfa"
    )
    iam_client.enable_mfa_device(
        UserName=user_name,
        SerialNumber=device["VirtualMFADevice"]["SerialNumber"],
        AuthenticationCode1="123456",
        AuthenticationCode2="234567",
    )


def test_empty_account_returns_empty_list(iam_client):
    assert find_users_without_mfa() == []


def test_user_with_mfa_not_flagged(iam_client):
    _make_user_with_mfa(iam_client, "secure-user")
    assert find_users_without_mfa() == []


def test_user_without_mfa_is_flagged(iam_client):
    iam_client.create_user(UserName="exposed-user")
    assert find_users_without_mfa() == ["exposed-user"]


def test_mixed_users_only_no_mfa_returned(iam_client):
    _make_user_with_mfa(iam_client, "secure-1")
    iam_client.create_user(UserName="exposed-1")
    _make_user_with_mfa(iam_client, "secure-2")
    iam_client.create_user(UserName="exposed-2")

    result = find_users_without_mfa()

    assert sorted(result) == ["exposed-1", "exposed-2"]
