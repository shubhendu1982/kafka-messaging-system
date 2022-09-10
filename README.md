# Secure kafka-messaging-system

This project demonstrates some features of the Apache Kafka system. It is implemented using the kafka-python library for python. We need to ensure that kafka instance is accesed only via tls and also a topic can be restricted to a set of microservices(zero trust microservice).After some research we found strimji kafka operator is sutable for our need. This repositry will describe how to setup a full blown kafka cluster using the operator and sample python code to communicate with this cluster(consumer.py and producer.py).

## Outline:
In this story, will describe the installation of Kafka using strimzi operator. Below are some facts behind strimzi within our cluster

- Secure by Default- Built-in security which can support the deployment of zero trust microservice
TLS, SCRAM-SHA, and OAuth authentication
Automated Certificate Management
- Manages the Kafka Cluster - Deploys and manages all of the components of this complex application, including dependencies like Apache ZooKeeper® that are traditionally hard to administer.

- Monitoring - Built-in support for monitoring using Prometheus and provided Grafana dashboards

## Setup secure strimji kafka in k8s cluster

### Step 1: Add the helm repo and install the Strimzi operator in the Kafka namespace.

```
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm install my-strimzi-release strimzi/strimzi-kafka-operator --namespace kafka --version 0.29.0 --create-namespace --set watchNamespaces="{data-portal}"
```
N.B. watchNamespaces="{data-portal} is needed so that operator can watch out for the application namespace where Kafka cluster will be installed.

### Step 2:  Provision of the Kafka cluster in the application namespace(data-portal) so that the application can access the Kafka instance

```
copy https://strimzi.io/examples/latest/kafka/kafka-persistent-single.yaml
replace listeners

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

### Step 3: Wait for cluster setup completion

kubectl wait kafka/my-cluster --for=condition=Ready --timeout=300s -n data-portal
Once completed "kafka.kafka.strimzi.io/my-cluster condition met" message will be displayed

### Step 4: Configuring internal clients to trust the cluster CA:
https://strimzi.io/docs/operators/in-development/configuring.html#configuring-internal-clients-to-trust-cluster-ca-str

### Step 5: Configuring external clients to trust the cluster CA:
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
## Sample producer and consumer

Use the image pushed in the docker hub as part of CD use the proper tag

### Step 1: Create a topic (my-topic) in kafka cluster (my-cluster)

```
cat << EOF | kubectl create -n my-kafka-project -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: my-topic
  labels:
    strimzi.io/cluster: "my-cluster"
spec:
  partitions: 3
  replicas: 1
EOF

```

### Step 2: Create user which is having acl for the  (my-topic)

```
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: my-user
  labels:
    strimzi.io/cluster: my-cluster
spec:
  authorization:
    type: simple
    acls:
      # access to my-topic
      - resource:
          type: topic
          name: my-topic
          patternType: literal
        operation: Write
        host: "*"
      - resource:
          type: topic
          name: my-topic
          patternType: literal
        operation: Create
        host: "*"
      - resource:
          type: topic
          name: my-topic
          patternType: literal
        operation: Describe
        host: "*"
      - resource:
          type: topic
          name: my-topic
          patternType: literal
        operation: Read
        host: "*"
      # access to status.storage.topic
      - resource:
          type: topic
          name: connect-cluster-status
          patternType: literal
        operation: Write
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-status
          patternType: literal
        operation: Create
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-status
          patternType: literal
        operation: Describe
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-status
          patternType: literal
        operation: Read
        host: "*"
      # access to config.storage.topic
      - resource:
          type: topic
          name: connect-cluster-configs
          patternType: literal
        operation: Write
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-configs
          patternType: literal
        operation: Create
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-configs
          patternType: literal
        operation: Describe
        host: "*"
      - resource:
          type: topic
          name: connect-cluster-configs
          patternType: literal
        operation: Read
        host: "*"
      # consumer group
      - resource:
          type: group
          name: connect-cluster
          patternType: literal
        operation: Read
        host: "*"
```

### Step 3: Run producer in k8s

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
       image: shubhendu1982/kafka-messaging-system:<tag>-main
       volumeMounts:
       - name: secret-volume
         mountPath: /data/crt
       - name: my-user-secret-volume
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

### Step 4: Run consumer in k8s

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
       image: shubhendu1982/kafka-messaging-system:<tag>-main
       volumeMounts:
       - name: secret-volume
         mountPath: /data/crt
       - name: my-user-secret-volume
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
## CI

This repo also contains code for running static code analysis and also some unit and integration tests using github actions.

### Unit and integration tests

Unit and intgration test run has been integrated and runs for each check in git hub. It ensures quality of the code.

### Static code analysis

Static code analysis has been added as part of the CI and during commit using git client. A set of best practices (as part of the precommit hook) and code quality pugin like mypy, pylint, flake8, bandit etc. has been integrated to ensure quality of the delivered code.


## CD

Each merge to main branch executes CD pipeline which is also using github actions pipeline to push the docker image to docker hub. This image can be used for further testing and depoy to k8s cluster.

### Security scan of images

Security scanning using trivy of the image is performed as part of CD ensures.Trivy is a comprehensive and easy-to-use open source vulnerability scanner for container images,file systems, and Git repositories, as well as for configuration issues. Trivy detects vulnerabilities of OS packages (Alpine, RHEL, CentOS, etc.) and language-specific packages (Bundler, Composer, npm, yarn, etc.).

## To run precommit hook Run command bedore checkin
```
pre-commit run --all-files
```
