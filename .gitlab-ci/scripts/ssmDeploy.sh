#!/bin/bash

set -e

# 1. Map GitLab UI choice ("both") to SSM parameter expected choice ("all")
TARGET_APP="${APPLICATION_CHOICE}"

if [ "${TARGET_APP}" = "both" ]; then
  TARGET_APP="both"
fi

# Fallback check if APPLICATION_CHOICE wasn't passed or is empty
if [ -z "${TARGET_APP}" ]; then
  echo "WARNING: APPLICATION_CHOICE is empty. Defaulting to backend."
  TARGET_APP="backend"
fi

echo "Deploying targeting application selection: ${TARGET_APP}"

# 2. Sending SSM command with dynamic parameters
echo "Sending SSM command..."
COMMAND_ID=$(aws ssm send-command \
  --document-name "${DOCUMENT_NAME}" \
  --targets "[{\"Key\":\"instanceIds\",\"Values\":[\"${INSTANCE_ID}\"]}]" \
  --parameters "{\"application\":[\"${TARGET_APP}\"],\"imagename\":[\"${IMAGE_NAME}\"],\"imagetag\":[\"${IMAGE_TAG}\"]}" \
  --region "${AWS_DEFAULT_REGION}" \
  --query "Command.CommandId" \
  --output text)

echo "Command sent successfully. Command ID: ${COMMAND_ID}"

# 3. Execution Waiter Loop
echo "Waiting for SSM command to execute..."

until aws ssm wait command-executed --command-id "$COMMAND_ID" --instance-id "$INSTANCE_ID" --region "$AWS_DEFAULT_REGION" 2>/dev/null; do
    echo "Waiter reached 100s window limit, checking status again..."
    
    # Check if the command actually failed completely so we don't loop forever
    STATUS=$(aws ssm get-command-invocation \
      --command-id "$COMMAND_ID" \
      --instance-id "$INSTANCE_ID" \
      --region "$AWS_DEFAULT_REGION" \
      --query "Status" --output text)
      
    if [ "$STATUS" = "Failed" ] || [ "$STATUS" = "Cancelled" ] || [ "$STATUS" = "TimedOut" ]; then
        echo "SSM Command ended with state: ${STATUS}. Exiting."
        break
    fi
done

# 4. Fetch and display final outputs
echo "--------------------------------------------------------"
echo "Fetching final command execution results..."
echo "--------------------------------------------------------"

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$AWS_DEFAULT_REGION"