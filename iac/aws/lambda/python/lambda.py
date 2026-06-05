import boto3
import os
import time
import json
import urllib.request

ssm = boto3.client('ssm')
autoscaling = boto3.client('autoscaling')

S3_BUCKET    = "dev-impressico-backups"
DB_PASSWORD  = os.environ.get("DB_PASSWORD", "password")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")

def send_slack(message: str, color: str = "#36a64f"):
    if not SLACK_WEBHOOK:
        return
    payload = json.dumps({
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "AWS Lambda | ASG Lifecycle",
            "ts": int(time.time())
        }]
    }).encode()
    req = urllib.request.Request(
        SLACK_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=5)


def lambda_handler(event, context):
    print("EVENT RECEIVED:", event)

    detail      = event['detail']
    instance_id = detail['EC2InstanceId']
    hook_name   = detail['LifecycleHookName']
    asg_name    = detail['AutoScalingGroupName']
    token       = detail['LifecycleActionToken']

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    dump_file = f"/var/lib/docker/volumes/simple-fullstack-app_mysql_data/_data/backup_{timestamp}.sql"
    s3_dest   = f"s3://{S3_BUCKET}/backups/{instance_id}/backup_{timestamp}.sql"
    ssm_status = "NOT_STARTED"

    # Notify: instance terminating, backup starting
    send_slack(
        f":warning: *Instance Terminating* — `{instance_id}`\n"
        f"ASG: `{asg_name}`\n"
        f"Backup starting → `{s3_dest}`",
        color="#ff9900"
    )

    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [
                    f"docker exec mysql_db sh -c \"mysqldump -u root -p'{DB_PASSWORD}' --all-databases > /var/lib/mysql/backup_{timestamp}.sql\"",
                    f"aws s3 cp {dump_file} {s3_dest}",
                    f"docker exec mysql_db rm -f /var/lib/mysql/backup_{timestamp}.sql",
                    "echo DONE"
                ]
            }
        )
        command_id = response['Command']['CommandId']
        print(f"[SSM] Command sent: {command_id}")

        while True:
            time.sleep(10)
            result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            ssm_status = result['Status']
            print(f"[SSM] Status: {ssm_status}")

            if ssm_status == 'Success':
                print(f"[DONE] Backup uploaded to {s3_dest}")
                print(result.get('StandardOutputContent', ''))
                # Notify: backup done
                send_slack(
                    f":white_check_mark: *Backup Complete* — `{instance_id}`\n"
                    f"Uploaded to: `{s3_dest}`\n"
                    f"Instance will now terminate.",
                    color="#36a64f"
                )
                break
            elif ssm_status in ['Failed', 'Cancelled', 'TimedOut']:
                err = result.get('StandardErrorContent', 'No error output')
                print(f"[FAIL] {err}")
                # Notify: backup failed
                send_slack(
                    f":x: *Backup FAILED* — `{instance_id}`\n"
                    f"Status: `{ssm_status}`\n"
                    f"Error: ```{err[:300]}```",
                    color="#e01e5a"
                )
                break

    except Exception as e:
        print(f"[ERROR] {e}")
        send_slack(
            f":x: *Lambda Error* — `{instance_id}`\n"
            f"Exception: `{str(e)}`",
            color="#e01e5a"
        )

    finally:
        autoscaling.complete_lifecycle_action(
            LifecycleHookName=hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionToken=token,
            LifecycleActionResult='CONTINUE'
        )
        print("[ASG] Lifecycle hook completed")

    return {"status": ssm_status}