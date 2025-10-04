## Pod创建的完整流程

### 1. **kubectl发起请求**

bash

```bash
kubectl run nginx --image=nginx:alpine
```

kubectl做的事：

- 构造Pod对象的JSON/YAML
- 调用API Server的REST API
- 发送HTTP POST请求到 `https://192.168.56.11:6443/api/v1/namespaces/default/pods`

### 2. **API Server处理请求**

API Server收到请求后：

1. 认证（Authentication）
   - 验证请求者身份（通过kubeconfig的证书）
2. 鉴权（Authorization）
   - 检查用户是否有权限创建Pod（RBAC规则）
3. 准入控制（Admission Control）
   - 运行一系列准入控制器
   - 例如：ResourceQuota（检查配额）、LimitRanger（设置默认资源）
4. 验证（Validation）
   - 检查Pod定义是否合法（必填字段、格式等）
5. 持久化
   - 将Pod对象写入etcd
   - 此时Pod状态为 `Pending`

### 3. **Scheduler调度**

**Scheduler** 持续监听API Server：

1. 监听新Pod
   - Watch API: `GET /api/v1/pods?watch=true&fieldSelector=spec.nodeName=`
   - 发现未调度的Pod（nodeName为空）
2. 预选（Predicate）
   - 过滤不符合条件的节点
   - 检查：资源是否足够、端口是否冲突、亲和性规则等
3. 优选（Priority）
   - 给通过预选的节点打分
   - 考虑：资源使用率、亲和性权重、数据本地性等
4. 绑定（Bind）
   - 选择得分最高的节点
   - 调用API Server的Bind接口
   - 更新Pod的 `spec.nodeName` 字段

### 4. **Kubelet创建容器**

**目标节点的Kubelet** 持续监听API Server：

1. 监听Pod变化
   - Watch API: `GET /api/v1/nodes/{node-name}/pods`
   - 发现调度到本节点的新Pod
2. **准备工作**

```
   - 创建Pod的网络命名空间
   - 分配Pod IP（通过CNI插件，如Flannel）
   - 创建Pod的数据卷目录
   - 拉取镜像（如果不存在）
```

1. **启动容器**

```
   顺序：
   a. Init容器（如果有）
      - 按顺序启动
      - 必须全部成功
   
   b. Pause容器（沙箱容器）
      - 维持Pod的网络命名空间
      - 镜像：rancher/mirrored-pause:3.6
   
   c. 主容器
      - 调用containerd创建容器
      - 挂载数据卷
      - 注入环境变量、ConfigMap、Secret
      - 执行PostStart钩子
```

1. 健康检查
   - 执行StartupProbe（如果配置）
   - 执行LivenessProbe
   - 执行ReadinessProbe
2. 状态上报
   - 将容器状态报告给API Server
   - 更新Pod状态：`Pending` → `ContainerCreating` → `Running`

### 5. **Controller Manager（后台）**

虽然不直接参与Pod创建，但持续监控：

- **Endpoint Controller**: 如果Pod有Service，更新Endpoints
- **Node Controller**: 监控节点健康状态
- **ReplicaSet Controller**: 如果是Deployment的Pod，确保副本数正确

------

## 流程图

```
kubectl run nginx
    │
    ▼
┌─────────────────┐
│  API Server     │ 1. 认证、鉴权、准入控制
│  (kube-apiserver)│ 2. 写入etcd
└────────┬────────┘ 3. 状态: Pending
         │
         │ watch
         ▼
┌─────────────────┐
│   Scheduler     │ 1. 预选节点
│ (kube-scheduler)│ 2. 优选打分
└────────┬────────┘ 3. 绑定到节点
         │          4. 更新spec.nodeName
         │
         │ watch
         ▼
┌─────────────────┐
│    Kubelet      │ 1. 创建网络namespace
│  (目标节点)      │ 2. 分配Pod IP
└────────┬────────┘ 3. 拉取镜像
         │          4. 创建容器
         │          5. 启动容器
         │          6. 健康检查
         ▼
    [Running]
```

------

## 实际观察

你可以通过命令观察这个过程：

bash

```bash
# 创建Pod
kubectl run nginx --image=nginx:alpine

# 实时观察状态变化
kubectl get pods -w

# 查看事件（完整流程）
kubectl describe pod nginx

# 在K9s中按'd'查看describe，Events部分会显示：
# - Scheduled: 被调度到哪个节点
# - Pulling: 拉取镜像
# - Pulled: 镜像拉取完成
# - Created: 容器创建
# - Started: 容器启动
```

------

## API调用示例

如果想看实际的API调用，可以用 `--v=8` 参数：

bash

```bash
kubectl run test --image=nginx:alpine --v=8
```

会输出所有HTTP请求细节，包括：

- POST请求创建Pod
- API Server返回的响应
- 认证过程

------

这就是创建Pod的完整流程。每个组件都通过Watch API Server来协同工作，这种"声明式"架构是Kubernetes的核心设计理念。