## 主题：Kubernetes网络模型

### 1. Kubernetes网络三大原则

K8s要求网络满足三个基本条件：

**原则1：所有Pod可以互相通信，无需NAT**

```
Pod A (10.42.1.5) 可以直接访问 Pod B (10.42.2.8)
不需要端口映射，不需要地址转换
```

**原则2：所有节点可以与所有Pod通信，无需NAT**

```
节点 192.168.56.11 可以直接访问任意Pod 10.42.x.x
```

**原则3：Pod看到的自己的IP，和别人看到的IP一致**

```
Pod内执行 ip addr → 10.42.1.5
外部访问这个Pod → 也是 10.42.1.5
不像Docker有内部IP和映射的外部IP
```

### 2. CNI插件的作用

**CNI (Container Network Interface)** 负责实现这三个原则。

你的K3s集群用的是Flannel，工作流程：

**Pod创建时**：

```
1. kubelet调用CNI插件（Flannel）
2. Flannel分配Pod IP（从节点的CIDR段）
3. 创建网络命名空间
4. 配置veth pair连接Pod和节点
5. 设置路由规则
```

**跨节点通信**：

```
Node1的Pod-A (10.42.1.5) 访问 Node2的Pod-B (10.42.2.8)

1. Pod-A发出数据包，目标 10.42.2.8
2. 查路由表：10.42.2.0/24 via flannel.1
3. Flannel封装数据包（VXLAN隧道）
4. 通过物理网络发送到Node2
5. Node2的Flannel解封装
6. 转发到Pod-B
```

### 3. kube-proxy的三种模式

Service的负载均衡由kube-proxy实现，有三种模式：

**模式1：iptables（默认，K3s使用）**

```bash
# 当创建Service时，kube-proxy写入iptables规则
# 查看规则（在你的K3s集群）
kubectl get svc wordpress -o wide
# ClusterIP: 10.106.49.55

# 在节点上查看iptables
ssh vagrant@192.168.56.11 'sudo iptables-save | grep 10.106.49.55'
```

工作原理：

```
访问 ClusterIP:80
    ↓
iptables拦截（DNAT）
    ↓
随机选择一个Pod IP
    ↓
转发到Pod:8080
```

特点：

- 稳定、成熟
- 性能一般（规则多时性能下降）
- 随机负载均衡

**模式2：ipvs（性能更好）**

使用Linux内核的IPVS模块：

```
优势：
- 更高性能
- 支持多种负载均衡算法（轮询、最少连接等）
- 大规模集群表现更好

劣势：
- 需要加载内核模块
- 调试相对复杂
```

**模式3：eBPF（最新，Cilium使用）**

利用Linux eBPF技术：

```
优势：
- 性能最高
- 更灵活的网络策略
- 可观测性强

劣势：
- 需要较新内核（4.19+）
- 配置复杂
```

### 4. DNS服务发现机制

你看到WordPress用"mysql"访问数据库，DNS解析过程：

**CoreDNS配置**：

```yaml
# K8s集群默认的DNS服务
apiVersion: v1
kind: Service
metadata:
  name: kube-dns
  namespace: kube-system
spec:
  clusterIP: 10.96.0.10  # 这是集群DNS服务器
```

**Pod的DNS配置**（自动注入）：

```bash
# 每个Pod的 /etc/resolv.conf
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
```

**解析规则**：

```
请求 "mysql"
    ↓
尝试 mysql.default.svc.cluster.local
    ↓
CoreDNS查询：
  - Service名称 "mysql"
  - 命名空间 "default"
    ↓
返回结果：
  - 普通Service → ClusterIP
  - Headless Service → Pod IP列表
```

**完整域名格式**：

```
<service-name>.<namespace>.svc.cluster.local

示例：
mysql.default.svc.cluster.local
wordpress.default.svc.cluster.local
api-service.production.svc.cluster.local
```

### 5. Service到Pod的转发流程

完整流程图：

```
客户端Pod
    ↓ (1) 访问 wordpress:80
DNS解析
    ↓ (2) 返回 10.106.49.55
发送请求到 10.106.49.55:80
    ↓ (3) 节点拦截
kube-proxy (iptables规则)
    ↓ (4) DNAT转换
选择后端Pod：10.42.1.8:8080
    ↓ (5) 转发
Flannel跨节点路由
    ↓ (6) 到达目标
目标Pod收到请求
```

### 6. 实际验证

在你的K3s集群可以验证：

```bash
# 1. 查看Pod的DNS配置
kubectl run test --image=busybox --rm -it --restart=Never -- cat /etc/resolv.conf

# 2. 查看Service的iptables规则
kubectl get svc wordpress -o jsonpath='{.spec.clusterIP}'
# 假设是 10.106.49.55
ssh vagrant@192.168.56.11 'sudo iptables-save | grep 10.106.49.55 | head -5'

# 3. 查看Flannel路由
ssh vagrant@192.168.56.11 'ip route | grep flannel'

# 4. 查看CoreDNS配置
kubectl get configmap coredns -n kube-system -o yaml
```

------

## 总结：网络分层

```
Layer 4: Service抽象层
  - ClusterIP/NodePort/LoadBalancer
  - kube-proxy负责转发

Layer 3: Pod网络层
  - CNI插件（Flannel/Calico等）
  - 跨节点通信

Layer 2: 服务发现层
  - CoreDNS
  - Service名称解析
```

------

接下来想学：

1. **存储架构** - PV/PVC/StorageClass原理
2. **调度机制** - Scheduler如何选择节点
3. **安全模型** - RBAC、准入控制
4. **或其他网络主题** - Ingress、NetworkPolicy

