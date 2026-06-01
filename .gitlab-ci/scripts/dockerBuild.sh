#!/bin/bash

set -e

echo "Logging into Amazon ECR..."
aws ecr get-login-password --region "$AWS_DEFAULT_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "Building Docker image: $IMAGE_NAME:$IMAGE_TAG..."
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

echo "Pushing image to ECR..."
docker push "$IMAGE_NAME:$IMAGE_TAG"

echo "Cleaning up local Docker resources..."
docker system prune -a -f

echo "Successfully built and pushed $IMAGE_TAG"
