#!/bin/bash

echo "Deploying Kafka Transform Pipeline to Kubernetes..."

# Step 1: Deploy infrastructure services first
echo "Step 1: Deploying MongoDB..."
kubectl apply -f mongodb-deployment.yaml
echo "MongoDB deployment created"

echo "Step 2: Deploying Kafka..."
kubectl apply -f kafka-deployment.yaml
echo "Kafka deployment created"

# Step 3: Build Docker images for minikube
echo "Step 3: Building Docker images for minikube..."
echo "Setting Docker environment to use minikube's Docker daemon..."
eval $(minikube docker-env)

cd ..
echo "Building producer image..."
docker build -t kafkatranform-producer:latest ./producer
echo "Building consumer image..."
docker build -t kafkatranform-consumer:latest ./consumer
echo "Building transformer image..."
docker build -t kafkatranform-transformer:latest ./transformer
echo "All Docker images built for minikube"

# Step 4: Deploy application services
cd kubernetes
echo "Step 4: Deploying Producer..."
kubectl apply -f producer-deployment.yaml
echo "Producer deployment created"

echo "Step 5: Deploying Consumer..."
kubectl apply -f consumer-deployment.yaml
echo "Consumer deployment created"

echo "Step 6: Deploying Transformer..."
kubectl apply -f transformer-deployment.yaml
echo "Transformer deployment created"

echo "Step 7: Deploying Kafdrop..."
kubectl apply -f kafdrop-deployment.yaml
echo "Kafdrop deployment created"

echo "Deployment completed!"
echo ""
echo "Check the status with:"
echo "kubectl get pods"
echo "kubectl get services"
echo ""
echo "View logs with:"
echo "kubectl logs -f deployment/producer"
echo "kubectl logs -f deployment/consumer"
echo "kubectl logs -f deployment/transformer"