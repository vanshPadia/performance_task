#!/bin/bash

set -e

echo "========================================"
echo "  SSM Deploy Triggered"
echo "  Application : ${APPLICATION_CHOICE}"
echo "  Image Tag   : ${IMAGE_TAG}"
echo "  ECR Repo    : ${ECR_REPOSITORY}"
echo "========================================"

# Send SSM command to EC2 instance
echo "Sending SSM command to instance: ${INSTANCE_ID}..."

COMMAND_ID=$(aws ssm send-command \
  --document-name "${DOCUMENT_NAME}" \
  --targets "[{\"Key\":\"instanceIds\",\"Values\":[\"${INSTANCE_ID}\"]}]" \
  --parameters "{
    \"application\":[\"${APPLICATION_CHOICE}\"],
    \"ecrRegistry\":[\"${ECR_REGISTRY}\"],
    \"ecrRepository\":[\"${ECR_REPOSITORY}\"],
    \"imageTag\":[\"${IMAGE_TAG}\"],
    \"awsRegion\":[\"${AWS_DEFAULT_REGION}\"]
  }" \
  --region "${AWS_DEFAULT_REGION}" \
  --query "Command.CommandId" \
  --output text)

echo "SSM Command sent. Command ID: ${COMMAND_ID}"

# Wait for command to finish
echo "Waiting for command to complete..."
aws ssm wait command-executed \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$AWS_DEFAULT_REGION"

# Get final status
STATUS=$(aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$AWS_DEFAULT_REGION" \
  --query "Status" \
  --output text)

echo "--------------------------------------------------------"
echo "Command Status: ${STATUS}"
echo "--------------------------------------------------------"

# Print full output
aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$AWS_DEFAULT_REGION"

# Fail the GitLab job if SSM command failed
if [ "$STATUS" != "Success" ]; then
  echo "ERROR: SSM command ended with status: ${STATUS}"
  exit 1
fi

echo "Deployment completed successfully."