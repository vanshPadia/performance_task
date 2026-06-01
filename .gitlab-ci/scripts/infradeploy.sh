#!/bin/bash

set -e

echo "Starting CloudFormation deployment for stack: $environment-$product-$service-stack"

aws cloudformation deploy \
    --region "ca-central-1" \
    --stack-name "$environment-$product-$service-stack" \
    --template-file "$TEMPLATE_PATH" \
    --parameter-overrides \
    environment="$environment" \
    product="$product" \
    service="$service" \
    keyName="$keyName" \
    imageRetentionCount="$imageRetentionCount" \
    --capabilities CAPABILITY_IAM

echo "Deployment completed successfully!"
