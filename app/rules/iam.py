"""IAM audit rules for Sentinel."""

import boto3


def find_users_without_mfa() -> list[str]:
    """Return names of IAM users that have no MFA device enabled."""
    iam = boto3.client("iam")
    response = iam.list_users()

    users_without_mfa: list[str] = []

    for user in response["Users"]:
        user_name = user["UserName"]
        mfa_response = iam.list_mfa_devices(UserName=user_name)

        if not mfa_response["MFADevices"]:
            users_without_mfa.append(user_name)

    return users_without_mfa
