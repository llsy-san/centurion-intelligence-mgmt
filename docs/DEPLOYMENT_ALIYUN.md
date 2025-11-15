# 阿里云容器化部署文档

## 概述

本文档详细介绍如何在阿里云上部署订单支付系统，包括基础设施准备、容器化部署、监控配置等完整流程。

## 目录

1. [阿里云服务准备](#1-阿里云服务准备)
2. [基础设施配置](#2-基础设施配置)
3. [容器镜像构建](#3-容器镜像构建)
4. [Kubernetes部署](#4-kubernetes部署)
5. [数据库配置](#5-数据库配置)
6. [负载均衡配置](#6-负载均衡配置)
7. [监控和日志](#7-监控和日志)
8. [CI/CD流水线](#8-cicd流水线)
9. [安全配置](#9-安全配置)
10. [运维管理](#10-运维管理)

## 1. 阿里云服务准备

### 1.1 所需阿里云服务

| 服务名称 | 用途 | 规格建议 |
|---------|------|----------|
| 容器服务 ACK | Kubernetes集群 | 标准托管版，3个Worker节点 |
| 容器镜像服务 ACR | 镜像仓库 | 企业版 |
| 云数据库 RDS | PostgreSQL数据库 | 高可用版，4核8GB |
| 云数据库 Redis | 缓存服务 | 主从版，2GB |
| 负载均衡 SLB | 流量分发 | 应用型负载均衡 |
| 日志服务 SLS | 日志收集 | 标准版 |
| 云监控 CMS | 监控告警 | 基础版 |
| 专有网络 VPC | 网络隔离 | 自定义VPC |
| 弹性公网IP | 外网访问 | 按流量计费 |

### 1.2 账号和权限配置

```bash
# 安装阿里云CLI
curl -L https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz | tar -xzf -
sudo mv aliyun /usr/local/bin/

# 配置访问凭证
aliyun configure set \
  --profile default \
  --mode AK \
  --region cn-hangzhou \
  --access-key-id YOUR_ACCESS_KEY_ID \
  --access-key-secret YOUR_ACCESS_KEY_SECRET

# 验证配置
aliyun ecs DescribeRegions
```

### 1.3 创建专有网络VPC

```bash
# 创建VPC
aliyun ecs CreateVpc \
  --RegionId cn-hangzhou \
  --VpcName order-payment-vpc \
  --CidrBlock 172.16.0.0/16 \
  --Description "订单支付系统VPC"

# 创建交换机
aliyun ecs CreateVSwitch \
  --RegionId cn-hangzhou \
  --ZoneId cn-hangzhou-h \
  --VpcId vpc-xxxxxxxxx \
  --VSwitchName order-payment-vswitch \
  --CidrBlock 172.16.1.0/24

# 创建安全组
aliyun ecs CreateSecurityGroup \
  --RegionId cn-hangzhou \
  --VpcId vpc-xxxxxxxxx \
  --SecurityGroupName order-payment-sg \
  --Description "订单支付系统安全组"
```

## 2. 基础设施配置

### 2.1 创建ACK集群

```yaml
# ack-cluster.yaml
apiVersion: cs.alibabacloud.com/v1
kind: Cluster
metadata:
  name: order-payment-cluster
spec:
  clusterType: ManagedKubernetes
  kubernetesVersion: "1.28.3-aliyun.1"
  region: cn-hangzhou
  zoneid: cn-hangzhou-h
  vpcid: vpc-xxxxxxxxx
  vswitchid: vsw-xxxxxxxxx
  containerCidr: 172.20.0.0/16
  serviceCidr: 172.21.0.0/20
  workerInstanceTypes:
    - ecs.c6.xlarge
  workerSystemDiskCategory: cloud_essd
  workerSystemDiskSize: 120
  workerDataDiskCategory: cloud_essd
  workerDataDiskSize: 200
  numOfNodes: 3
  sshFlags: true
  tags:
    - key: Environment
      value: production
    - key: Project
      value: order-payment-system
```

### 2.2 配置kubectl

```bash
# 获取集群凭证
aliyun cs GET /clusters/{cluster-id}/user_config > ~/.kube/config

# 验证连接
kubectl get nodes
kubectl get namespaces

# 创建命名空间
kubectl create namespace order-payment-system
kubectl create namespace monitoring
kubectl create namespace logging
```

### 2.3 创建存储类

```yaml
# storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: alicloud-disk-ssd
provisioner: diskplugin.csi.alibabacloud.com
parameters:
  type: cloud_essd
  regionId: cn-hangzhou
  zoneId: cn-hangzhou-h
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

## 3. 容器镜像构建

### 3.1 创建容器镜像服务仓库

```bash
# 创建命名空间
aliyun cr CreateNamespace \
  --NamespaceName order-payment-system

# 创建镜像仓库
aliyun cr CreateRepository \
  --RepoNamespace order-payment-system \
  --RepoName order-service \
  --RepoType PUBLIC \
  --Summary "订单服务镜像"

aliyun cr CreateRepository \
  --RepoNamespace order-payment-system \
  --RepoName payment-service \
  --RepoType PUBLIC \
  --Summary "支付服务镜像"

aliyun cr CreateRepository \
  --RepoNamespace order-payment-system \
  --RepoName shipping-service \
  --RepoType PUBLIC \
  --Summary "发货服务镜像"

aliyun cr CreateRepository \
  --RepoNamespace order-payment-system \
  --RepoName api-gateway \
  --RepoType PUBLIC \
  --Summary "API网关镜像"
```

### 3.2 Dockerfile优化

```dockerfile
# order-service/docker/Dockerfile.prod
FROM python:3.11-slim as builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 复制依赖
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY app/ ./app/
COPY shared/ ./shared/

# 设置权限
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 3.3 构建和推送镜像

```bash
# 登录ACR
docker login --username=your-username registry.cn-hangzhou.aliyuncs.com

# 构建镜像脚本
#!/bin/bash
# build-and-push.sh

REGISTRY="registry.cn-hangzhou.aliyuncs.com/order-payment-system"
VERSION=${1:-latest}

services=("order-service" "payment-service" "shipping-service" "api-gateway")

for service in "${services[@]}"; do
  echo "Building $service..."
  
  cd $service
  docker build -t $REGISTRY/$service:$VERSION -f docker/Dockerfile.prod .
  docker push $REGISTRY/$service:$VERSION
  
  # 同时推送latest标签
  if [ "$VERSION" != "latest" ]; then
    docker tag $REGISTRY/$service:$VERSION $REGISTRY/$service:latest
    docker push $REGISTRY/$service:latest
  fi
  
  cd ..
  echo "$service build and push completed"
done

echo "All services built and pushed successfully!"
```

## 4. Kubernetes部署

### 4.1 配置ConfigMap和Secret

```yaml
# config/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: order-payment-config
  namespace: order-payment-system
data:
  # 数据库配置
  DB_HOST: "rm-xxxxxxxxx.mysql.rds.aliyuncs.com"
  DB_PORT: "5432"
  DB_DATABASE: "order_system"
  
  # Redis配置
  REDIS_HOST: "r-xxxxxxxxx.redis.rds.aliyuncs.com"
  REDIS_PORT: "6379"
  
  # 服务发现配置
  ORDER_SERVICE_URL: "http://order-service:8001"
  PAYMENT_SERVICE_URL: "http://payment-service:8002"
  SHIPPING_SERVICE_URL: "http://shipping-service:8003"
  
  # 应用配置
  DEBUG: "false"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: order-payment-secrets
  namespace: order-payment-system
type: Opaque
data:
  # Base64编码的敏感信息
  DB_USERNAME: cG9zdGdyZXM=  # postgres
  DB_PASSWORD: eW91ci1wYXNzd29yZA==  # your-password
  REDIS_PASSWORD: cmVkaXMtcGFzc3dvcmQ=  # redis-password
  JWT_SECRET_KEY: eW91ci1qd3Qtc2VjcmV0LWtleQ==  # your-jwt-secret-key
  ALIPAY_PRIVATE_KEY: eW91ci1hbGlwYXkta2V5  # your-alipay-key
```

### 4.2 订单服务部署

```yaml
# deployments/order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: order-payment-system
  labels:
    app: order-service
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        version: v1
    spec:
      containers:
      - name: order-service
        image: registry.cn-hangzhou.aliyuncs.com/order-payment-system/order-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: DB_HOST
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_USERNAME
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_PASSWORD
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: order-payment-system
  labels:
    app: order-service
spec:
  selector:
    app: order-service
  ports:
  - port: 8001
    targetPort: 8001
    name: http
  type: ClusterIP
```

### 4.3 发货服务部署（支持门票二维码）

```yaml
# deployments/shipping-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shipping-service
  namespace: order-payment-system
  labels:
    app: shipping-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shipping-service
  template:
    metadata:
      labels:
        app: shipping-service
        version: v1
    spec:
      containers:
      - name: shipping-service
        image: registry.cn-hangzhou.aliyuncs.com/order-payment-system/shipping-service:latest
        ports:
        - containerPort: 8003
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: DB_HOST
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_USERNAME
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_PASSWORD
        - name: QR_CODE_BASE_URL
          value: "https://qr.yourdomain.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: qr-codes
          mountPath: /app/qr-codes
      volumes:
      - name: qr-codes
        persistentVolumeClaim:
          claimName: qr-codes-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: shipping-service
  namespace: order-payment-system
  labels:
    app: shipping-service
spec:
  selector:
    app: shipping-service
  ports:
  - port: 8003
    targetPort: 8003
    name: http
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qr-codes-pvc
  namespace: order-payment-system
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: alicloud-nas
  resources:
    requests:
      storage: 10Gi
```

### 4.4 API网关部署

```yaml
# deployments/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: order-payment-system
  labels:
    app: api-gateway
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        version: v1
    spec:
      containers:
      - name: api-gateway
        image: registry.cn-hangzhou.aliyuncs.com/order-payment-system/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: ORDER_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: ORDER_SERVICE_URL
        - name: PAYMENT_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: PAYMENT_SERVICE_URL
        - name: SHIPPING_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: SHIPPING_SERVICE_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: JWT_SECRET_KEY
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: order-payment-system
  labels:
    app: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
```

## 5. 数据库配置

### 5.1 创建RDS PostgreSQL实例

```bash
# 创建RDS实例
aliyun rds CreateDBInstance \
  --RegionId cn-hangzhou \
  --ZoneId cn-hangzhou-h \
  --Engine PostgreSQL \
  --EngineVersion 15.0 \
  --DBInstanceClass rds.pg.s3.large \
  --DBInstanceStorage 100 \
  --DBInstanceStorageType cloud_essd \
  --PayType Postpaid \
  --SecurityIPList "172.16.0.0/16" \
  --DBInstanceDescription "订单支付系统数据库"

# 创建数据库
aliyun rds CreateDatabase \
  --DBInstanceId rm-xxxxxxxxx \
  --DBName order_system \
  --CharacterSetName UTF8

# 创建数据库账号
aliyun rds CreateAccount \
  --DBInstanceId rm-xxxxxxxxx \
  --AccountName order_user \
  --AccountPassword "YourStrongPassword123!" \
  --AccountType Normal \
  --AccountDescription "订单系统数据库用户"

# 授权数据库访问
aliyun rds GrantAccountPrivilege \
  --DBInstanceId rm-xxxxxxxxx \
  --AccountName order_user \
  --DBName order_system \
  --AccountPrivilege ReadWrite
```

### 5.2 创建Redis实例

```bash
# 创建Redis实例
aliyun r-kvstore CreateInstance \
  --RegionId cn-hangzhou \
  --ZoneId cn-hangzhou-h \
  --InstanceName order-payment-redis \
  --InstanceClass redis.master.small.default \
  --ChargeType PostPaid \
  --Password "YourRedisPassword123!" \
  --VpcId vpc-xxxxxxxxx \
  --VSwitchId vsw-xxxxxxxxx
```

### 5.3 数据库初始化Job

```yaml
# jobs/db-init.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-init
  namespace: order-payment-system
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: db-init
        image: registry.cn-hangzhou.aliyuncs.com/order-payment-system/order-service:latest
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: order-payment-config
              key: DB_HOST
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_USERNAME
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: order-payment-secrets
              key: DB_PASSWORD
```

## 6. 负载均衡配置

### 6.1 创建应用负载均衡

```yaml
# ingress/alb-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: order-payment-ingress
  namespace: order-payment-system
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/load-balancer-name: order-payment-alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-redirect: "true"
    alb.ingress.kubernetes.io/certificate-arn: "arn:acs:cas:cn-hangzhou:your-account:certificate/your-cert-id"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
spec:
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
  - host: admin.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 8080
```

### 6.2 配置SSL证书

```bash
# 上传SSL证书到阿里云证书服务
aliyun cas UploadUserCertificate \
  --CertName yourdomain.com \
  --Cert "$(cat yourdomain.com.crt)" \
  --Key "$(cat yourdomain.com.key)"
```

## 7. 监控和日志

### 7.1 部署Prometheus监控

```yaml
# monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
    - job_name: 'order-payment-services'
      static_configs:
      - targets: ['order-service:8001', 'payment-service:8002', 'shipping-service:8003']

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

### 7.2 配置日志服务SLS

```yaml
# logging/fluent-bit.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/containers/*order-payment*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On

    [OUTPUT]
        Name  aliyun_sls
        Match *
        Project your-sls-project
        Logstore order-payment-logs
        Endpoint cn-hangzhou.log.aliyuncs.com
        Access_Key_Id ${ALIYUN_ACCESS_KEY_ID}
        Access_Key_Secret ${ALIYUN_ACCESS_KEY_SECRET}

---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      name: fluent-bit
  template:
    metadata:
      labels:
        name: fluent-bit
    spec:
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:latest
        env:
        - name: ALIYUN_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aliyun-credentials
              key: access-key-id
        - name: ALIYUN_ACCESS_KEY_SECRET
          valueFrom:
            secretKeyRef:
              name: aliyun-credentials
              key: access-key-secret
        volumeMounts:
        - name: config
          mountPath: /fluent-bit/etc
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: fluent-bit-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

## 8. CI/CD流水线

### 8.1 阿里云云效配置

```yaml
# .acs/pipeline.yaml
version: '1.0'
name: order-payment-system-pipeline
stages:
  - name: 代码检查
    jobs:
      - name: 代码质量检查
        steps:
          - name: 代码检出
            uses: git-checkout@v1
          - name: Python环境
            uses: python-setup@v1
            with:
              python-version: '3.11'
          - name: 安装依赖
            run: pip install -r requirements.txt
          - name: 代码检查
            run: |
              flake8 .
              mypy .
              pytest tests/ --cov=app

  - name: 构建镜像
    jobs:
      - name: Docker构建
        steps:
          - name: 代码检出
            uses: git-checkout@v1
          - name: Docker构建推送
            uses: docker-build@v1
            with:
              dockerfile: ./order-service/docker/Dockerfile.prod
              context: ./order-service
              registry: registry.cn-hangzhou.aliyuncs.com
              repository: order-payment-system/order-service
              tag: ${PIPELINE_ID}

  - name: 部署测试环境
    jobs:
      - name: 部署到测试环境
        steps:
          - name: 更新Kubernetes部署
            uses: kubectl-deploy@v1
            with:
              kubeconfig: ${KUBE_CONFIG}
              namespace: order-payment-test
              manifests: |
                deployments/order-service.yaml
                deployments/payment-service.yaml
                deployments/shipping-service.yaml

  - name: 自动化测试
    jobs:
      - name: 集成测试
        steps:
          - name: 运行集成测试
            run: |
              pytest tests/integration/ -v
              pytest tests/e2e/ -v

  - name: 部署生产环境
    condition: ${BRANCH} == 'main'
    jobs:
      - name: 部署到生产环境
        approval: true
        steps:
          - name: 更新生产环境
            uses: kubectl-deploy@v1
            with:
              kubeconfig: ${PROD_KUBE_CONFIG}
              namespace: order-payment-system
              manifests: |
                deployments/
```

### 8.2 自动化部署脚本

```bash
#!/bin/bash
# deploy.sh

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="order-payment-${ENVIRONMENT}"

echo "Deploying to ${ENVIRONMENT} environment..."

# 更新镜像版本
kubectl set image deployment/order-service \
  order-service=registry.cn-hangzhou.aliyuncs.com/order-payment-system/order-service:${VERSION} \
  -n ${NAMESPACE}

kubectl set image deployment/payment-service \
  payment-service=registry.cn-hangzhou.aliyuncs.com/order-payment-system/payment-service:${VERSION} \
  -n ${NAMESPACE}

kubectl set image deployment/shipping-service \
  shipping-service=registry.cn-hangzhou.aliyuncs.com/order-payment-system/shipping-service:${VERSION} \
  -n ${NAMESPACE}

kubectl set image deployment/api-gateway \
  api-gateway=registry.cn-hangzhou.aliyuncs.com/order-payment-system/api-gateway:${VERSION} \
  -n ${NAMESPACE}

# 等待部署完成
kubectl rollout status deployment/order-service -n ${NAMESPACE}
kubectl rollout status deployment/payment-service -n ${NAMESPACE}
kubectl rollout status deployment/shipping-service -n ${NAMESPACE}
kubectl rollout status deployment/api-gateway -n ${NAMESPACE}

echo "Deployment completed successfully!"

# 运行健康检查
kubectl get pods -n ${NAMESPACE}
kubectl get services -n ${NAMESPACE}
```

## 9. 安全配置

### 9.1 网络策略

```yaml
# security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: order-payment-network-policy
  namespace: order-payment-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8001
    - protocol: TCP
      port: 8002
    - protocol: TCP
      port: 8003
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 443   # HTTPS
    - protocol: TCP
      port: 53    # DNS
    - protocol: UDP
      port: 53    # DNS
```

### 9.2 Pod安全策略

```yaml
# security/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: order-payment-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 9.3 RBAC配置

```yaml
# security/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-payment-sa
  namespace: order-payment-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: order-payment-role
  namespace: order-payment-system
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: order-payment-rolebinding
  namespace: order-payment-system
subjects:
- kind: ServiceAccount
  name: order-payment-sa
  namespace: order-payment-system
roleRef:
  kind: Role
  name: order-payment-role
  apiGroup: rbac.authorization.k8s.io
```

## 10. 运维管理

### 10.1 自动扩缩容配置

```yaml
# autoscaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
  namespace: order-payment-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shipping-service-hpa
  namespace: order-payment-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shipping-service
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 10.2 备份策略

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/${DATE}"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 备份数据库
pg_dump -h rm-xxxxxxxxx.mysql.rds.aliyuncs.com \
  -U order_user \
  -d order_system \
  > ${BACKUP_DIR}/database_backup.sql

# 备份Redis
redis-cli -h r-xxxxxxxxx.redis.rds.aliyuncs.com \
  --rdb ${BACKUP_DIR}/redis_backup.rdb

# 备份Kubernetes配置
kubectl get all -n order-payment-system -o yaml > ${BACKUP_DIR}/k8s_resources.yaml

# 上传到OSS
ossutil cp -r ${BACKUP_DIR} oss://your-backup-bucket/order-payment-system/

echo "Backup completed: ${BACKUP_DIR}"
```

### 10.3 监控告警配置

```yaml
# monitoring/alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: order-payment-alerts
  namespace: monitoring
spec:
  groups:
  - name: order-payment-system
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "Error rate is above 10% for 5 minutes"
    
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage"
        description: "Memory usage is above 90% for 10 minutes"
    
    - alert: DatabaseConnectionFailure
      expr: up{job="postgres-exporter"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Database connection failure"
        description: "Cannot connect to PostgreSQL database"
```

### 10.4 故障恢复流程

```bash
#!/bin/bash
# disaster-recovery.sh

BACKUP_DATE=${1}
NAMESPACE="order-payment-system"

if [ -z "$BACKUP_DATE" ]; then
  echo "Usage: $0 <backup_date>"
  echo "Example: $0 20241030_153000"
  exit 1
fi

echo "Starting disaster recovery for backup: $BACKUP_DATE"

# 下载备份文件
ossutil cp -r oss://your-backup-bucket/order-payment-system/${BACKUP_DATE} ./restore/

# 恢复数据库
psql -h rm-xxxxxxxxx.mysql.rds.aliyuncs.com \
  -U order_user \
  -d order_system \
  < ./restore/${BACKUP_DATE}/database_backup.sql

# 恢复Redis
redis-cli -h r-xxxxxxxxx.redis.rds.aliyuncs.com \
  --rdb ./restore/${BACKUP_DATE}/redis_backup.rdb

# 恢复Kubernetes资源
kubectl apply -f ./restore/${BACKUP_DATE}/k8s_resources.yaml

# 验证恢复
kubectl get pods -n ${NAMESPACE}
kubectl get services -n ${NAMESPACE}

echo "Disaster recovery completed"
```

## 总结

本文档提供了在阿里云上部署订单支付系统的完整指南，包括：

1. **基础设施准备**: VPC、ACK集群、RDS、Redis等
2. **容器化部署**: Docker镜像构建、Kubernetes部署配置
3. **服务治理**: 负载均衡、服务发现、配置管理
4. **监控运维**: 日志收集、性能监控、告警配置
5. **安全加固**: 网络策略、RBAC、安全扫描
6. **自动化**: CI/CD流水线、自动扩缩容、备份恢复

关键特性：
- 支持门票二维码生成和用户资产管理
- 高可用架构设计
- 自动扩缩容能力
- 完整的监控告警体系
- 安全的网络隔离
- 自动化部署流程

建议在实际部署时：
1. 根据业务规模调整资源配置
2. 完善监控告警规则
3. 定期进行备份和恢复演练
4. 建立完整的运维文档
5. 制定应急响应预案