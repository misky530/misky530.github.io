# Kubernetes实战练习任务清单

## 练习说明

- 每个任务都提供了完整的命令和YAML文件
- 建议按顺序完成,每个任务都基于前面的知识
- 完成后记得清理资源再进行下一个任务
- 遇到问题时使用 `kubectl describe` 和 `kubectl logs` 排查

---

## 第一部分: Kubernetes基础 (30分钟)

### 任务1.1: 理解Pod - 最小部署单元

**目标**: 创建单个Pod,理解Pod的生命周期

```bash
# 创建一个nginx Pod
kubectl run nginx-pod --image=nginx:alpine

# 查看Pod状态
kubectl get pods
kubectl get pods -o wide  # 查看更多信息(IP、节点等)

# 查看Pod详细信息
kubectl describe pod nginx-pod

# 查看Pod日志
kubectl logs nginx-pod

# 进入Pod执行命令
kubectl exec -it nginx-pod -- sh
# 在容器内执行: curl localhost
# 退出: exit

# 端口转发测试访问
kubectl port-forward pod/nginx-pod 8080:80 &
curl http://localhost:8080
killall kubectl  # 停止端口转发

# 删除Pod
kubectl delete pod nginx-pod
```

**验证点**:
- Pod从Pending -> ContainerCreating -> Running的过程
- Pod被分配了集群内部IP
- Pod被调度到某个worker节点

---

### 任务1.2: 使用YAML管理Pod

**目标**: 学习使用声明式配置

创建文件 `pod-with-labels.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-labeled
  labels:
    app: web
    env: dev
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
```

```bash
# 应用配置
kubectl apply -f pod-with-labels.yaml

# 查看标签
kubectl get pods --show-labels

# 通过标签选择器查询
kubectl get pods -l app=web
kubectl get pods -l env=dev

# 查看资源使用情况
kubectl top pod nginx-labeled

# 清理
kubectl delete -f pod-with-labels.yaml
```

**验证点**:
- 理解labels和selectors的作用
- 理解资源requests和limits

---

### 任务1.3: Deployment - 管理Pod副本

**目标**: 使用Deployment管理多个Pod副本

创建文件 `nginx-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
```

```bash
# 部署应用
kubectl apply -f nginx-deployment.yaml

# 查看Deployment
kubectl get deployments
kubectl get rs  # ReplicaSet
kubectl get pods -o wide

# 扩缩容
kubectl scale deployment nginx-deployment --replicas=5
kubectl get pods  # 观察新Pod创建

kubectl scale deployment nginx-deployment --replicas=2
kubectl get pods  # 观察Pod终止

# 更新镜像(滚动更新)
kubectl set image deployment/nginx-deployment nginx=nginx:1.26-alpine
kubectl rollout status deployment/nginx-deployment

# 查看更新历史
kubectl rollout history deployment/nginx-deployment

# 回滚到上一个版本
kubectl rollout undo deployment/nginx-deployment

# 查看Deployment详情
kubectl describe deployment nginx-deployment

# 清理
kubectl delete -f nginx-deployment.yaml
```

**验证点**:
- Deployment自动创建ReplicaSet
- 扩缩容的自动化
- 滚动更新零停机
- 回滚能力

---

### 任务1.4: Service - 服务发现与负载均衡

**目标**: 理解Service的三种类型

创建文件 `nginx-with-service.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-clusterip
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

```bash
# 部署
kubectl apply -f nginx-with-service.yaml

# 查看服务
kubectl get svc

# 测试ClusterIP(仅集群内部访问)
CLUSTER_IP=$(kubectl get svc nginx-clusterip -o jsonpath='{.spec.clusterIP}')
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -O- http://$CLUSTER_IP

# 测试NodePort(外部访问)
curl http://192.168.56.11:30080
curl http://192.168.56.21:30080
curl http://192.168.56.22:30080

# 查看Service的Endpoints
kubectl get endpoints nginx-clusterip

# 测试负载均衡(多次请求会分配到不同Pod)
for i in {1..10}; do
  curl -s http://192.168.56.11:30080 | grep title
done

# 清理
kubectl delete -f nginx-with-service.yaml
```

**验证点**:
- ClusterIP用于集群内部通信
- NodePort在所有节点上开放端口
- Service自动负载均衡到多个Pod

---

## 第二部分: 配置与存储 (40分钟)

### 任务2.1: ConfigMap - 配置管理

**目标**: 使用ConfigMap管理应用配置

创建文件 `configmap-demo.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  app.properties: |
    app.name=MyApp
    app.version=1.0
    app.environment=development
  database.url: "postgresql://db.example.com:5432/mydb"
  log.level: "INFO"
---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-config
spec:
  containers:
  - name: app
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
    - |
      echo "=== Environment Variables ==="
      echo "DB_URL: $DB_URL"
      echo "LOG_LEVEL: $LOG_LEVEL"
      echo ""
      echo "=== Config File ==="
      cat /config/app.properties
      echo ""
      echo "Sleeping..."
      sleep 3600
    env:
    - name: DB_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.url
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: log.level
    volumeMounts:
    - name: config-volume
      mountPath: /config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: app.properties
```

```bash
# 部署
kubectl apply -f configmap-demo.yaml

# 查看ConfigMap
kubectl get configmap
kubectl describe configmap app-config

# 查看Pod日志(验证配置已注入)
kubectl logs app-with-config

# 进入Pod验证
kubectl exec -it app-with-config -- sh
# 在容器内执行:
# echo $DB_URL
# cat /config/app.properties
# exit

# 更新ConfigMap
kubectl create configmap app-config --from-literal=log.level=DEBUG --dry-run=client -o yaml | kubectl apply -f -

# 重启Pod使配置生效
kubectl delete pod app-with-config
kubectl apply -f configmap-demo.yaml
kubectl logs app-with-config

# 清理
kubectl delete -f configmap-demo.yaml
```

**验证点**:
- ConfigMap两种注入方式:环境变量和文件挂载
- 配置与代码分离
- 更新ConfigMap需要重启Pod

---

### 任务2.2: Secret - 敏感信息管理

**目标**: 使用Secret管理密码、证书等敏感数据

```bash
# 创建Secret(命令行方式)
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=P@ssw0rd123

# 查看Secret(数据被base64编码)
kubectl get secret db-secret -o yaml

# 解码查看
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 -d
```

创建文件 `secret-demo.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-key
type: Opaque
stringData:
  api-key: "sk-1234567890abcdef"
  api-endpoint: "https://api.example.com"
---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secret
spec:
  containers:
  - name: app
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
    - |
      echo "=== Secret as Environment Variables ==="
      echo "Username: $DB_USER"
      echo "Password: $DB_PASS (hidden)"
      echo ""
      echo "=== Secret as Files ==="
      echo "API Key: $(cat /secrets/api-key)"
      echo "API Endpoint: $(cat /secrets/api-endpoint)"
      sleep 3600
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
    volumeMounts:
    - name: secret-volume
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: api-key
```

```bash
# 部署
kubectl apply -f secret-demo.yaml

# 查看日志
kubectl logs app-with-secret

# 进入Pod验证
kubectl exec -it app-with-secret -- sh
# cat /secrets/api-key
# echo $DB_USER
# exit

# 清理
kubectl delete -f secret-demo.yaml
kubectl delete secret db-secret
```

**验证点**:
- Secret和ConfigMap用法类似,但用于敏感数据
- Secret数据被base64编码(不是加密!)
- 在生产环境应使用Vault等工具管理Secret

---

### 任务2.3: Volume - 数据持久化

**目标**: 理解临时卷和持久卷的区别

创建文件 `volume-demo.yaml`:
```yaml
# EmptyDir: Pod生命周期内的临时存储
apiVersion: v1
kind: Pod
metadata:
  name: shared-volume-pod
spec:
  containers:
  - name: writer
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
    - |
      while true; do
        echo "$(date): Writer container" >> /data/log.txt
        sleep 5
      done
    volumeMounts:
    - name: shared-data
      mountPath: /data
  - name: reader
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
    - |
      while true; do
        echo "=== Latest logs ==="
        tail -5 /data/log.txt 2>/dev/null || echo "No logs yet"
        sleep 10
      done
    volumeMounts:
    - name: shared-data
      mountPath: /data
  volumes:
  - name: shared-data
    emptyDir: {}
---
# HostPath: 挂载节点上的目录(不推荐生产使用)
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: host-data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: host-data
    hostPath:
      path: /tmp/k8s-data
      type: DirectoryOrCreate
```

```bash
# 部署
kubectl apply -f volume-demo.yaml

# 查看shared-volume-pod的日志
kubectl logs shared-volume-pod -c writer
kubectl logs shared-volume-pod -c reader

# 进入Pod验证数据共享
kubectl exec -it shared-volume-pod -c reader -- cat /data/log.txt

# 验证hostPath
# 先在节点上创建文件
POD_NODE=$(kubectl get pod hostpath-pod -o jsonpath='{.spec.nodeName}')
echo $POD_NODE
ssh vagrant@192.168.56.21 "echo '<h1>Hello from HostPath</h1>' | sudo tee /tmp/k8s-data/index.html"

# 访问nginx
kubectl port-forward pod/hostpath-pod 8080:80 &
curl http://localhost:8080
killall kubectl

# 删除Pod后数据丢失(emptyDir)
kubectl delete pod shared-volume-pod
kubectl apply -f volume-demo.yaml
kubectl logs shared-volume-pod -c reader  # 日志文件不存在了

# 清理
kubectl delete -f volume-demo.yaml
ssh vagrant@192.168.56.21 "sudo rm -rf /tmp/k8s-data"
```

**验证点**:
- emptyDir用于Pod内容器间共享数据,Pod删除后数据丢失
- hostPath挂载节点目录,但Pod可能调度到不同节点
- 生产环境应使用PersistentVolume

---

## 第三部分: 实战项目 (60分钟)

### 任务3.1: 部署WordPress + MySQL

**目标**: 部署一个完整的Web应用,包含数据库

创建文件 `wordpress-app.yaml`:
```yaml
# MySQL密码
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
stringData:
  password: "MySecretPassword123"
---
# MySQL部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  labels:
    app: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        - name: MYSQL_DATABASE
          value: wordpress
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        emptyDir: {}
---
# MySQL服务
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
  clusterIP: None  # Headless service
---
# WordPress部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
  labels:
    app: wordpress
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
      - name: wordpress
        image: wordpress:6.4-apache
        env:
        - name: WORDPRESS_DB_HOST
          value: mysql
        - name: WORDPRESS_DB_NAME
          value: wordpress
        - name: WORDPRESS_DB_USER
          value: root
        - name: WORDPRESS_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        ports:
        - containerPort: 80
---
# WordPress服务
apiVersion: v1
kind: Service
metadata:
  name: wordpress
spec:
  type: NodePort
  selector:
    app: wordpress
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30090
```

```bash
# 部署整个应用
kubectl apply -f wordpress-app.yaml

# 查看所有资源
kubectl get all
kubectl get secrets

# 等待Pod就绪
kubectl get pods -w
# 按Ctrl+C退出

# 查看MySQL日志
kubectl logs -l app=mysql

# 查看WordPress日志
kubectl logs -l app=wordpress

# 访问WordPress(在浏览器打开)
echo "访问: http://192.168.56.11:30090"

# 测试负载均衡
for i in {1..5}; do
  curl -s http://192.168.56.11:30090 | grep -o '<title>.*</title>'
done

# 模拟故障恢复
kubectl get pods
# 删除一个WordPress Pod
kubectl delete pod <wordpress-pod-name>
# 观察自动重建
kubectl get pods -w

# 扩容WordPress
kubectl scale deployment wordpress --replicas=4
kubectl get pods

# 清理
kubectl delete -f wordpress-app.yaml
```

**验证点**:
- 多容器应用的部署
- Service作为服务发现(WordPress通过"mysql"域名连接数据库)
- Deployment的自愈能力
- 有状态应用(MySQL)和无状态应用(WordPress)的区别

---

### 任务3.2: 部署微服务应用 - 前后端分离

**目标**: 部署一个前后端分离的应用,理解微服务架构

创建文件 `microservices-app.yaml`:
```yaml
# 后端API
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
      tier: api
  template:
    metadata:
      labels:
        app: backend
        tier: api
    spec:
      containers:
      - name: api
        image: hashicorp/http-echo
        args:
        - "-text={\"status\":\"ok\",\"message\":\"Hello from Backend API\",\"version\":\"1.0\"}"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: backend-api
spec:
  selector:
    app: backend
    tier: api
  ports:
  - port: 80
    targetPort: 8080
---
# 前端Web
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-config
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>Microservices Demo</title>
      <style>
        body { font-family: Arial; margin: 50px; }
        button { padding: 10px 20px; font-size: 16px; }
        #result { margin-top: 20px; padding: 20px; background: #f0f0f0; }
      </style>
    </head>
    <body>
      <h1>Microservices Application</h1>
      <button onclick="callAPI()">Call Backend API</button>
      <div id="result"></div>
      <script>
        async function callAPI() {
          try {
            const response = await fetch('/api/');
            const data = await response.text();
            document.getElementById('result').innerHTML = 
              '<h3>API Response:</h3><pre>' + data + '</pre>';
          } catch (error) {
            document.getElementById('result').innerHTML = 
              '<h3>Error:</h3><pre>' + error + '</pre>';
          }
        }
      </script>
    </body>
    </html>
  nginx.conf: |
    server {
      listen 80;
      location / {
        root /usr/share/nginx/html;
        index index.html;
      }
      location /api/ {
        proxy_pass http://backend-api/;
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
      tier: web
  template:
    metadata:
      labels:
        app: frontend
        tier: web
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: frontend-config
          mountPath: /usr/share/nginx/html
          subPath: index.html
        - name: frontend-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: nginx.conf
      volumes:
      - name: frontend-config
        configMap:
          name: frontend-config
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-web
spec:
  type: NodePort
  selector:
    app: frontend
    tier: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30100
```

```bash
# 部署应用
kubectl apply -f microservices-app.yaml

# 查看所有资源
kubectl get all
kubectl get configmap

# 等待就绪
kubectl get pods -w
# 按Ctrl+C退出

# 测试前端
curl http://192.168.56.11:30100

# 测试API代理
curl http://192.168.56.11:30100/api/

# 在浏览器中打开并点击按钮测试
echo "浏览器访问: http://192.168.56.11:30100"

# 查看服务间通信
kubectl run debug --image=busybox --rm -it --restart=Never -- sh
# 在debug容器中:
# wget -O- http://backend-api
# exit

# 模拟后端升级
kubectl set image deployment/backend-api api=hashicorp/http-echo:latest
kubectl rollout status deployment/backend-api

# 查看更新过程
kubectl rollout history deployment/backend-api

# 清理
kubectl delete -f microservices-app.yaml
```

**验证点**:
- 前后端分离架构
- Nginx反向代理配置
- 服务间通信(frontend通过Service名称调用backend)
- 滚动更新

---

### 任务3.3: 健康检查与优雅关闭

**目标**: 配置健康检查,确保应用可靠性

创建文件 `health-check-demo.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-probes
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
      - name: app
        image: hashicorp/http-echo
        args:
        - "-text=I am healthy"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
        # 启动探针:容器启动后多久开始健康检查
        startupProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        # 存活探针:检测容器是否需要重启
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        # 就绪探针:检测容器是否可以接收流量
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        # 资源限制
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        # 优雅关闭
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
---
apiVersion: v1
kind: Service
metadata:
  name: demo-service
spec:
  selector:
    app: demo
  ports:
  - port: 80
    targetPort: 8080
```

```bash
# 部署
kubectl apply -f health-check-demo.yaml

# 观察Pod启动过程
kubectl get pods -w
# 注意READY列从0/1变为1/1的过程

# 查看Pod详情
kubectl describe pod -l app=demo | grep -A 10 "Conditions:"

# 模拟存活探针失败(进入容器杀死进程)
POD=$(kubectl get pod -l app=demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- killall http-echo

# 观察Pod自动重启
kubectl get pods -w
# 看到RESTARTS列增加

# 模拟就绪探针失败
# (实际应用中,可以通过停止应用进程或返回非200状态码)

# 查看Service的Endpoints
kubectl get endpoints demo-service

# 测试滚动更新时的零停机
# 在一个终端持续访问
while true; do 
  curl -s http://192.168.56.11:$(kubectl get svc demo-service -o jsonpath='{.spec.ports[0].nodePort}') || echo "Failed"
  sleep 0.5
done

# 在另一个终端执行更新
kubectl set image deployment/app-with-probes app=hashicorp/http-echo:latest

# 观察更新过程中没有请求失败

# 清理
kubectl delete -f health-check-demo.yaml
```

**验证点**:
- startupProbe用于慢启动应用
- livenessProbe检测死锁,失败后重启容器
- readinessProbe控制是否接收流量
- preStop钩子实现优雅关闭

---

## 第四部分: 进阶主题 (30分钟)

### 任务4.1: 资源配额与限制

**目标**: 限制命名空间的资源使用

```bash
# 创建新命名空间
kubectl create namespace quota-demo

# 创建ResourceQuota
kubectl create -f - << EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: quota-demo
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
    pods: "5"
EOF

# 查看配额
kubectl describe quota compute-quota -n quota-demo

# 尝试创建Pod(会受配额限制)
kubectl run nginx --image=nginx -n quota-demo
# 失败:必须指定资源requests/limits

# 创建符合配额的Pod
kubectl run nginx --image=nginx -n quota-demo \
  --requests='cpu=100m,memory=128Mi' \
  --limits='cpu=200m,memory=256Mi'

# 查看资源使用情况
kubectl describe quota -n quota-demo

# 尝试超出配额
for i in {1..6}; do
  kubectl run pod-$i --image=nginx -n quota-demo \
    --requests='cpu=100m,memory=128Mi' \
    --limits='cpu=200m,memory=256Mi'
done
# 第6个会失败:超出pod数量限制

# 清理
kubectl delete namespace quota-demo
```

**验证点**:
- ResourceQuota限制命名空间资源
- Pod必须设置requests/limits才能创建
- 达到配额上限后无法创建新资源

---

### 任务4.2: 网络策略(NetworkPolicy)

**目标**: 使用NetworkPolicy控制Pod间通信

```bash
# 创建测试环境
kubectl create namespace netpol-demo

# 创建前端和后端应用
kubectl create deployment frontend --image=nginx -n netpol-demo
kubectl create deployment backend --image=nginx -n netpol-demo
kubectl create deployment database --image=nginx -n netpol-demo

# 给Pod打标签
kubectl label pod -l app=frontend tier=frontend -n netpol-demo
kubectl label pod -l app=backend tier=backend -n netpol-demo
kubectl label pod -l app=database tier=database -n netpol-demo

# 暴露服务
kubectl expose deployment backend --port=80 -n netpol-demo
kubectl expose deployment database --port=80 -n netpol-demo

# 测试默认情况(所有Pod互通)
kubectl run test --image=busybox -n netpol-demo --rm -it --restart=Never -- \
  wget -O- http://backend --timeout=2

# 应用网络策略:只允许backend访问database
kubectl create -f - << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-policy
  namespace: netpol-demo
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 80
EOF

# 测试frontend访问database(应该被拒绝)
FRONTEND_POD=$(kubectl get pod -l app=frontend -n netpol-demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec $FRONTEND_POD -n netpol-demo -- wget -O- http://database --timeout=5
# 应该超时

# 测试backend访问database(应该成功)
BACKEND_POD=$(kubectl get pod -l app=backend -n netpol-demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec $BACKEND_POD -n netpol-demo -- wget -O- http://database --timeout=5

# 清理
kubectl delete namespace netpol-demo
```

**验证点**:
- NetworkPolicy实现微隔离
- 默认情况下K8s允许所有Pod通信
- NetworkPolicy可以限制入站(Ingress)和出站(Egress)流量

**注意**: K3s默认不支持NetworkPolicy,需要安装Calico等CNI插件。如果测试失败,这是正常的。

---

### 任务4.3: 任务和定时任务

**目标**: 使用Job和CronJob运行批处理任务

创建文件 `jobs-demo.yaml`:
```yaml
# 一次性任务
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: busybox
        command: ["/bin/sh", "-c"]
        args:
        - |
          echo "Starting data migration..."
          for i in $(seq 1 10); do
            echo "Processing record $i/10"
            sleep 2
          done
          echo "Migration completed successfully"
      restartPolicy: Never
  backoffLimit: 3
---
# 并行任务
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-processing
spec:
  parallelism: 3
  completions: 6
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["/bin/sh", "-c"]
        args:
        - |
          echo "Worker starting: $HOSTNAME"
          sleep 10
          echo "Worker done: $HOSTNAME"
      restartPolicy: Never
---
# 定时任务
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "*/2 * * * *"  # 每2分钟执行一次
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ["/bin/sh", "-c"]
            args:
            - |
              echo "=== Backup started at $(date) ==="
              echo "Backing up database..."
              sleep 5
              echo "Backup completed"
          restartPolicy: OnFailure
```

```bash
# 部署
kubectl apply -f jobs-demo.yaml

# 查看Job
kubectl get jobs

# 查看Job的Pod
kubectl get pods

# 查看一次性任务的日志
kubectl logs -l job-name=data-migration

# 观察并行任务
kubectl get pods -l job-name=parallel-processing -w
# 看到3个Pod并行运行,完成后启动新的,直到6个都完成

# 查看CronJob
kubectl get cronjob

# 等待2分钟后查看执行历史
sleep 130
kubectl get jobs  # 应该看到backup-job-xxxxx

# 查看CronJob创建的Job日志
kubectl logs -l job-name=<backup-job-xxxxx>

# 手动触发CronJob
kubectl create job --from=cronjob/backup-job manual-backup

# 清理
kubectl delete -f jobs-demo.yaml
```

**验证点**:
- Job用于一次性任务
- 支持并行和串行执行
- CronJob定时执行任务
- 失败后自动重试(backoffLimit)

---

## 第五部分: 综合实战项目 (60分钟)

### 任务5.1: 完整的电商微服务系统

**目标**: 部署一个包含多个微服务的完整应用

创建文件 `ecommerce-system.yaml`:
```yaml
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: ecommerce
---
# Redis缓存
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: ecommerce
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: ecommerce
spec:
  selector:
    app: redis
  ports:
  - port: 6379
---
# 用户服务
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
  namespace: ecommerce
data:
  SERVICE_NAME: "user-service"
  REDIS_HOST: "redis"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: ecommerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        version: v1
    spec:
      containers:
      - name: service
        image: hashicorp/http-echo
        args:
        - "-text={\"service\":\"user\",\"version\":\"v1\",\"users\":[\"alice\",\"bob\"]}"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: user-service-config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 3
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: ecommerce
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 8080
---
# 商品服务
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
  namespace: ecommerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: product-service
  template:
    metadata:
      labels:
        app: product-service
        version: v1
    spec:
      containers:
      - name: service
        image: hashicorp/http-echo
        args:
        - "-text={\"service\":\"product\",\"version\":\"v1\",\"products\":[\"laptop\",\"phone\",\"tablet\"]}"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: product-service
  namespace: ecommerce
spec:
  selector:
    app: product-service
  ports:
  - port: 80
    targetPort: 8080
---
# 订单服务
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: ecommerce
spec:
  replicas: 2
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
      - name: service
        image: hashicorp/http-echo
        args:
        - "-text={\"service\":\"order\",\"version\":\"v1\",\"orders\":[]}"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: ecommerce
spec:
  selector:
    app: order-service
  ports:
  - port: 80
    targetPort: 8080
---
# API Gateway
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-nginx-config
  namespace: ecommerce
data:
  nginx.conf: |
    server {
      listen 80;
      
      location /api/users {
        proxy_pass http://user-service/;
      }
      
      location /api/products {
        proxy_pass http://product-service/;
      }
      
      location /api/orders {
        proxy_pass http://order-service/;
      }
      
      location / {
        return 200 '{"message":"E-commerce API Gateway","endpoints":["/api/users","/api/products","/api/orders"]}';
        add_header Content-Type application/json;
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: ecommerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: nginx.conf
      volumes:
      - name: nginx-config
        configMap:
          name: gateway-nginx-config
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: ecommerce
spec:
  type: NodePort
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30200
```

```bash
# 部署整个系统
kubectl apply -f ecommerce-system.yaml

# 查看所有资源
kubectl get all -n ecommerce

# 等待所有Pod就绪
kubectl get pods -n ecommerce -w

# 测试API Gateway
curl http://192.168.56.11:30200/

# 测试各个服务
curl http://192.168.56.11:30200/api/users
curl http://192.168.56.11:30200/api/products
curl http://192.168.56.11:30200/api/orders

# 查看服务依赖关系
kubectl get svc -n ecommerce

# 进入一个Pod测试服务发现
kubectl run debug -n ecommerce --image=busybox --rm -it --restart=Never -- sh
# 在容器内:
# nslookup user-service
# wget -O- http://user-service
# wget -O- http://product-service
# exit

# 模拟流量负载测试
for i in {1..20}; do
  curl -s http://192.168.56.11:30200/api/products &
done
wait

# 查看Pod分布
kubectl get pods -n ecommerce -o wide

# 扩容某个服务
kubectl scale deployment product-service -n ecommerce --replicas=5
kubectl get pods -n ecommerce -w

# 查看资源使用
kubectl top pods -n ecommerce

# 清理
kubectl delete namespace ecommerce
```

**验证点**:
- 微服务架构实践
- API Gateway模式
- 服务间通信
- 水平扩展
- 资源管理

---

## 第六部分: 故障排查与最佳实践 (20分钟)

### 任务6.1: 常见问题排查

**目标**: 学习调试技巧

```bash
# 创建一个有问题的应用
kubectl create deployment broken-app --image=nginx:wrong-tag

# 问题1: ImagePullBackOff
kubectl get pods
kubectl describe pod <broken-app-pod>  # 查看Events
kubectl logs <broken-app-pod>  # 可能没有日志

# 修复
kubectl set image deployment/broken-app nginx=nginx:alpine
kubectl delete deployment broken-app

# 问题2: CrashLoopBackOff
kubectl run crash-app --image=busybox --command -- /bin/sh -c "exit 1"
kubectl get pods
kubectl logs crash-app
kubectl describe pod crash-app

# 清理
kubectl delete pod crash-app

# 问题3: Service无法访问
kubectl create deployment test-app --image=nginx
kubectl expose deployment test-app --port=8080 --target-port=80  # 错误的targetPort

# 诊断
kubectl get svc test-app
kubectl get endpoints test-app  # Endpoints为空

# 修复
kubectl delete svc test-app
kubectl expose deployment test-app --port=80 --target-port=80

# 验证
kubectl get endpoints test-app
kubectl run test --image=busybox --rm -it --restart=Never -- wget -O- http://test-app

# 清理
kubectl delete deployment test-app
kubectl delete svc test-app
```

---

### 任务6.2: Kubernetes最佳实践检查清单

**实践要点**:

1. **资源管理**
   - 始终设置resources requests和limits
   - 使用ResourceQuota限制命名空间资源
   - 定期查看资源使用情况

2. **健康检查**
   - 配置livenessProbe和readinessProbe
   - 设置合理的超时和重试次数
   - 使用startupProbe处理慢启动应用

3. **配置管理**
   - 使用ConfigMap管理配置
   - 使用Secret管理敏感信息
   - 避免在镜像中硬编码配置

4. **标签和选择器**
   - 使用有意义的标签(app, version, tier等)
   - 通过标签组织和查询资源
   - 使用命名空间隔离不同环境

5. **安全**
   - 不使用latest标签,指定具体版本
   - 使用非root用户运行容器
   - 启用NetworkPolicy限制流量
   - 定期更新镜像修复安全漏洞

6. **可观测性**
   - 应用输出结构化日志到stdout/stderr
   - 暴露metrics端点
   - 使用统一的日志聚合系统

---

## 练习总结

完成这些任务后,你应该掌握:

**基础概念**:
- Pod、Deployment、Service、ConfigMap、Secret
- 资源请求与限制
- 健康检查机制
- 存储卷的使用

**实战能力**:
- 部署单体应用和微服务应用
- 配置服务发现和负载均衡
- 实现滚动更新和回滚
- 处理有状态和无状态应用

**运维技能**:
- 故障排查和日志分析
- 资源配额管理
- 水平扩展
- 最佳实践应用

---

## 下一步学习建议

1. **深入学习**:
   - Helm包管理
   - Ingress Controller
   - StatefulSet和DaemonSet
   - PersistentVolume和StorageClass

2. **可观测性**:
   - Prometheus监控
   - Grafana可视化
   - ELK日志栈

3. **CI/CD集成**:
   - GitOps(ArgoCD/FluxCD)
   - Jenkins/GitLab CI与K8s集成

4. **生产环境准备**:
   - 高可用集群搭建
   - 备份与恢复
   - 安全加固
   - 性能优化

---

## 清理所有练习资源

```bash
# 删除所有测试资源
kubectl delete all --all
kubectl delete configmap --all
kubectl delete secret --all
kubectl delete namespace netpol-demo quota-demo ecommerce 2>/dev/null

# 验证清理
kubectl get all
```