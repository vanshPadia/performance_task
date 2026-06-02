# performance_task/lambda/python/lambda.py
import json
import boto3
import time
import urllib3

# Initialize AWS Clients
ssm_client = boto3.client('ssm')
asg_client = boto3.client('autoscaling')

# Constants configured to match your s3.yml export: "dev-impressico-backups"
S3_BUCKET_NAME = "dev-impressico-backups"
DATA_TO_BACKUP = "/var/log/" 

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    # Extract details from the EventBridge ASG Lifecycle Event
    detail = event.get('detail', {})
    asg_name = detail.get('AutoScalingGroupName')
    instance_id = detail.get('EC2InstanceId')
    lifecycle_hook_name = detail.get('LifecycleHookName')
    lifecycle_action_token = detail.get('LifecycleActionToken')
    
    if not lifecycle_hook_name:
        return {'statusCode': 200, 'body': 'Skipping: Not a lifecycle hook.'}

    # 1. Fetch Slack Webhook URL from SSM Parameter Store (Provisioned via iam.yml)
    slack_webhook_url = None
    try:
        param_response = ssm_client.get_parameter(
            Name="/dev/slack/webhook",
            WithDecryption=True
        )
        slack_webhook_url = param_response['Parameter']['Value']
    except Exception as e:
        print(f"Failed to fetch Slack Webhook URL from SSM: {str(e)}")

    # 2. Trigger SSM Run Command on dying EC2 to ship logs to S3 before terminating
    shell_commands = [
        "echo 'Starting backup to S3...'",
        f"TAR_FILE='/tmp/backup-{instance_id}-{int(time.time())}.tar.gz'",
        f"tar -czf $TAR_FILE {DATA_TO_BACKUP} 2>/dev/null || true",
        f"aws s3 cp $TAR_FILE s3://{S3_BUCKET_NAME}/ec2-backups/{instance_id}/",
        "echo 'Backup complete.'"
    ]
    
    ssm_success = False
    try:
        print(f"Sending SSM Run Command to instance {instance_id}")
        ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': shell_commands}
        )
        # Briefly pause so the instance has time to compress and upload before shutdown
        time.sleep(12)
        ssm_success = True
    except Exception as e:
        print(f"Failed to trigger SSM backup command: {str(e)}")

    # 3. Dispatch direct Slack Notification as required by PIP
    if slack_webhook_url:
        slack_message = {
            "text": f"⚠️ *EC2 Instance Terminating (Recovery Flow Triggered)*\n\n"
                    f"*Instance ID:* `{instance_id}`\n"
                    f"*AutoScaling Group:* `{asg_name}`\n"
                    f"*Backup S3 Bucket:* `s3://{S3_BUCKET_NAME}/ec2-backups/{instance_id}/`\n"
                    f"*Backup Status:* {'Success' if ssm_success else 'Failed/Skipped'}\n"
                    f"ASG is currently launching a replacement instance."
        }
        http = urllib3.PoolManager()
        try:
            http.request(
                'POST',
                slack_webhook_url,
                body=json.dumps(slack_message),
                headers={'Content-Type': 'application/json'}
            )
            print("Slack notification dispatched.")
        except Exception as e:
            print(f"Failed to dispatch Slack notification: {str(e)}")

    # 4. Complete Lifecycle Hook so ASG can proceed with termination
    try:
        print(f"Completing Lifecycle Hook for {instance_id}")
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='CONTINUE'
        )
    except Exception as e:
        print(f"Error completing lifecycle: {str(e)}")
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='ABANDON'
        )
        
    return {
        'statusCode': 200,
        'body': json.dumps('Workflow executed successfully')
    }