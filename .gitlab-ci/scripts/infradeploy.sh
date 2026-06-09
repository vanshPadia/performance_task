#!/bin/bash

set -e

case "$CFT_STACK" in
  vpc)            TEMPLATE_PATH="iac/aws/cloudformation/vpc.yml" ;;
  iam)            TEMPLATE_PATH="iac/aws/cloudformation/iam.yml" ;;
  s3)             TEMPLATE_PATH="iac/aws/cloudformation/s3.yml" ;;
  ecr)            TEMPLATE_PATH="iac/aws/cloudformation/ecr.yml" ;;
  securityGroups) TEMPLATE_PATH="iac/aws/cloudformation/securityGroups.yml" ;;
  grafanaEc2)     TEMPLATE_PATH="iac/aws/cloudformation/grafanaEc2.yml" ;;
  loadBalancer)   TEMPLATE_PATH="iac/aws/cloudformation/loadBalancer.yml" ;;
  autoScaling)    TEMPLATE_PATH="iac/aws/cloudformation/autoScaling.yml" ;;
  ssmDocument)    TEMPLATE_PATH="iac/aws/cloudformation/ssmDocument.yml" ;;
  *)
    echo "ERROR: Unknown CFT_STACK value: '$CFT_STACK'"
    echo "Valid values: vpc, iam, s3, ecr, securityGroups, grafanaEc2, loadBalancer, autoScaling, ssmDocument"
    exit 1
    ;;
esac

echo "Starting CloudFormation deployment for stack: $environment-$product-$CFT_STACK-stack"

aws cloudformation deploy \
    --region "ap-south-1" \
    --stack-name "$environment-$product-$CFT_STACK-stack" \
    --template-file "$TEMPLATE_PATH" \
    --parameter-overrides \
    environment="$environment" \
    product="$product" \
    service="$CFT_STACK" \
    gitlabUsername="$GITLAB_USER" \
    gitlabToken="$GITLAB_TOKEN" \
    grafanaAdminPassword="$GRAFANA_ADMIN_PASSWORD" \
    slackWebhookUrl="$SLACK_WEBHOOK_URL" \
    keyName="$keyName" \
    repoUrl="$repoUrl" \
    imageRetentionCount="$imageRetentionCount" \
    --capabilities CAPABILITY_IAM \
    --capabilities CAPABILITY_NAMED_IAM

echo "Deployment completed successfully!"
