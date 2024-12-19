# iam-auto-assume

## Background
IAM policies can be very subtle, fragile and frustrating. You might find yourself in a whack-a-mole loop:
- pushing Terraform IAM policy code changes
- waiting for CI/CD to apply the changes policy change
- waiting to see if the resource using the policy is happy or sad
- rinse and repeat

This python helper function enables you to easily assume into the target role from your laptop while you're tweaking policies and testing IAM access iteratively and quickly.

## Usage
`auto_assume(role_name)`

This function automatically updates the trust policy of a specified IAM role
to allow the current role to assume it. It then assumes the specified role and returns the 
temporary credentials which you can use to test access from your local machine
while you iteratively modify the IAM policies (e.g. in the console)

Don't use this in prod. This is for testing purposes only. It doesn't revert the trust policy change.

Example python script:
```
import sys
import boto
from iam_auto_assume import auto_assume

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
```
