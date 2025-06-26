
**Producer → Kafka Topic → Consumer → MongoDB → Transformer → Clean Data**

This project implements a scalable, real-time data processing pipeline using Kafka, MongoDB, Kubernetes (Minikube/OpenShift), and Python. It simulates a message-driven architecture where employee records flow through multiple processing stages—ingestion, transformation, and storage—across distributed pods.

# Problem Statement
Raw data—especially employee-related data—is generated in high volume and often in inconsistent formats. Processing this data in real-time while ensuring accuracy, auditability, and fault tolerance becomes a challenge, particularly in distributed microservice environments.

This project solves that problem by:

Queueing raw records through Kafka.
Persisting them in a raw MongoDB queue collection.
Transforming, enriching, and updating them using stateless transformer pods.
Allowing horizontal scaling of processing pods.
Maintaining detailed audit logs, retry tracking, and failure recovery.


**Producer Pod**              
Simulates real-time data generation. Pushes employee records into a Kafka topic.

**Consumer Pod**
Listens to the Kafka topic and stores raw messages in MongoDB with metadata.

**Transformer Pod(s)**
Polls MongoDB for unprocessed records. Applies transformation logic, enriches data, and updates the same document with status, latency, retries, etc. Multiple transformer pods can run concurrently. 

**Operator Pod**
Monitors MongoDB queue length or pod performance and scales transformer pods accordingly via Kubernetes APIs.

# Tech Stacks
Kafka – For decoupled message-based data ingestion and real-time streaming

MongoDB – For storing raw and processed employee records with flexible schema

Python – Core language for all service logic (Producer, Consumer, Transformer)

PyMongo – For interacting with MongoDB and performing atomic operations

Docker – Containerizes each service for isolated, portable deployments

Kubernetes / Minikube / OpenShift – For orchestration, scaling, and service management

Kafka-Python – Kafka client library used by producer and consumer pods





# mongoDB port expose to connect to compass

kubectl port-forward pod/<podName> 27017:27017

if needs auth : 
    mongodb://root:example@localhost:27017/?authSource=admin


# minikube commands 
    minikube status 
    minikube start
    minikube stop
    kubectl get pods
    kubectl get deployments
    kubectl delete deployments --all
