### 1. Service的工作原理

你看到WordPress通过 `mysql` 这个名称连接数据库，背后的机制：

**DNS解析**：

```
WordPress容器请求 "mysql"
    ↓
CoreDNS解析为 Service的ClusterIP (或Pod IP列表)
    ↓
请求发送到目标地址
```

**三种Service模式对比**：

```
类型ClusterIP实际案例
ClusterIP10.106.49.55wordpress Service
None (Headless)无ClusterIPmysql Service
NodePortClusterIP + NodePortwordpress:30080
```

**Headless Service**（mysql使用的）：

- `clusterIP: None`
- DNS直接返回Pod IP列表
- 适合有状态服务（数据库、缓存）
- 客户端自己做负载均衡



## Service类型的设置和应用场景

Service类型在YAML的 `spec.type` 字段设置：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP  # 或 NodePort、LoadBalancer
  # type不写默认就是ClusterIP
```

------

## 三种类型详解

### 1. ClusterIP（默认）

**配置**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP  # 可以省略，默认就是这个
  selector:
    app: backend
  ports:
  - port: 80        # Service端口
    targetPort: 8080 # Pod端口
```

**特点**：

- 分配一个集群内部IP（如 10.106.49.55）
- **只能在集群内部访问**
- DNS解析返回这个ClusterIP
- kube-proxy负责转发到后端Pod

**应用场景**：

- 内部微服务通信（前端调用后端API）
- 不需要暴露到集群外的服务
- 数据库、缓存等中间件（如果不需要外部访问）

**工作流程**：

```
前端Pod访问 backend-service:80
    ↓
DNS解析为 10.106.49.55
    ↓
kube-proxy拦截请求
    ↓
转发到某个backend Pod的8080端口
```

------

### 2. Headless Service（ClusterIP: None）

**配置**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None  # 关键：设为None
  selector:
    app: mysql
  ports:
  - port: 3306
```

**特点**：

- **不分配ClusterIP**
- DNS直接返回所有Pod的IP列表
- 客户端自己选择连接哪个Pod
- 没有负载均衡（或由客户端实现）

**DNS行为**：

```bash
# 普通Service
nslookup backend-service
# 返回：10.106.49.55 (Service的ClusterIP)

# Headless Service
nslookup mysql
# 返回：10.42.1.5, 10.42.2.8 (所有Pod的IP)
```

**应用场景**：

1. **有状态服务**（StatefulSet）
   - 数据库主从集群（需要区分master/slave）
   - Redis集群（需要直连特定节点）
   - Kafka、Zookeeper等
2. **需要Pod稳定标识**
   - 每个Pod有固定的DNS名称
   - 如：`mysql-0.mysql.default.svc.cluster.local`
3. **自定义负载均衡**
   - 客户端自己实现连接池
   - 需要sticky session（会话保持）

**为什么数据库用Headless**：

```
主从架构的MySQL：
- master: mysql-0 (写操作)
- slave1: mysql-1 (读操作)
- slave2: mysql-2 (读操作)

应用需要：
- 写请求 → 直连mysql-0
- 读请求 → 随机选择slave

如果用普通Service：
- 写请求可能被转发到slave（错误）
- 无法区分master和slave
```

------

### 3. NodePort

**配置**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: NodePort
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # 30000-32767范围，可省略自动分配
```

**特点**：

- 在所有节点上开放相同端口（30080）
- 通过 `<任意节点IP>:30080` 访问
- 同时创建ClusterIP（内部仍可用）

**访问方式**：

```bash
# 外部访问
curl http://192.168.56.11:30080
curl http://192.168.56.21:30080
curl http://192.168.56.22:30080
# 访问任何节点都能到达服务

# 内部访问（仍然可用）
curl http://frontend:80
```

**应用场景**：

1. **开发/测试环境**
   - 快速暴露服务到外部
   - 不需要LoadBalancer
2. **本地集群**
   - Minikube、Kind、裸机K8s
   - 没有云厂商LoadBalancer
3. **特定端口需求**
   - 需要固定端口的传统应用
   - 防火墙只开放特定端口

**缺点**：

- 端口范围限制（30000-32767）
- 每个Service占用一个端口
- 需要管理端口分配
- 没有SSL终止

------

## 实际对比示例

```yaml
# 场景：电商系统

# 1. 前端 - NodePort（给用户访问）
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: NodePort
  selector:
    app: frontend
  ports:
  - port: 80
    nodePort: 30080

# 2. API服务 - ClusterIP（内部调用）
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: ClusterIP  # 只在集群内访问
  selector:
    app: api
  ports:
  - port: 8080

# 3. MySQL主从 - Headless（区分master/slave）
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None  # Headless
  selector:
    app: mysql
  ports:
  - port: 3306

# 访问流程：
# 用户 → frontend:30080 → api-service:8080 → mysql:3306
```

------

## 何时用哪种

| 场景                      | 推荐类型     | 原因             |
| ------------------------- | ------------ | ---------------- |
| 微服务内部通信            | ClusterIP    | 不暴露，简单高效 |
| 对外提供服务（测试）      | NodePort     | 快速暴露         |
| 对外提供服务（生产）      | LoadBalancer | 云厂商负载均衡   |
| 数据库主从                | Headless     | 需要区分实例     |
| 有状态应用（StatefulSet） | Headless     | 稳定的网络标识   |
| 需要自定义LB              | Headless     | 客户端控制       |

------

## 你的理解补充

你说的"Headless只需要名称就可以自行解析，类似域名"是对的，但更准确的说：

**Headless Service的价值**：

1. DNS返回Pod IP列表而非单一ClusterIP
2. 每个Pod有稳定的DNS名称（配合StatefulSet）
3. 客户端可以自己选择连接哪个Pod

不是"不需要负载均衡"，而是"需要更精细的控制"，比如：

- 写请求必须到master
- 读请求可以到任意slave
- 需要会话保持到同一个Pod

在本地K3s环境测试这三种类型的区别吗？用已有的nginx镜像就能演示。