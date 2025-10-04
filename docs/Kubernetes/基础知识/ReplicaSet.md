## ReplicaSet的控制循环（Reconciliation Loop）

Deployment通过**ReplicaSet Controller**持续监控和调谐来保证副本数。

### 核心机制：控制循环

**ReplicaSet Controller**在Controller Manager中运行，执行无限循环：

```
while true:
    1. 观察当前状态（实际运行的Pod数）
    2. 对比期望状态（replicas=3）
    3. 如果不一致，采取行动
    4. 等待一段时间，重复
```

### 具体实现

**1. 监听变化**

ReplicaSet Controller通过Watch API监听：

- ReplicaSet对象的变化
- 匹配label的Pod的变化

go

```go
// Controller伪代码
watch := client.Watch(ReplicaSets)
for event := range watch {
    if event.Type == "MODIFIED" {
        reconcile(event.Object)
    }
}
```

**2. 调谐逻辑（Reconciliation）**

go

```go
func reconcile(rs ReplicaSet) {
    // 查询匹配label selector的所有Pod
    pods := getPods(rs.Spec.Selector)
    currentReplicas := len(pods)
    desiredReplicas := rs.Spec.Replicas
    
    if currentReplicas < desiredReplicas {
        // 需要创建Pod
        diff := desiredReplicas - currentReplicas
        for i := 0; i < diff; i++ {
            createPod(rs.Spec.Template)
        }
    } else if currentReplicas > desiredReplicas {
        // 需要删除Pod
        diff := currentReplicas - desiredReplicas
        for i := 0; i < diff; i++ {
            deletePod(pods[i])
        }
    }
    // currentReplicas == desiredReplicas: 什么都不做
}
```

**3. 触发调谐的场景**

- 创建Deployment时
- 修改replicas时（scale up/down）
- Pod被删除时（手动删除或崩溃）
- Pod失败时（CrashLoopBackOff）
- 节点故障时（Pod不可达）

------

## 实际演示

bash

```bash
# 创建Deployment
kubectl create deployment test --image=nginx:alpine --replicas=3

# 观察ReplicaSet
kubectl get rs
# NAME               DESIRED   CURRENT   READY
# test-xxxx          3         3         3

# 手动删除一个Pod
kubectl delete pod <pod-name>

# 立即查看
kubectl get pods -w
# 会看到：
# 1. 一个Pod状态变为Terminating
# 2. 几乎同时，新Pod被创建（Pending → Running）
```

### 观察调谐过程

bash

```bash
# 在一个终端持续观察
kubectl get pods -l app=test -w

# 在另一个终端删除Pod
kubectl delete pod -l app=test --all

# 第一个终端会看到：
# - 3个Pod进入Terminating
# - 立即创建3个新Pod
# - ReplicaSet确保始终有3个Running
```

------

## 控制器的特性

### 1. **最终一致性（Eventual Consistency）**

- 不保证瞬时一致
- 但保证最终会达到期望状态
- 删除Pod后可能有短暂的时间少于3个

### 2. **幂等性（Idempotent）**

- 重复执行调谐操作结果相同
- 已经是3个Pod时，不会创建新的

### 3. **声明式（Declarative）**

- 你声明"我要3个Pod"
- 控制器负责实现"如何达到3个"

------

## 失败场景处理

### 场景1: Pod崩溃

```
Pod-1: Running
Pod-2: Running  
Pod-3: CrashLoopBackOff

Controller观察到:
- 只有2个Running
- 不会删除崩溃的Pod
- 会持续重启Pod-3（kubelet负责）
- 总数仍然是3个
```

### 场景2: 节点故障

```
Node-1 宕机，上面有Pod-1

Controller操作:
1. 等待Pod-1变为Unknown（约40秒）
2. 在其他节点创建新Pod-1'
3. 旧Pod-1会被标记为Terminating
4. 最终总数回到3个
```

### 场景3: 资源不足

```
集群没有足够资源创建新Pod

Controller行为:
- 持续尝试创建Pod
- Pod会停在Pending状态
- 不会放弃，直到成功或被删除
```

------

## 验证机制

你可以看到ReplicaSet的调谐日志：

bash

```bash
# 查看ReplicaSet events
kubectl describe rs <replicaset-name>

# 输出类似：
# Events:
#   Type    Reason            Age   From                   Message
#   ----    ------            ----  ----                   -------
#   Normal  SuccessfulCreate  5m    replicaset-controller  Created pod: test-xxxx-1
#   Normal  SuccessfulCreate  5m    replicaset-controller  Created pod: test-xxxx-2
#   Normal  SuccessfulCreate  5m    replicaset-controller  Created pod: test-xxxx-3
#   Normal  SuccessfulDelete  2m    replicaset-controller  Deleted pod: test-xxxx-2
#   Normal  SuccessfulCreate  2m    replicaset-controller  Created pod: test-xxxx-4
```

------

## Owner References（所有权关系）

ReplicaSet通过**OwnerReference**跟踪它创建的Pod：

yaml

```yaml
# Pod的metadata
metadata:
  ownerReferences:
  - apiVersion: apps/v1
    kind: ReplicaSet
    name: nginx-deployment-xxxx
    uid: xxxxxx
    controller: true
```

当Pod被删除时，API Server通知ReplicaSet Controller，触发调谐。

------

## 总结

保证3个副本的关键：

1. **持续监控**：Watch API监听变化
2. **控制循环**：不断对比期望与实际状态
3. **自动修复**：检测到差异立即采取行动
4. **所有权追踪**：通过OwnerReference跟踪Pod

这种"控制循环"模式是Kubernetes所有Controller的核心设计，不只是ReplicaSet，DaemonSet、StatefulSet、Job等都是同样的原理。

AC

明白了,那当扩容和缩容时,也是类似的机制么

Edit

完全正确，扩容和缩容就是同样的调谐机制，只是触发条件不同。

## 扩容（Scale Up）

bash

```bash
kubectl scale deployment nginx-deployment --replicas=5
```

**发生的事情**：

1. API Server更新
   - kubectl修改Deployment的 `spec.replicas: 3 → 5`
   - 写入etcd
2. Deployment Controller触发
   - Watch到Deployment变化
   - 更新对应ReplicaSet的replicas: `3 → 5`
3. **ReplicaSet Controller调谐**

```
   当前状态: 3个Pod运行中
   期望状态: 5个Pod
   差值: 需要创建2个Pod
   
   行动: 
   - 创建Pod-4
   - 创建Pod-5
```

1. Scheduler + Kubelet
   - Scheduler调度新Pod到节点
   - Kubelet创建容器

**特点**：

- 所有Pod同时创建（并行）
- 不会等待旧Pod
- 新Pod和旧Pod完全平等

------

## 缩容（Scale Down）

bash

```bash
kubectl scale deployment nginx-deployment --replicas=2
```

**发生的事情**：

1. **ReplicaSet Controller调谐**

```
   当前状态: 5个Pod运行中
   期望状态: 2个Pod
   差值: 需要删除3个Pod
   
   行动:
   - 选择3个Pod删除
   - 发送删除请求
```

1. **删除顺序（重要）** ReplicaSet按以下优先级选择要删除的Pod：

```
   优先删除：
   1. Unscheduled（未调度的）
   2. Pending（等待中的）
   3. Unknown/Not Ready（状态异常的）
   4. Ready但运行时间短的
   5. 最后才删除健康且运行时间长的
```

1. **优雅终止** 被选中的Pod执行终止流程：

```
   1. Pod标记为Terminating
   2. 从Service的Endpoints移除（不再接收新请求）
   3. 执行PreStop钩子
   4. 发送SIGTERM信号给容器
   5. 等待terminationGracePeriodSeconds（默认30秒）
   6. 超时后发送SIGKILL强制终止
```

**特点**：

- 智能选择删除对象
- 优先删除不健康的
- 优雅终止，避免请求丢失

------

## 实际观察

bash

```bash
# 创建Deployment
kubectl create deployment test --image=nginx:alpine --replicas=3

# 观察扩容
kubectl scale deployment test --replicas=6
kubectl get pods -w
# 会看到3个新Pod同时创建

# 观察缩容
kubectl scale deployment test --replicas=2
kubectl get pods -w
# 会看到4个Pod同时进入Terminating
```

------

## 滚动更新时的特殊情况

滚动更新时，扩缩容机制更复杂：

bash

```bash
kubectl set image deployment/test nginx=nginx:1.26
```

**过程**：

1. 创建新ReplicaSet
   - 新版本的ReplicaSet，replicas=0
2. **逐步扩容新ReplicaSet，缩容旧ReplicaSet**

```
   初始: 旧RS=3, 新RS=0
   
   步骤1: 旧RS=2, 新RS=1  (创建1个新Pod，等Ready后删除1个旧Pod)
   步骤2: 旧RS=1, 新RS=2
   步骤3: 旧RS=0, 新RS=3  (完成)
```

1. **由maxSurge和maxUnavailable控制**

yaml

```yaml
   strategy:
     rollingUpdate:
       maxSurge: 1        # 最多多1个Pod
       maxUnavailable: 1  # 最多少1个Pod
```

------

## 验证删除策略

创建一些不健康的Pod观察删除顺序：

bash

```bash
# 创建5个Pod
kubectl create deployment test --image=nginx:alpine --replicas=5

# 模拟一个Pod失败
kubectl exec <pod-name> -- sh -c "exit 1"

# 立即缩容到2
kubectl scale deployment test --replicas=2

# 观察哪些Pod被删除
kubectl get pods -w
```

你会发现崩溃的Pod会优先被删除。

------

## 控制循环的统一性

所有场景都是同一个控制循环：

go

```go
func reconcile(rs ReplicaSet) {
    currentPods := getPods(rs.Spec.Selector)
    current := len(currentPods)
    desired := rs.Spec.Replicas
    
    switch {
    case current < desired:
        // 扩容场景
        createPods(desired - current)
    case current > desired:
        // 缩容场景
        podsToDelete := selectPodsToDelete(currentPods, current - desired)
        deletePods(podsToDelete)
    default:
        // 已达到期望状态
        return
    }
}
```

无论是手动scale、Pod删除、还是滚动更新，都是这个逻辑在工作。

你的理解完全正确 - 扩缩容就是相同的调谐机制，只是期望值变了，控制器会自动计算差值并采取行动。