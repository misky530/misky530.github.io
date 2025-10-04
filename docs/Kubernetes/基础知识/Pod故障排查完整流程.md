## Pod故障排查完整流程

模拟一个实际场景：

bash

```bash
# 创建一个会崩溃的Pod
cat > crashpod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: buggy-app
spec:
  containers:
  - name: app
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
    - |
      echo "App starting..."
      sleep 10
      echo "Simulating crash!"
      exit 1
EOF

kubectl apply -f crashpod.yaml
```

等待20秒后，Pod会崩溃。现在开始排查：

------

## 排查步骤

### 1. 快速查看状态

bash

```bash
# 查看Pod状态
kubectl get pods

# 输出可能是：
# NAME        READY   STATUS             RESTARTS   AGE
# buggy-app   0/1     CrashLoopBackOff   3          2m
```

**关键信息**：

- `STATUS`: 告诉你问题类型
- `RESTARTS`: 重启次数（说明持续失败）
- `READY`: 0/1表示容器未就绪

### 2. 查看详细信息

bash

```bash
kubectl describe pod buggy-app
```

**重点看这几个部分**：

```
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
  Started:      ...
  Finished:     ...

Events:
  Type     Reason     Age                  From               Message
  ----     ------     ----                 ----               -------
  Normal   Scheduled  3m                   default-scheduler  Successfully assigned...
  Normal   Pulling    3m                   kubelet            Pulling image "busybox"
  Normal   Pulled     3m                   kubelet            Successfully pulled image
  Normal   Created    2m (x4 over 3m)      kubelet            Created container app
  Normal   Started    2m (x4 over 3m)      kubelet            Started container app
  Warning  BackOff    1m (x6 over 2m)      kubelet            Back-off restarting failed container
```

**诊断**：

- `Exit Code: 1` - 应用异常退出
- `Events` 显示重启循环

### 3. 查看日志

bash

```bash
# 查看当前容器日志
kubectl logs buggy-app

# 查看上一次崩溃的日志（重要）
kubectl logs buggy-app --previous

# 如果有多个容器
kubectl logs buggy-app -c app
```

**输出**：

```
App starting...
Simulating crash!
```

找到了问题：应用在启动10秒后主动退出。

### 4. 进入容器调试（如果还在运行）

bash

```bash
# 进入容器
kubectl exec -it buggy-app -- sh

# 检查环境
env | grep APP_
ls -la /app
cat /etc/config/app.conf

# 手动运行启动命令
/app/start.sh
```

------

## 常见故障场景

### 场景1: ImagePullBackOff

bash

```bash
kubectl get pods
# NAME    READY   STATUS             RESTARTS   AGE
# app     0/1     ImagePullBackOff   0          5m
```

**排查**：

bash

```bash
kubectl describe pod app | grep -A 10 Events

# 看到：
# Failed to pull image "myapp:v999": rpc error: code = NotFound
```

**原因**：镜像不存在或无权限

**解决**：

bash

```bash
# 修复镜像名
kubectl set image deployment/app app=myapp:v1
```

### 场景2: CrashLoopBackOff

**常见原因**：

1. 应用启动失败（配置错误、依赖缺失）
2. 健康检查失败
3. 资源不足（OOMKilled）
4. 权限问题

**排查**：

bash

```bash
# 1. 查看退出码
kubectl describe pod app | grep "Exit Code"

# 常见退出码：
# 0: 正常退出
# 1: 通用错误
# 137: SIGKILL（通常是OOM）
# 139: SIGSEGV（段错误）

# 2. 检查OOM
kubectl describe pod app | grep -i oom
# 看到: Reason: OOMKilled

# 3. 查看资源使用
kubectl top pod app
```

**解决OOM**：

yaml

```yaml
resources:
  limits:
    memory: "512Mi"  # 增加内存限制
  requests:
    memory: "256Mi"
```

### 场景3: Pending（一直等待）

bash

```bash
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# app     0/1     Pending   0          5m
```

**排查**：

bash

```bash
kubectl describe pod app

# 看Events:
# Warning  FailedScheduling  2m   scheduler  0/3 nodes are available: 
#          insufficient cpu (3), insufficient memory (3)
```

**原因**：

- 资源不足
- 节点亲和性规则不满足
- 污点/容忍度不匹配

**解决**：

bash

```bash
# 检查节点资源
kubectl top nodes

# 降低资源请求
kubectl set resources deployment app --requests=cpu=100m,memory=128Mi
```

### 场景4: RunContainerError

bash

```bash
kubectl describe pod app | grep -A 5 "Last State"

# Last State:     Terminated
#   Reason:       StartError
#   Message:      failed to create containerd task: 
#                 OCI runtime create failed: permission denied
```

**常见原因**：

- Volume挂载权限问题
- SecurityContext配置错误
- Selinux/AppArmor限制

**排查**：

bash

```bash
# 检查挂载
kubectl get pod app -o yaml | grep -A 10 volumes

# 检查安全上下文
kubectl get pod app -o yaml | grep -A 10 securityContext
```

------

## 系统性排查工具

### 一键诊断脚本

bash

```bash
#!/bin/bash
POD=$1

echo "=== Pod状态 ==="
kubectl get pod $POD

echo -e "\n=== Pod详情 ==="
kubectl describe pod $POD

echo -e "\n=== 当前日志 ==="
kubectl logs $POD --tail=20

echo -e "\n=== 上次崩溃日志 ==="
kubectl logs $POD --previous --tail=20 2>/dev/null || echo "无历史日志"

echo -e "\n=== 资源使用 ==="
kubectl top pod $POD 2>/dev/null || echo "Metrics不可用"

echo -e "\n=== 所在节点 ==="
NODE=$(kubectl get pod $POD -o jsonpath='{.spec.nodeName}')
echo "节点: $NODE"
kubectl describe node $NODE | grep -A 5 "Allocated resources"
```

使用：

bash

```bash
chmod +x debug-pod.sh
./debug-pod.sh buggy-app
```

------

## 在K9s中排查

K9s提供了便捷的排查界面：

1. 输入 `:pod` 查看所有Pod
2. 选中问题Pod，按 `d` 查看describe
3. 按 `y` 查看完整YAML
4. 按 `l` 查看日志（虽然你的环境不可用，但命令行kubectl logs可以）
5. 按 `s` 进入Shell调试

红色的Pod就是有问题的。

------

## 排查顺序总结

```
1. kubectl get pods              → 看STATUS
2. kubectl describe pod          → 看Events和State
3. kubectl logs pod --previous   → 看崩溃时日志
4. kubectl top pod               → 看资源使用
5. kubectl exec -it pod -- sh    → 进容器调试
6. kubectl get events            → 看集群事件
```

**记住两个黄金原则**：

1. **日志是最好的朋友** - 90%的问题日志里有答案
2. **Events告诉你发生了什么** - describe的Events部分记录了完整的生命周期

现在试试创建那个崩溃的Pod，按照这个流程排查一遍，体验真实的故障诊断过程。