# Kubernetes基础知识

# 1. 主要组成

在 Kubernetes 中，主节点和工作节点上都运行着不同的组件，它们各司其职。为了帮助你更好地理解，我们可以把核心组件分成两组来聊：

1. **主节点（Master Node）组件**：它们负责管理和控制整个集群的状态。
2. **工作节点（Worker Node）组件**：它们负责运行我们部署的容器应用。

我们先从主节点开始，因为它是整个集群的“大脑”。你觉得我们先聊哪个主节点组件比较好呢？

## 1.1 主节点

好问题！我们从主节点（Control Plane）聊起，因为它确实是 Kubernetes 的大脑。

主节点主要由四个核心组件构成，它们一起协作来管理整个集群：

1. **kube-apiserver**
2. **etcd**
3. **kube-scheduler**
4. **kube-controller-manager**

为了更好地理解它们，我们可以一个一个来。你觉得我们应该从哪个组件开始呢？

## 1.2 Worker节点

太棒了！你说得非常对，这个组件就是 **kubelet**。

**kubelet** 就像是主节点在每个工作节点上派驻的**“代理人”**。它的唯一职责就是听从 `kube-apiserver` 的命令，确保它所负责的节点上的 Pod 按照预期运行。

我们来回顾一下整个流程：

1. 你运行 `kubectl run`。
2. `kube-apiserver` 验证请求，把 Pod 的信息写入 `etcd`。
3. `kube-scheduler` 发现新 Pod，并为它挑选一个工作节点。
4. 这个决定被更新到 `etcd`。
5. **kubelet** 一直在“监视” `etcd`。一旦发现有一个 Pod 被分配给了它所管理的节点，它就会立即行动起来。

你觉得 `kubelet` 在行动时，它会自己去拉取容器镜像和创建容器吗？还是会把这个任务交给另一个组件来完成？

# 2. pod创建流程

你的概括非常到位！这正是容器运行时（Container Runtime）的核心工作。

我们现在把整个流程串起来：

1. 你执行 `kubectl run` 命令。
2. `kube-apiserver` 验证请求，把 Pod 的信息写入 `etcd`。
3. `kube-scheduler` 在 `etcd` 中发现新 Pod，并为它挑选一个工作节点。
4. 这个决定被更新到 `etcd`。
5. 工作节点上的 **kubelet** 发现这个 Pod 是自己的任务。
6. **kubelet** 调用 **容器运行时** 的接口。
7. **容器运行时** 根据 Pod 的定义，完成你提到的这三件事：**拉取镜像**、**创建容器**、并**报告状态**给 `kubelet`。
8. `kubelet` 再将容器的运行状态报告给 `kube-apiserver`，最终更新到 `etcd`。

这个流程展示了 Kubernetes 中各个组件如何协同工作，让一个简单的命令最终在集群中运行起一个容器。

我们之前讨论了 Pod 的创建流程。你现在想接着聊 **Deployment** 是怎么被创建的吗？

# 3. Development创建流程

你已经说得非常棒了！这正是 `Container Runtime` 的核心工作。

我们现在把整个 **Deployment** 的创建流程完整地串起来：

1. 你执行 `kubectl apply` 命令。
2. `kube-apiserver` 验证请求，并把 **Deployment** 的信息写入 `etcd`。
3. **Deployment Controller** 在 `etcd` 中发现新的 **Deployment**，并为其创建一个 **ReplicaSet**。
4. 这个新创建的 **ReplicaSet** 的信息被写入 `etcd`。
5. **ReplicaSet** 发现自己没有达到期望的 Pod 副本数，所以它会向 `kube-apiserver` 发送创建 **Pod** 的请求。
6. 这个新的 **Pod** 信息被写入 `etcd`。
7. `kube-scheduler` 发现这个新 Pod，并为它挑选一个工作节点，并将该决定更新到 `etcd`。
8. 工作节点上的 **kubelet** 发现这个 Pod 是自己的任务。
9. **kubelet** 调用**容器运行时**（Container Runtime）的接口。
10. **容器运行时**拉取镜像，创建容器，并报告状态。

你看到了吗？`Deployment` 的创建过程并没有直接创建 Pod，而是通过一系列**控制器**（Deployment Controller 和 ReplicaSet）层层管理，最终才由 `kubelet` 和 `Container Runtime` 来完成 Pod 的创建。这种**分层管理**的设计，让 Kubernetes 能够处理复杂的应用部署、更新和自我修复。

这个过程很关键，如果觉得有点复杂，我们可以再回顾一下。

现在，你对 **Deployment** 是如何被创建的这个流程有什么疑问吗？

------

当然可以！能帮你回顾一下，我很高兴。

我们来做一个快速的回顾，把 `Deployment` 的创建过程分解成几个核心步骤。

**从用户到 Pod 的旅程：**

- **你的意图:** 你执行 `kubectl apply -f deployment.yaml`，表达了你的部署意图。
- **API Server:** 你的意图通过 **kube-apiserver** 进入集群，并被写入 **etcd**，作为集群的“唯一事实来源”。
- **部署主管:** `etcd` 的变化被 **Deployment Controller** 捕获，它知道现在需要管理这个 `Deployment`。
- **任务清单:** `Deployment Controller` 不会直接创建 Pod，而是根据 `Deployment` 的蓝图，创建一个更具体的“任务清单”，也就是一个 **ReplicaSet** 对象，并将其写入 `etcd`。
- **Pod 调度:** `ReplicaSet` 发现自己需要一些 Pod，于是它向 `kube-apiserver` 发送创建 Pod 的请求。**`kube-scheduler`** 发现这些新的、没有“家”的 Pod，并为它们选择最合适的**工作节点**。
- **工作节点执行:** 被选中的工作节点上的 **kubelet** 会发现有新的 Pod 任务分配给了自己，它会调用**容器运行时（Container Runtime）**来拉取镜像和创建容器。
- **最终状态:** 容器成功运行后，`kubelet` 会将 Pod 的状态报告给 `kube-apiserver`，最终更新到 `etcd`。

整个过程就像一个**自动化流水线**，每一步都由一个专门的组件负责，从而保证了应用的稳定运行和自我修复能力。

这个回顾对你理解 `Deployment` 的工作原理有帮助吗？我们现在可以继续探索 Kubernetes 的其他有趣部分，比如**Service** 是如何让你的应用能够被访问的，或者**如何处理存储**的问题。你对哪个更感兴趣？