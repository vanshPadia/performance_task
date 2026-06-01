import json
import boto3
import time

# Initialize AWS Clients
ssm_client = boto3.client('ssm')
asg_client = boto3.client('autoscaling')
sns_client = boto3.client('sns')

# Configuration (Replace these with your actual environment variables or strings)
S3_BUCKET_NAME = "your-backup-logs-bucket-name"
SNS_TOPIC_ARN = "arn:aws:sns:region:account-id:your-topic-name"
DATA_TO_BACKUP = "/var/log/"  # Change this to the specific directory or files you need

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    # Extract details from the EventBridge ASG Lifecycle Event
    detail = event['detail']
    asg_name = detail['AutoScalingGroupName']
    instance_id = detail['EC2InstanceId']
    lifecycle_hook_name = detail['LifecycleHookName']
    lifecycle_action_token = detail['LifecycleActionToken']
    
    # 1. Send Notification via SNS
    try:
        message = f"Alert: The EC2 instance {instance_id} in ASG '{asg_name}' is terminating. Initiating S3 data backup."
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"EC2 Termination Alert: {instance_id}",
            Message=message
        )
        print(f"Notification sent for {instance_id}")
    except Exception as e:
        print(f"Failed to send SNS notification: {str(e)}")

    # 2. Trigger SSM Run Command to back up data from EC2 to S3
    # This command tallows us to interactively grab data right before the instance dies
    shell_commands = [
        f"echo 'Starting backup to S3...'",
        f"TAR_FILE='/tmp/backup-{instance_id}-{int(time.time())}.tar.gz'",
        f"tar -czf $TAR_FILE {DATA_TO_BACKUP}",
        f"aws s3 cp $TAR_FILE s3://{S3_BUCKET_NAME}/ec2-backups/{instance_id}/",
        f"echo 'Backup complete.'"
    ]
    
    try:
        print(f"Sending SSM Run Command to instance {instance_id}")
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': shell_commands},
            CloudWatchOutputConfig={
                'CloudWatchLogGroupName': '/aws/lambda/asg-termination-backup',
                'CloudWatchOutputEnabled': True
            }
        )
        command_id = response['Command']['CommandId']
        
        # Wait briefly for the command to execute (Polling loop)
        # For production, a Step Function or EventBridge pattern is more robust, 
        # but a brief loop works well for quick log collections.
        time.sleep(15) 
        
        # 3. Complete the Lifecycle Hook so ASG can finally terminate the instance
        print(f"Completing Lifecycle Hook for {instance_id}")
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='CONTINUE' # Tells ASG to proceed with termination
        )
        
    except Exception as e:
        print(f"Error during backup/lifecycle completion: {str(e)}")
        # In case of failure, abandon the hook so the instance doesn't hang indefinitely
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='ABANDON'
        )
        
    return {
        'statusCode': 200,
        'body': json.dumps('Process executed.')
    }