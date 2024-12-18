"""
iam_auto_assume.py

Here are some helper functions, primarily:
auto_assume(role_name): automatically updates the trust policy of a specified IAM role
to allow the current role to assume it. It then assumes the specified role and returns the 
temporary credentials which you can use to test access from your local machine
while you iteratively modify the IAM policies.

Don't use in prod. This is for testing purposes only. It doesn't revert the trust policy change.

import sys
from iam_auto_assume import auto_assume

def test_access():
    role_name = sys.argv[1]
    credentials = auto_assume(role_name)
    # then do stuff to test your policies e.g.
    s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    print(s3_client.list_buckets())
"""
import boto3
import botocore.exceptions
import json
import time


def get_current_account_id():
    """
    Determines the AWS account ID of the current runtime.

    :return: AWS account ID as a string.
    """
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        return identity['Account']
    except Exception as e:
        print(f"An error occurred while retrieving the current account ID: {str(e)}")
        return None


def construct_role_arn(role_name):
    """
    Constructs a valid IAM role ARN given the role name and account ID.

    :param role_name: Name of the IAM role.
    :param account_id: AWS account ID where the role resides.
    :return: Constructed IAM role ARN.
    """
    account_id = get_current_account_id()
    return f"arn:aws:iam::{account_id}:role/{role_name}"

    
def get_current_role_arn():
    """
    Determines the ARN of the current runtime role.

    :return: ARN of the current role.
    """
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        return identity['Arn']
    except Exception as e:
        print(f"An error occurred while retrieving the current role ARN: {str(e)}")
        return None


def update_trust_policy(target_role_name, current_role_arn):
    """
    Updates the trust policy of the specified IAM role to allow the current role to assume it.

    :param target_role_name: Name of the target IAM role to update.
    :param current_role_arn: ARN of the current role that should be allowed to assume the target role.
    """
    # Initialize the IAM client
    iam_client = boto3.client('iam')

    try:
        # Get the existing trust policy of the target role
        response = iam_client.get_role(RoleName=target_role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']

        # Check if the current role is already in the trust policy
        for statement in trust_policy.get("Statement", []):
            if statement.get("Effect") == "Allow" and current_role_arn in statement.get("Principal", {}).get("AWS", []):
                print(f"The role {current_role_arn} is already allowed to assume {target_role_name}.")
                return

        # Add the current role ARN to the trust policy
        new_statement = {
            "Effect": "Allow",
            "Principal": {"AWS": current_role_arn},
            "Action": "sts:AssumeRole"
        }
        trust_policy["Statement"].append(new_statement)

        # Update the role's trust policy
        iam_client.update_assume_role_policy(
            RoleName=target_role_name,
            PolicyDocument=json.dumps(trust_policy)
        )
        print(f"Updated the trust policy for role {target_role_name} to allow {current_role_arn} to assume it.")
        print("Waiting 10s for the trust policy update to propagate...")
        # kind of hacky but I found if you try to early it caches the failed response
        time.sleep(10)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Function to assume a role
def assume_role(role_arn):
    sts_client = boto3.client('sts')
    try:
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="TestRoleSession"
        )
        return assumed_role['Credentials']
    except botocore.exceptions.ClientError as e:
        print(f"Failed to assume role: {e}")
        return None

def auto_assume(role_name):
    # Assume the test role
    update_trust_policy(role_name, get_current_role_arn())
    credentials = assume_role(construct_role_arn(role_name))
    return credentials
