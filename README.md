# kafka-messaging-system

This project demonstrates some features of the Apache Kafka system. It is implemented using the kafka-python library for python.

# Dependencies

## Setup strimji kafka in the cluster

### Outline:
In this story, will describe the installation of Kafka using strimzi operator. Below are some facts behind strimzi within our cluster

- Secure by Default- Built-in security which can support the deployment of zero trust microservice
TLS, SCRAM-SHA, and OAuth authentication
Automated Certificate Management
- Manages the Kafka Cluster - Deploys and manages all of the components of this complex application, including dependencies like Apache ZooKeeper® that are traditionally hard to administer.

- Monitoring - Built-in support for monitoring using Prometheus and provided Grafana dashboards

#### Steps:

##### Step 1: Add the helm repo and install the Strimzi operator in the Kafka namespace. 

```
helm repo add strimzi https://strimzi.io/charts/
helm repo update  
helm install my-strimzi-release strimzi/strimzi-kafka-operator --namespace kafka --version 0.29.0 --create-namespace --set watchNamespaces="{data-portal}"

```
N.B. watchNamespaces="{data-portal} is needed so that operator can watch out for the application namespace where Kafka cluster will be installed. 

##### Step 2:  Provision of the Kafka cluster in the application namespace(data-portal) so that the application can access the Kafka instance

copy https://strimzi.io/examples/latest/kafka/kafka-persistent-single.yaml 

replace listeners

```
- name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls
    authorization:
      type: simple
```
Modify the replica count as below

```
kafka:
     replicas: 3
     config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2 
zookeeper:
    replicas: 3
```
Apply the modified file in the cluster

```
kubectl apply -f <modifiedfile>.yaml -n data-portal
```

##### Step 3: Wait for cluster setup completion

kubectl wait kafka/my-cluster --for=condition=Ready --timeout=300s -n data-portal
Once completed "kafka.kafka.strimzi.io/my-cluster condition met" message will be displayed

##### Step 4: Configuring internal clients to trust the cluster CA:  
https://strimzi.io/docs/operators/in-development/configuring.html#configuring-internal-clients-to-trust-cluster-ca-str

##### Step 5: Configuring external clients to trust the cluster CA: 
https://strimzi.io/docs/operators/in-development/configuring.html#configuring-external-clients-to-trust-cluster-ca-str

```
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafka:
    version: 3.2.0
    replicas: 3
    listeners:
         - name: tls
           port: 9093
           type: internal
           tls: true
           authentication:
             type: tls
    authorization:
      type: simple
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      inter.broker.protocol.version: "3.2"
    storage:
      type: jbod
      volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: false
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      deleteClaim: false
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

## Requirments 

Requires Python 3 and pip3

### install packages 
```
pip install -r requirements.txt
```

To start a producer, open a new terminal


    cd src/
    python producer.py


To start a consumer, in another terminal


    cd src/
    python consumer.py
    
To run producer and consumer in k8s
```
apiVersion: v1
kind: Pod
metadata:
  labels:
    purpose: kafka-producer
  name: kafka-producer
spec:
     containers:
     - name: kafka-producer
       image: shubhendu1982/kafka-messaging-system:0.0.0-18-da3bc2c-main     
       volumeMounts:
       - name: secret-volume
         mountPath: /data/crt  
       - name: user-secret-volume
         mountPath: /data/usercrt      
       command: ["python"]
       args: ["/service/src/producer.py"]
       restartPolicy: OnFailure
     volumes:
     - name: secret-volume
       secret:
         secretName: my-cluster-cluster-ca-cert
     - name: user-secret-volume
       secret:
         secretName: my-user
```    
    
To run consumer in k8s

```
apiVersion: v1
kind: Pod
metadata:
  labels:
    purpose: kafka-consumer
  name: kafka-consumer
spec:
     containers:
     - name: kafka-producer
       image: shubhendu1982/kafka-messaging-system:0.0.0-18-da3bc2c-main     
       volumeMounts:
       - name: secret-volume
         mountPath: /data/crt  
       - name: user-secret-volume
         mountPath: /data/usercrt      
       command: ["python"]
       args: ["/service/src/consumer.py"]
       restartPolicy: OnFailure
     volumes:
     - name: secret-volume
       secret:
         secretName: my-cluster-cluster-ca-cert
     - name: user-secret-volume
       secret:
         secretName: my-user
```
