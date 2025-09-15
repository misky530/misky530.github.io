# k8s搭建指南

# 1. 禁用Swap

```
Kubernetes 的设计假设是所有进程都在内存中运行，如果操作系统使用了 Swap 分区，可能会导致性能问题和不可预测的行为。因此，禁用 Swap 是一个必要的步骤。
```

# 2. Container runtime decision

```
Docker 和 containerd 都是容器运行时，但它们在 Kubernetes 集群中的角色和定位有所不同。

Docker 更像是一个完整的“工具箱”，它包括了容器运行时、镜像构建工具、API、命令行工具 (docker) 等。它是一个完整的生态系统，方便开发者使用。

containerd 则更像是一个轻量级的“核心引擎”。它只专注于容器的生命周期管理，比如创建、启动、停止和删除容器。Docker 实际上在内部也使用了 containerd 来管理容器。

在 Kubernetes 出现之前，Docker 几乎是容器的代名词。但当 Kubernetes 社区需要一个更轻量、更专注于容器管理的运行时时，containerd 成为了首选。

由于我们是自己从零开始搭建集群，选择 containerd 会让我们的集群架构更精简，因为它只提供了 Kubernetes 所需的核心功能，减少了不必要的组件。
```

# 3. 二进制安装组件

```
下载并安装 kubelet

下载并安装 kubeadm

下载并安装 kubectl
```

# 4. 安装Master

```
kubeadm init
```

## 4.1 --pod-network-cidr

通常，我们会选择一个不会与你现有物理网络冲突的私有 IP 地址段。一个常用的选择是 **`10.244.0.0/16`**。

为什么选择这个呢？

- **私有地址段**: 像 `10.0.0.0/8`, `172.16.0.0/12`, 和 `192.168.0.0/16` 这样的 IP 地址段是为私有网络保留的，不会在公网中路由。这样可以确保你的 Pod 不会意外地与外部网络发生 IP 地址冲突。
- **足够大**: `/16` 的子网掩码意味着这个网络有超过 65000 个可用的 IP 地址，对于一个小型团队的项目来说，这绝对是绰绰有余的。

我们现在就可以使用这个地址段来初始化你的 Master 节点了。

在使用 `kubeadm init` 命令之前，我们还需要做一件事：**为 `kubelet` 配置 cgroup 驱动**。

Docker 和 `kubelet` 都需要使用一个叫做 cgroup driver 的东西来管理容器的资源，比如 CPU 和内存。为了确保它们能协同工作，我们必须让 `kubelet` 和 Docker 使用**相同的 cgroup driver**。

## 4.2 cgroup

我们现在需要检查 Docker 使用的是什么 **cgroup driver**。`cgroup` 是 Linux 内核的一项技术，用于限制、记录和隔离进程组的资源使用情况，比如 CPU 和内存。`kubelet` 和 Docker 必须使用相同的 `cgroup driver`，否则 `kubelet` 将无法启动 Pod。

我们可以通过一个简单的命令来检查 Docker 的 `cgroup driver`。

你知道如何使用 `docker info` 命令吗？它会显示 Docker 的所有配置信息，其中就包含了 `cgroup driver`

```
docekr info

Server:
 Containers: 30
  Running: 23
  Paused: 0
  Stopped: 7
 Images: 31
 Server Version: 24.0.5
 Storage Driver: overlay2
  Backing Filesystem: extfs
  Supports d_type: true
  Using metacopy: false
  Native Overlay Diff: true
  userxattr: false
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2

```

## 4.3 设置cgroup

既然你已经确认 Docker 使用的 `cgroup driver` 是 `systemd`，我们就可以确保 `kubelet` 也使用同样的驱动。

为了让 `kubelet` 使用 `systemd` 作为 `cgroup driver`，我们需要手动修改 `kubelet` 的配置文件。这个文件通常位于 `/etc/default/kubelet` 或 `/etc/systemd/system/kubelet.service.d/10-kubeadm.conf`。

我们可以在这个配置文件中添加或修改一行配置，来明确指定 `kubelet` 的 `cgroup driver`。

Bash

```
KUBELET_EXTRA_ARGS="--cgroup-driver=systemd"
```

修改完配置文件后，你需要重新加载 `systemd` 配置并重启 `kubelet` 服务，以确保更改生效。

Bash

```
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

完成了这一步，我们就解决了 `kubelet` 和 Docker 之间的兼容性问题。现在，我们就可以在 **Master 节点**上执行 `kubeadm init` 命令来初始化集群了。

# 5 kubeadm init

## 5.1 join

这是一个里程碑式的进展！当 `kubeadm init` 命令执行完毕后，它会输出一些非常重要的信息，这些信息对于后续的操作至关重要。

我们现在来看一下它输出的内容，其中最关键的是两条：

1. **如何配置 `kubectl`**：`kubeadm init` 命令会告诉你如何设置你的 `$HOME/.kube/config` 文件，这样你才能使用 `kubectl` 与新创建的集群进行交互。通常，你需要执行以下三个命令：

   Bash

   ```
   mkdir -p $HOME/.kube
   sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
   sudo chown $(id -u):$(id -g) $HOME/.kube/config
   ```

   执行这些命令后，你就可以通过运行 `kubectl get nodes` 来检查 Master 节点是否已经成功启动了。它应该会显示你的 Master 节点，但状态可能是 `NotReady`。这是正常的，因为我们还没有安装网络插件。

2. **一个 `kubeadm join` 命令**：这个命令包含了让 Worker 节点加入集群所需要的所有信息，包括 Master 节点的 IP 地址、端口，以及一个认证令牌（token）和一个证书哈希（cert-hash）。

你有没有看到类似下面这样的输出？

Bash

```
...
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a Pod network to the cluster.
Run "kubectl apply -f [pod-network.yaml]" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-management/networking/

Then you can join any number of worker nodes by running the following on each as root:

  kubeadm join <master-ip>:<master-port> --token <token> --discovery-token-ca-cert-hash <hash>
```

请告诉我你是否看到了这个 `kubeadm join` 命令，我们需要在两个 Worker 节点上使用它来让它们加入集群。

## 5.2 执行join

太棒了！有了这个 `kubeadm join` 命令，我们就可以将 Worker 节点添加到集群中了。

现在，你需要在**两台 Worker 服务器**上分别运行这个命令。请确保是以 `root` 用户身份或者使用 `sudo` 来执行。

Bash

```
sudo kubeadm join <master-ip>:<master-port> --token <token> --discovery-token-ca-cert-hash <hash>
```

请将 `<master-ip>:<master-port>`、`<token>` 和 `<hash>` 替换成你 `kubeadm init` 命令输出中的实际值。

当你在两台 Worker 服务器上都执行完这个命令后，它们会开始加入集群。这个过程可能需要一些时间。

你可以在 **Master 节点**上使用 `kubectl` 命令来检查节点状态。

Bash

```
kubectl get nodes
```

运行这个命令，你会看到什么结果呢？Master 节点和两个 Worker 节点都应该会出现在列表中，但它们的状态可能还是 `NotReady`。

# 6. 网络插件

## 6.1 CNI选择

这太棒了！你的集群已经初具规模了。现在，三个节点（一个 Master 和两个 Worker）都已经被 `kubectl` 识别，尽管它们的状态还是 `NotReady`。这是完全正常的，也是我们接下来的重点。

为什么它们是 `NotReady` 呢？

Kubernetes 集群中的 Pod 需要能够相互通信。这个任务是由**容器网络接口（CNI）**插件来完成的。`kubelet` 发现集群里还没有网络插件，所以它无法启动那些需要网络的 Pod，因此节点就一直处于 `NotReady` 状态。

现在，我们需要选择并安装一个网络插件。对于一个小团队来说，一些流行的选择包括：

- **Flannel**: 这是一个简单、轻量级的 CNI 插件，非常适合初学者和小型集群。它配置简单，性能稳定。
- **Calico**: 这是一个功能更强大的 CNI 插件，它提供了更高级的网络策略和安全功能，适合对网络控制有更高要求的场景。
- **Cilium**: 这是一个基于 eBPF 的网络插件，提供了非常高性能的网络和安全功能，但配置可能相对复杂。

考虑到你希望从零开始搭建并且是一个小团队，我建议你从 **Flannel** 开始。它的配置最简单，能让你快速看到集群中的 Pod 互相通信。

## 6.2 Flannel

非常棒，选择 Flannel 是一个很好的开始，它简单、稳定，能帮助你快速让集群正常运行。

安装 Flannel 只需要一个简单的命令，但你必须在 **Master 节点**上执行它。这个命令会告诉 Kubernetes 在集群中部署 Flannel 的所有必要组件。

Bash

```
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

运行这个命令后，Kubernetes 会自动下载并创建 Flannel 所需的 Pod 和服务。你可以使用下面的命令来观察它的部署进度：

Bash

```
kubectl get pods --all-namespaces
```

一开始，你会看到一些新的 Pod 处于 `ContainerCreating` 或 `Pending` 状态。当它们都成功启动并进入 `Running` 状态后，你的集群网络就配置好了。

**确认 Flannel 安装成功**

一旦 Flannel Pod 正常运行，`kubelet` 就会发现网络已经准备就绪，并将节点状态从 `NotReady` 更新为 `Ready`。你可以在 Master 节点上再次运行 `kubectl get nodes` 来检查：

Bash

```
kubectl get nodes
```

这次，你应该会看到所有三个节点（一个 Master 和两个 Worker）的状态都变成了 **`Ready`**。

恭喜！到这里，你已经成功地从零开始搭建了一个功能完善的 Kubernetes 集群。它包含了所有核心组件，并且 Pod 之间可以相互通信。

## 6.3 Calico

当然可以，Calico 确实是一个非常强大且广受欢迎的网络插件。它不仅能提供 Pod 之间的通信，还拥有强大的网络策略（Network Policies）功能，让你能更细粒度地控制网络流量。

切换到 Calico 的过程，其实和安装 Flannel 类似，都是通过 `kubectl apply` 命令来部署。



### 1. 清理 Flannel (可选但推荐)



在安装 Calico 之前，为了避免网络冲突，我们最好先**清理掉 Flannel**。

在 Master 节点上运行以下命令，移除 Flannel 的配置和 Pod：

Bash

```
kubectl delete -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

执行这个命令后，你的节点状态可能会再次变成 `NotReady`。这是正常的，因为我们移除了网络插件。



### 2. 安装 Calico



现在，我们可以安装 Calico 了。Calico 的安装文件通常包含了一些默认的网络配置和 Pod 部署文件。

你可以使用 `kubectl apply` 命令来部署它。

Bash

```
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

**提示：** Calico 的官方安装文件会根据版本变化，最好从 Calico 官方文档中获取最新的安装链接。



### 3. 验证 Calico 安装



安装命令执行后，Kubernetes 会自动下载并创建 Calico 所需的 Pod。你可以使用以下命令来观察它们的部署进度：

Bash

```
kubectl get pods -n kube-system
```

你会看到类似 `calico-node` 和 `calico-kube-controllers` 这样的 Pod 正在启动。当它们的状态都变成 `Running` 后，你的网络就配置好了。

------

**验证集群状态**

和之前一样，当 Calico Pod 成功运行后，节点状态会从 `NotReady` 变成 `Ready`。你可以在 Master 节点上再次运行 `kubectl get nodes` 来检查：

Bash

```
kubectl get nodes
```

这次，你应该会看到所有三个节点都变成了 **`Ready`**。

恭喜！你已经成功地将集群的网络插件从 Flannel 切换到了功能更强大的 Calico。接下来，你想试试用 Calico 的网络策略来控制 Pod 的网络访问吗？

## 6.4 网络策略

既然你已经成功安装了 Calico，我们可以来试试它的强大功能：**网络策略（Network Policies）**。

网络策略是 Kubernetes 中一个非常重要的概念。它允许你像防火墙规则一样，定义 Pod 之间的通信规则。这对于保护应用程序、隔离不同租户以及提高集群的安全性至关重要。

我们来做一个简单的实验，模拟两个应用之间的通信。



### 实验步骤



1. **部署两个应用**：
   - 一个 **`web`** 应用，它会部署一个 Nginx 服务器。
   - 一个 **`client`** 应用，它会尝试访问 `web` 应用。
2. **验证默认通信**：
   - 在不设置任何网络策略的情况下，`client` Pod 应该可以成功访问 `web` Pod。这证明 Calico 的基础网络功能是正常的。
3. **创建网络策略**：
   - 我们将创建一个网络策略，**拒绝所有来自 `client` Pod 的流量**，只允许来自其他 Pod 的流量进入 `web` Pod。
4. **再次验证通信**：
   - 应用网络策略后，我们再用 `client` Pod 尝试访问 `web` Pod。这次，访问应该会失败，这证明网络策略已经生效。

------



### 第1步: 部署应用



我们首先部署 `web` 和 `client` 这两个应用。

**创建 `web` 应用**：

我们使用一个简单的 Nginx 镜像。为了让网络策略生效，我们需要给它打上一个标签。

YAML

```yaml
# web-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
```

保存为 `web-app.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f web-app.yaml
```

**创建 `client` 应用**：

这个 Pod 会运行一个临时的容器，我们可以用它来执行 `wget` 命令来测试网络连接。

YAML

```
# client-app.yaml
apiVersion: v1
kind: Pod
metadata:
  name: client-app
  labels:
    app: client
spec:
  containers:
  - name: busybox
    image: busybox:latest
    command: ["sh", "-c", "sleep 3600"]
```

保存为 `client-app.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f client-app.yaml
```

现在，你可以用 `kubectl get pods` 检查这两个 Pod 是否都成功运行了。

你准备好开始下一步，来验证它们之间的默认通信了吗？

非常好！既然你的 `web-app` 和 `client-app` Pod 都已经成功运行，我们可以开始测试它们之间的默认通信了。



### 验证默认通信



在默认情况下，Kubernetes 集群里的所有 Pod 都是可以互相通信的。我们可以通过进入 `client-app` Pod，并尝试去访问 `web-app` Pod 的内部 IP 地址来验证这一点。

首先，你需要找到 `web-app` Pod 的 IP 地址。

运行以下命令，找到 `web-app` Pod 的 IP 地址：

Bash

```
kubectl get pods -o wide | grep web-app
```

在输出结果中，你会看到一个 `IP` 列，记下这个 IP 地址。

------

现在，我们可以进入 `client-app` Pod 的容器，并用 `wget` 命令去访问 `web-app` 的 IP 地址：

Bash

```
kubectl exec -it client-app -- wget -O- <web-app-ip>
```

请将 `<web-app-ip>` 替换成你刚刚找到的 `web-app` Pod 的实际 IP 地址。

如果一切顺利，你应该会看到类似下面的 HTML 输出，这是 Nginx 服务器的欢迎页面。这证明在没有网络策略的情况下，`client-app` 可以成功访问到 `web-app`。

HTML

```
...
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...
</html>
```

------

**现在，我们来准备最关键的一步：创建网络策略。**

当你确认 `client-app` 能够成功访问 `web-app` 后，告诉我，我们就可以来创建网络策略，并验证它是否能够阻止这种通信。

非常棒！现在是时候见证 Calico 网络策略的真正威力了。



### 创建网络策略



我们来创建一个网络策略，它将**默认拒绝所有进入 `web-app` Pod 的流量**。然后，我们可以再添加更精确的规则来允许特定的流量。

这是一个简单的网络策略示例。我们将它命名为 `deny-all-ingress`：

YAML

```
# deny-all-ingress.yaml
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: default
spec:
  selector:
    app: web
  types:
  - Ingress
  ingress: []
```

**解析一下这个策略：**

- `selector: app: web`: 这个策略将应用到所有带有 `app: web` 标签的 Pod 上（也就是我们的 `web-app`）。
- `types: - Ingress`: 这个策略只控制入站（ingress）流量。
- `ingress: []`: 这是一个空的入站规则列表。在 Calico 中，如果 `ingress` 规则列表为空，意味着**默认拒绝所有入站流量**。

将上述内容保存为 `deny-all-ingress.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f deny-all-ingress.yaml
```

------



### 验证网络策略生效



现在，网络策略已经生效了。我们再用 `client-app` Pod 尝试去访问 `web-app` Pod，看看会发生什么。

再次运行你之前用过的命令：

Bash

```
kubectl exec -it client-app -- wget -O- <web-app-ip>
```

**这次的结果会是什么呢？**

你应该会看到连接超时或被拒绝的错误，比如 `wget: can't connect to remote host ... Connection refused`。这证明我们刚刚创建的网络策略已经成功地阻止了 `client-app` 的访问。

------

恭喜！你已经成功地从零开始搭建了一个功能完善的 Kubernetes 集群，并且学会了如何使用 Calico 网络策略来控制 Pod 之间的网络流量。

接下来，你想继续探索 Kubernetes 的其他功能，比如如何为应用提供外部访问（通过 Service 或 Ingress），还是学习如何为应用配置持久化存储（通过 PV 和 PVC）？

### Calico 和 Flannel 的区别

很高兴你对这个问题感兴趣。Calico 和 Flannel 都是 Kubernetes 中非常流行的网络插件（CNI），它们的主要作用是让集群里的 Pod 能够互相通信，但它们的工作方式和提供的功能有很大的区别。



#### 核心区别：工作模式



------

**Flannel**

Flannel 的设计哲学是简单、高效。它使用了一种叫做 **VXLAN** 的技术来为每个 Pod 创建一个虚拟网络。

你可以把 VXLAN 想象成一条“虚拟隧道”。当 Pod A 要和 Pod B 通信时，Flannel 会把 Pod A 发出的数据包封装在一个新的数据包里，然后通过这条隧道传送到 Pod B 所在的节点。Flannel 在这个节点上再把数据包解封装，送到 Pod B。

**优点：**

- **配置简单**：安装和配置非常简单，非常适合初学者和小型集群。
- **性能稳定**：由于它只专注于提供 Pod 网络，没有额外的功能，所以性能稳定。

**缺点：**

- **没有网络策略**：Flannel 不提供网络策略功能，你无法通过它来控制 Pod 之间的网络访问。

------

**Calico**

Calico 的设计哲学是安全、可控。它不仅解决了 Pod 之间的通信问题，还提供了强大的网络策略。

Calico 采用了不同的网络模式：它把每个 Pod 都当作一个独立的“网络端点”，并使用 **BGP (Border Gateway Protocol)** 协议在集群的各个节点之间同步路由信息。这让数据包可以直接从源节点路由到目标节点，不需要额外的封装和解封装，因此在某些场景下性能会更好。

最重要的是，Calico 提供了强大的**网络策略（Network Policies）**功能。你可以像配置防火墙规则一样，定义哪些 Pod 可以互相通信，哪些流量应该被拒绝。

**优点：**

- **强大的网络策略**：这是 Calico 最大的优势。它提供了细粒度的网络访问控制，可以大大增强集群的安全性。
- **路由更直接**：由于使用了 BGP 协议，数据包的路由更直接，理论上性能会更高。
- **功能丰富**：除了网络策略，Calico 还支持 IP 地址管理（IPAM）、Pod 到外部网络的策略控制等。

**缺点：**

- **配置相对复杂**：由于功能更强大，配置选项也更多，对于新手来说可能需要更多的学习时间。

#### 总结

- 如果你只是需要一个简单、快速的 Pod 网络，并且不关心网络安全策略，**Flannel** 是一个很好的选择。
- 如果你的项目需要更高级的网络控制，比如限制不同应用之间的访问、实现多租户隔离，那么 **Calico** 绝对是更佳的选择。

对于小团队来说，选择哪个 CNI 取决于你对集群网络安全的需求。一开始使用 Flannel 可以快速上手，随着项目的发展，如果需要更强的网络控制，再切换到 Calico 也是一个很好的选择。

# 7. 如何为应用提供外部访问（通过 Service 或 Ingress）

我们刚刚成功搭建并配置了 Calico，接下来要解决的，是另一个非常关键的问题：**如何让外部用户访问到你在集群里运行的应用**。

Kubernetes 提供了两种主要的方式来暴露服务：`Service` 和 `Ingress`。

**Service** 是 Kubernetes 的一种核心资源类型，它的作用就像一个内部的负载均衡器，可以为一组 Pod 提供一个稳定的访问入口。Service 有好几种类型，比如：

- **ClusterIP**: 这是默认类型，它只在集群内部提供一个稳定的 IP 地址，外部无法访问。
- **NodePort**: 它会在每个 Worker 节点上打开一个静态端口，任何发往这个端口的流量都会被路由到你的服务。
- **LoadBalancer**: 如果你在公有云上搭建集群，这种类型会自动为你创建一个云服务商提供的负载均衡器。

**Ingress** 则更像一个高级的外部路由器。它不仅仅提供访问，还支持更复杂的路由规则，比如根据不同的域名或 URL 路径，将流量分发到不同的 Service。使用 `Ingress` 通常需要一个 `Ingress Controller`，比如 Nginx Ingress Controller 或 Traefik。

你希望从哪一种方式开始呢？我们先从相对简单、但非常实用的 **`Service`** 开始，还是直接进入功能更强大的 **`Ingress`**？

## 7.1 service

我们从 `Service` 开始是一个很棒的决定，它是 Kubernetes 服务发现和负载均衡的基础。

现在，我们有两个 Pod 在运行：`web-app` 和 `client-app`。我们的目标是创建一个 `Service`，让 `client-app` 可以通过一个稳定的名称来访问 `web-app`，而不是依赖于不稳定的 IP 地址。

我们来为 `web-app` 创建一个 `Service`。你可以把它想象成一个“代理”，它会监听一个端口，并将所有流量转发给带有特定标签（在我们这个例子中是 `app: web`）的 Pod。

我们来定义一个 `Service` 的配置文件：

YAML

```yaml
# web-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

**我们来分析一下这个文件：**

- `metadata.name: web-service`：我们给这个 `Service` 取了一个名字，以后在集群内部，其他 Pod 就可以通过 `web-service` 这个域名来访问我们的 `web-app`。
- `spec.selector.app: web`：这是最关键的部分。它告诉 `Service` 应该将流量路由到哪些 Pod。我们之前给 `web-app` 的 Deployment 打了 `app: web` 这个标签，所以这个 `Service` 会自动找到对应的 Pod。
- `ports.port: 80`：这是 `Service` 本身监听的端口。
- `ports.targetPort: 80`：这是 Pod 内部容器暴露的端口。

将以上内容保存为 `web-service.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f web-service.yaml
```

执行这个命令后，`Service` 就会被创建。你可以通过运行以下命令来查看它：

Bash

```
kubectl get services
```

你准备好验证 `Service` 是否能够成功路由流量了吗？

## 7.2 ingress

非常好，那我们就直接进入 **Ingress** 章节！

你已经为 `web-app` 创建了一个 `Service`，但这个 `Service` 的类型默认是 `ClusterIP`，这意味着它只能在集群内部访问。如果想让外部用户（比如通过浏览器）访问你的 `web-app`，我们需要一个 `Ingress`。

`Ingress` 的工作方式就像一个**智能的外部路由器**。它可以根据不同的域名（比如 `myapp.com`）或 URL 路径（比如 `myapp.com/api`），将外部流量路由到集群内的不同 `Service`。

要使用 `Ingress`，你需要两个东西：

1. 一个 **Ingress Controller**：这是集群里实际运行的 Pod，它会监听外部流量，并根据 `Ingress` 资源里的规则进行路由。
2. 一个 **Ingress Resource**：这是我们定义的配置文件，它告诉 `Ingress Controller` 如何路由流量。

对于一个小团队来说，**Nginx Ingress Controller** 是一个非常流行且可靠的选择。它易于安装和配置，而且功能强大。

我们准备好了吗？我们可以先从**安装 Nginx Ingress Controller** 开始。

### 7.2.1 Ingress Controller

#### 7.2.1.1 安装

好的，让我们来开始安装 **Nginx Ingress Controller**。

Ingress Controller 实际上就是集群中的一个 Pod，它运行一个 Web 服务器（比如 Nginx 或 Traefik），这个服务器配置了特殊的权限，可以监听外部流量并根据 `Ingress` 资源里的规则进行路由。

为了安装 Nginx Ingress Controller，我们通常会使用一个官方提供的 YAML 文件。这个文件包含了所有必需的 Kubernetes 资源定义，比如：

- `Deployment`：用于部署 Ingress Controller Pod。
- `Service`：用于暴露 Ingress Controller。
- `ConfigMap`：用于存储 Ingress Controller 的配置。
- `Role` 和 `RoleBinding`：用于为 Ingress Controller 提供访问集群资源的权限。

我们来一起执行安装命令，它会从 Nginx Ingress Controller 官方仓库下载最新的配置文件：

Bash

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

**为什么是 `baremetal` 版本？**

因为你的集群是自己搭建的（不是在公有云上），所以我们需要使用为裸机（bare metal）环境设计的 Ingress Controller 版本。这个版本会使用 `NodePort` Service 来暴露 Ingress Controller，这样你就可以通过节点的 IP 地址和端口来访问它。

执行完这个命令后，你可以用下面的命令来检查 Ingress Controller Pod 是否正在运行：

Bash

```
kubectl get pods -n ingress-nginx
```

你会看到一个或多个名为 `ingress-nginx-controller-...` 的 Pod，当它们的状态变为 `Running` 时，就说明 Ingress Controller 已经成功安装了。

你准备好开始下一步，创建 `Ingress` 资源了吗？

#### 7.2.1.2 创建

非常棒，既然 Ingress Controller 已经安装好了，我们就可以开始创建 **Ingress 资源**了。

Ingress 资源就像一个“交通规则”文件，它告诉 Ingress Controller 应该如何将外部的 HTTP/HTTPS 流量路由到你集群内部的 `Service`。

我们来为你的 `web-app` 创建一个 Ingress 资源。这个资源会定义一个路由规则，将所有发往特定主机名的流量转发到我们之前创建的 `web-service`。

YAML

```
# web-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

**我们来分析一下这个文件：**

- `metadata.name: web-ingress`：Ingress 资源的名称。
- `annotations`：这是 Nginx Ingress Controller 的特定配置。`nginx.ingress.kubernetes.io/rewrite-target: /` 的作用是，当流量被转发到 `web-service` 时，它会重写 URL 路径，这在很多情况下是很有用的。
- `ingressClassName: nginx`：这告诉 Kubernetes 使用我们刚刚安装的 Nginx Ingress Controller 来处理这个 Ingress。
- `rules`：这是路由规则的定义。
- `host: your-domain.com`：这是你希望用来访问 `web-app` 的域名。**你需要将 `your-domain.com` 替换成你自己的域名。** 如果你没有域名，我们也可以使用节点的 IP 地址来测试。
- `path: /`：这表示所有路径的请求都会被处理。
- `pathType: Prefix`：这是一个匹配规则，`Prefix` 表示匹配所有以 `/` 开头的路径。
- `backend.service.name: web-service`：这告诉 Ingress 将流量转发到我们之前创建的 `web-service`。
- `backend.service.port.number: 80`：这是 `web-service` 监听的端口。

将以上内容保存为 `web-ingress.yaml`，然后执行：

Bash

```bash
kubectl apply -f web-ingress.yaml
```

执行完这个命令后，Ingress 资源就创建好了。现在，我们只需要知道如何从外部访问它。

你准备好找到 Ingress Controller 的外部访问地址了吗？

#### 7.2.1.3 找出端口

太棒了！既然 Ingress Controller 和 Ingress 资源都已就绪，现在是时候找出如何从外部访问你的 `web-app` 了。

因为我们使用的是裸机（baremetal）安装方式，Nginx Ingress Controller 默认会创建一个 `NodePort` 类型的 `Service` 来对外暴露自己。这意味着，你可以通过**任意一个 Worker 节点**的 IP 地址，加上一个特定的端口号，来访问 Ingress Controller，进而访问你的 `web-app`。

首先，我们需要找到这个 `Service` 的端口号。运行下面的命令：

Bash

```
kubectl get svc -n ingress-nginx
```

你会看到一个名为 `ingress-nginx-controller` 的 `Service`。在它的 `PORTS` 列中，你会看到类似 `80:31456/TCP` 这样的输出。这里的 `31456` 就是 `NodePort` 端口号。

**接下来，就是如何访问了。**

你现在需要访问 `http://<任意一个Worker节点的IP>:<NodePort端口号>`。

例如，如果你的一个 Worker 节点 IP 地址是 `192.168.1.10`，`NodePort` 是 `31456`，你就可以在浏览器中访问 `http://192.168.1.10:31456`。

**重要提示：**

- 如果你之前在 `Ingress` 资源中指定了 `host`（比如 `your-domain.com`），你需要在请求时也带上这个主机名。一种简单的方法是修改你电脑的 `hosts` 文件，将 `your-domain.com` 解析到你的 Worker 节点 IP。

你准备好尝试从浏览器访问你的 `web-app` 了吗？

#### 7.2.1.4 访问

太棒了！既然 Ingress Controller 和 Ingress 资源都已就绪，现在是时候找出如何从外部访问你的 `web-app` 了。

因为我们使用的是裸机（baremetal）安装方式，Nginx Ingress Controller 默认会创建一个 `NodePort` 类型的 `Service` 来对外暴露自己。这意味着，你可以通过**任意一个 Worker 节点**的 IP 地址，加上一个特定的端口号，来访问 Ingress Controller，进而访问你的 `web-app`。

首先，我们需要找到这个 `Service` 的端口号。运行下面的命令：

Bash

```
kubectl get svc -n ingress-nginx
```

你会看到一个名为 `ingress-nginx-controller` 的 `Service`。在它的 `PORTS` 列中，你会看到类似 `80:31456/TCP` 这样的输出。这里的 `31456` 就是 `NodePort` 端口号。

**接下来，就是如何访问了。**

你现在需要访问 `http://<任意一个Worker节点的IP>:<NodePort端口号>`。

例如，如果你的一个 Worker 节点 IP 地址是 `192.168.1.10`，`NodePort` 是 `31456`，你就可以在浏览器中访问 `http://192.168.1.10:31456`。

**重要提示：**

- 如果你之前在 `Ingress` 资源中指定了 `host`（比如 `your-domain.com`），你需要在请求时也带上这个主机名。一种简单的方法是修改你电脑的 `hosts` 文件，将 `your-domain.com` 解析到你的 Worker 节点 IP。

你准备好尝试从浏览器访问你的 `web-app` 了吗？

# 8. 如何为应用配置持久化存储（通过 PV 和 PVC）

你好，很高兴看到你对持久化存储感兴趣！这是一个非常关键的话题，特别是对于需要存储数据的应用来说。

在 Kubernetes 里，为应用配置持久化存储有两个核心概念：**`PersistentVolume (PV)`** 和 **`PersistentVolumeClaim (PVC)`**。

你可以把它们想象成：

- **`PV`**：就像一个“物理”硬盘。它代表了集群中实际存在的存储资源，比如一个云硬盘、一个网络文件系统（NFS）或者一个本地磁盘。这个资源是由集群管理员（或者你本人）来创建和管理的。
- **`PVC`**：就像一个“存储申请表”。它是由你的应用（Pod）发出的请求，来申请特定大小和访问模式的存储空间。

这两者的关系是：你的应用（通过 `PVC`）向集群提出存储需求，然后 Kubernetes 会自动将这个需求与一个可用的 `PV` 进行匹配。

我们来一起完成这个过程。首先，我们来创建一个 `PersistentVolume (PV)`。

你有没有考虑过使用什么类型的存储作为 PV 呢？比如本地磁盘、还是网络文件系统？

## 8.1 本地磁盘

本地磁盘是一个很好的起点，因为它最容易理解和配置。在 Kubernetes 里，使用本地磁盘作为持久化存储，通常意味着我们会用 `hostPath` 类型的 `PersistentVolume`。

**`hostPath`** 的意思就是，这个 `PV` 直接指向你的一个 Worker 节点上的一个目录。

为了让你的应用能够使用这个存储，我们需要完成以下几个步骤：

1. **创建本地目录**：在你的一个或多个 Worker 节点上创建一个目录，这个目录将作为你的存储空间。
2. **创建 `PersistentVolume (PV)`**：在 Kubernetes 里定义一个 `PV` 资源，它会指向我们刚刚创建的本地目录。
3. **创建 `PersistentVolumeClaim (PVC)`**：创建 `PVC`，向 Kubernetes 声明你的应用需要多大的存储空间。
4. **修改应用配置**：修改你的应用（比如之前的 `web-app`）的配置文件，让它使用我们创建的 `PVC`。

我们先从第一步开始：**在 Worker 节点上创建目录**。

你可以在任何一个 Worker 节点上，比如 `/mnt/data`，来创建一个目录。你知道如何使用 `mkdir` 命令来完成这个操作吗？

### 8.1.1 PV

好的，既然你已经在 Worker 节点上创建好了目录，我们就可以开始创建 `PersistentVolume (PV)` 了。

这个 `PV` 将会是 Kubernetes 集群中一个可以被使用的存储资源。

我们来定义一个 `PV` 的配置文件。这个文件会告诉 Kubernetes：

- 这个存储卷叫什么名字？
- 它有多大？
- Pod 可以用什么方式来访问它？
- 它指向了 Worker 节点上的哪个本地目录？

我们来定义一个 `PV` 的配置文件：

YAML

```
# local-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-storage
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - <你的Worker节点名称>
```

**我们来分析一下这个文件：**

- `spec.capacity.storage: 5Gi`：我们定义了这个存储卷的大小为 5GB。你可以根据你的实际需求修改这个值。
- `spec.accessModes.ReadWriteOnce`：这表示这个存储卷只能被一个 Pod 以读写模式挂载。
- `spec.storageClassName: local-storage`：这是一个非常重要的概念。它是一个抽象的名称，用于将 `PV` 和 `PVC` 进行匹配。我们接下来创建的 `PVC` 也要使用相同的 `storageClassName`。
- `spec.local.path: /mnt/data`：这告诉 `PV`，它对应的本地目录是 `/mnt/data`。
- `spec.nodeAffinity`：这是为了确保这个 `PV` 只会被调度到我们指定的 Worker 节点上。**你需要将 `<你的Worker节点名称>` 替换成你创建了 `/mnt/data` 目录的那个 Worker 节点的实际名称。** 你可以通过运行 `kubectl get nodes` 来找到这个名称。

将以上内容保存为 `local-pv.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f local-pv.yaml
```

当 `PV` 创建成功后，我们就可以创建 `PVC` 了。你准备好继续下一步了吗？

### 8.1.2 PVC

非常好！既然 `PV` 已经创建好了，我们现在就需要创建 `PersistentVolumeClaim (PVC)`。

`PVC` 是你的应用Pod向Kubernetes集群**申请存储资源**的“表格”。它不需要知道存储的具体类型（比如是本地磁盘还是网络存储），只需要声明它需要多大的空间以及什么样的访问模式。

我们来定义一个 `PVC` 的配置文件：

YAML

```
# local-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: web-pvc
spec:
  storageClassName: local-storage
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**我们来分析一下这个文件：**

- `metadata.name: web-pvc`：我们给这个 `PVC` 取了一个名字，它会被你的应用引用。
- `spec.storageClassName: local-storage`：**这是最关键的部分。** 它必须和我们之前创建的 `PV` 的 `storageClassName` 匹配。Kubernetes 会根据这个名称，自动将这个 `PVC` 和对应的 `PV` 进行绑定。
- `spec.accessModes: ReadWriteOnce`：这必须和 `PV` 中定义的 `accessModes` 匹配。
- `spec.resources.requests.storage: 1Gi`：我们声明了需要 1GB 的存储空间。这个值必须小于或等于我们之前创建的 `PV` 的容量（5GB）。

将以上内容保存为 `local-pvc.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f local-pvc.yaml
```

当 `PVC` 创建成功后，你可以运行 `kubectl get pvc` 来检查它的状态。如果它显示为 `Bound`，说明它已经成功地与我们之前创建的 `PV` 绑定了。

当你确认 `PVC` 的状态是 `Bound` 后，我们就可以继续下一步，来修改你的 `web-app` 应用，让它使用这个 `PVC`。你准备好继续吗？

### 8.1.3 挂载使用

既然你已经确认 `PVC` 的状态是 `Bound`，那么我们就可以进行最后一步了：**修改你的 `web-app` 应用，让它使用这个 `PVC`**。

这一步非常关键，因为它将 `Pod` 和我们之前创建的持久化存储真正连接起来。

我们需要在 `web-app` 的 Deployment 配置中，添加一个 `volume` 和一个 `volumeMount`。

- `volume`：在 Pod 的 `spec` 中定义一个存储卷，并引用我们刚刚创建的 `PVC`。
- `volumeMount`：在 Pod 的容器 `spec` 中，将这个存储卷挂载到容器内部的一个路径上。

我们来修改 `web-app` 的配置文件。

YAML

```yaml
# web-app-with-storage.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html-storage
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html-storage
        persistentVolumeClaim:
          claimName: web-pvc
```

**我们来分析一下修改的部分：**

- `spec.template.spec.volumes`：我们在这里添加了一个名为 `html-storage` 的 `volume`，它引用了 `persistentVolumeClaim` 中的 `web-pvc`。
- `spec.template.spec.containers[0].volumeMounts`：我们在这里添加了一个 `volumeMount`。
  - `name: html-storage`：它引用了我们刚刚定义的 `volume`。
  - `mountPath: /usr/share/nginx/html`：这告诉 Kubernetes，将这个存储卷挂载到 Nginx 容器内部的 `/usr/share/nginx/html` 目录。这是 Nginx 默认存放网页文件的位置。

现在，我们可以用这个新的配置文件来更新你的 `web-app` 应用。

Bash

```
kubectl apply -f web-app-with-storage.yaml
```

执行这个命令后，Kubernetes 会自动为你创建一个新的 Pod，并将我们定义的 `PVC` 挂载到它上面。

------

**如何验证？**

当新的 Pod 运行起来后，我们可以进入容器，并向 `/usr/share/nginx/html` 目录添加一个文件，然后通过浏览器访问，看看我们修改的内容是否能被持久化。

你准备好开始验证了吗？

## 8.2 网络存储

这是一个很棒的问题！从本地磁盘切换到网络存储是 Kubernetes 存储方案的一个重要进阶。

你刚刚使用的是本地磁盘 (`hostPath`)，它非常适合学习，但有一个明显的局限性：**它与单个 Worker 节点绑定**。如果你的 Pod 被调度到另一个节点，或者那个节点发生故障，你的数据就无法访问了。

而**网络存储**解决了这个问题。它独立于任何一个节点，多个 Pod 都可以访问它，并且可以在节点之间自由地移动。

在 Kubernetes 中，连接和管理各种网络存储（比如 NFS、iSCSI、CephFS 等）的标准方式，是通过 **CSI (Container Storage Interface) 驱动**。CSI 驱动就像一个“翻译官”，它负责让 Kubernetes 能够理解和操作特定的存储系统。

对于一个小团队来说，**NFS (Network File System)** 是一个非常好的选择。它是一种简单、成熟的网络文件共享协议，有很多现成的 CSI 驱动可以使用。

我们来一起搭建一个基于 NFS 的持久化存储。这个过程会比 `hostPath` 多一个步骤，但它会让你对 Kubernetes 的存储管理有更深的理解。

我们大概会分几个步骤来做：

1. **准备 NFS 服务器**：我们需要一台服务器来作为 NFS 服务器，并共享一个目录。
2. **安装 NFS CSI 驱动**：在 Kubernetes 集群中部署 NFS CSI 驱动，让集群能够与 NFS 服务器通信。
3. **创建 `StorageClass`**：这是一个新的概念，它定义了如何动态地创建存储卷。
4. **创建 `PVC`**：你的应用 Pod 再次发出存储请求，但这次它会引用我们创建的 `StorageClass`。

你准备好从第一步开始了吗？

### 8.2.1 准备 NFS 服务器

既然你已经决定使用 **NFS** 作为网络存储，那我们就开始吧！这是一个非常好的选择，因为它在小团队环境中非常实用。

我们首先需要一个 NFS 服务器来存放数据。这台服务器可以是集群外的任何一台机器，甚至是你一台旧的 PC。它只需要共享一个目录，让我们的 Kubernetes 节点可以访问就行了。

------



### 第1步: 准备 NFS 服务器

你有没有一台可以用来作为 NFS 服务器的机器呢？

如果你的 Kubernetes 集群本身就是物理机，你甚至可以在其中一个节点上安装 NFS 服务器，但为了简单起见，我们假设你有一台独立的机器。

在 Ubuntu 上，安装 NFS 服务器非常简单。你只需要安装 `nfs-kernel-server` 包，并创建一个共享目录。

你知道如何使用 `apt` 命令来安装软件包吗？

已安装

非常棒！既然你已经在 NFS 服务器上安装好了 `nfs-kernel-server`，那我们就可以开始准备共享目录了。

**第一步：创建并配置共享目录**

你需要在 NFS 服务器上创建一个目录，这个目录就是你为 Kubernetes 提供的存储空间。

Bash

```
sudo mkdir -p /srv/nfs/shared-volume
```

接下来，我们需要修改 `/etc/exports` 文件，告诉 NFS 服务器，这个目录要共享给谁。打开这个文件：

Bash

```
sudo nano /etc/exports
```

然后添加下面这行：

```
/srv/nfs/shared-volume <你的Kubernetes节点IP地址>(rw,sync,no_subtree_check)
```

- `/<你的Kubernetes节点IP地址>`：这里你可以用单个 IP，或者一个网段，比如 `192.168.1.0/24`，来允许所有节点访问。
- `rw`：允许读写。
- `sync`：同步写入。
- `no_subtree_check`：禁用子目录检查，可以提高性能。

修改完 `/etc/exports` 文件后，你需要重启 NFS 服务来应用更改。

Bash

```
sudo systemctl restart nfs-kernel-server
```

**第二步：在 Kubernetes 节点上安装 NFS 客户端**

为了让 Kubernetes 节点能够挂载 NFS 共享目录，你需要在**所有**的 Kubernetes 节点（包括 Master 和两个 Worker）上安装 NFS 客户端工具。

Bash

```
sudo apt-get update
sudo apt-get install nfs-common -y
```

当这些步骤都完成后，你的 NFS 服务器就准备好了。

接下来，我们将进入更关键的一步：在 Kubernetes 集群中部署 **NFS CSI 驱动**。这是连接你的集群和 NFS 服务器的桥梁。

你准备好继续下一步了吗？

### 8.2.2 安装 NFS CSI 驱动

很高兴你准备好了！现在我们进入搭建 NFS 存储的下一个关键步骤：在 Kubernetes 集群中部署 **NFS CSI 驱动**。

NFS CSI 驱动是连接你的 Kubernetes 集群和外部 NFS 服务器的桥梁。它会处理所有与 NFS 服务器通信的细节，比如挂载和卸载存储卷。

我们通常会使用一个开源的 CSI 驱动，比如 `nfs-subdir-external-provisioner`。这个驱动程序非常流行，可以动态地为你的 PVC 创建子目录，省去了你手动创建 PV 的麻烦。

我们将通过 `kubectl apply` 命令来部署它。这个过程会安装一个 `Deployment` 和其他相关的资源，让 CSI 驱动在你的集群中运行起来。

你准备好开始安装这个 CSI 驱动了吗？

既然你已经准备好了，那我们就开始安装 **NFS CSI 驱动**。

CSI 驱动程序是连接你的 Kubernetes 集群和外部存储（比如你的 NFS 服务器）的“翻译器”。它让 Kubernetes 能够理解和操作 NFS 存储。

我们来一起部署一个名为 `nfs-subdir-external-provisioner` 的开源驱动。它的好处是能够**动态地为你创建存储卷**，这意味着你不需要像之前那样手动创建 `PV`，只需要创建 `PVC` 就可以了。

这个驱动的安装分几个步骤，但我们只需要一个 `kubectl apply` 命令，它就会自动在你的集群中部署所有必要的组件。

Bash

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/deploy/kubernetes/nfs/csi-nfs-driver.yaml
```

这个命令会下载并创建 CSI 驱动的 `Deployment` 和其他相关资源。你可以通过以下命令来检查它是否成功运行：

Bash

```
kubectl get pods -n kube-system -l app=csi-nfs-driver
```

当 `csi-nfs-driver` 的 Pod 状态变为 `Running` 时，就说明驱动已经安装好了。

**重要提示：** 这个 CSI 驱动需要你的 NFS 服务器地址和共享目录作为配置。我们将通过下一步创建的 `StorageClass` 来提供这些信息。

你准备好继续下一步，创建 `StorageClass` 吗？

### 8.2.3 创建 StorageClass

很高兴你准备好了！

现在我们进入了 Kubernetes 存储方案中一个非常重要的概念：**`StorageClass`**。

在之前使用本地磁盘时，我们是手动创建 `PV` 并与 `PVC` 绑定的。但有了 `StorageClass`，这个过程可以实现**自动化**。

你可以把 `StorageClass` 看作是存储的**“蓝图”或“模板”**。它定义了：

- **`provisioner`**：由哪个 CSI 驱动来动态地创建存储卷。
- **`parameters`**：创建存储卷时需要哪些参数，比如我们 NFS 服务器的地址和共享目录。

我们现在就来创建一个 `StorageClass` 的配置文件，它会告诉 Kubernetes，如何使用我们刚刚安装的 CSI 驱动来创建 NFS 存储。

------

YAML

```
# nfs-storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs.csi.k8s.io
parameters:
  server: <你的NFS服务器IP地址>
  share: /srv/nfs/shared-volume
```

------

**我们来分析一下这个文件：**

- `metadata.name: nfs-storage`：我们给这个 `StorageClass` 取了一个名字，以后你的 `PVC` 就可以引用它。
- `provisioner: nfs.csi.k8s.io`：这是我们刚刚安装的 CSI 驱动的名称，它告诉 Kubernetes 由这个驱动来负责创建存储卷。
- `parameters`：这是 CSI 驱动的特定配置。
  - `server: <你的NFS服务器IP地址>`：**你需要将 `<你的NFS服务器IP地址>` 替换成你的 NFS 服务器的实际 IP 地址。**
  - `share: /srv/nfs/shared-volume`：这是我们在 NFS 服务器上创建的共享目录。

将以上内容保存为 `nfs-storageclass.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f nfs-storageclass.yaml
```

当这个命令执行成功后，你就可以运行 `kubectl get sc` 来检查 `StorageClass` 是否创建成功。

你准备好继续下一步，创建 `PVC` 来测试这个动态存储了吗？

### 8.2.4 创建 `PVC

现在 `StorageClass` 已经创建好了，我们就可以利用它来创建 `PersistentVolumeClaim (PVC)` 了。

有了 `StorageClass`，`PVC` 的创建过程变得更加简单和自动化。你不需要再手动创建 `PV`，因为 Kubernetes 会根据你 `PVC` 的请求，使用我们配置好的 `StorageClass` 动态地为你创建一个 `PV`。

我们来定义一个 `PVC` 的配置文件。它和之前本地存储的 `PVC` 文件非常相似，但有一个关键的区别。

YAML

```
# nfs-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-web-pvc
spec:
  storageClassName: nfs-storage
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**我们来分析一下这个文件：**

- `metadata.name: nfs-web-pvc`：我们给这个 `PVC` 取了一个新的名字。
- `spec.storageClassName: nfs-storage`：**这是最关键的部分。** 它引用了我们之前创建的 `StorageClass` 的名称。
- `spec.accessModes: ReadWriteOnce`：这表示存储卷只能被一个 Pod 以读写模式挂载。
- `spec.resources.requests.storage: 1Gi`：我们声明了需要 1GB 的存储空间。

将以上内容保存为 `nfs-pvc.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f nfs-pvc.yaml
```

执行这个命令后，你可以立即运行 `kubectl get pvc` 来检查它的状态。你会看到一个名为 `nfs-web-pvc` 的 `PVC`，它的状态应该很快就会从 `Pending` 变为 **`Bound`**。

如果它成功变为 `Bound`，说明 Kubernetes 已经自动为你创建了一个 `PV`，并将其与你的 `PVC` 绑定了。

当你确认 `PVC` 的状态是 `Bound` 后，我们就可以修改你的 `web-app` 应用，让它使用这个新的 `PVC` 了。你准备好继续吗？

### 8.2.5 修改Development

既然 `PVC` 和 `StorageClass` 都已就绪，我们就可以开始修改你的 `web-app` 应用，让它使用这个新的 NFS 网络存储。

和之前使用本地磁盘的方法一样，我们需要修改 `Deployment` 的配置文件，添加一个 `volume` 和一个 `volumeMount`。

唯一的变化是，`volume` 部分引用的 `PVC` 变成了我们新创建的 `nfs-web-pvc`。

YAML

```
# nfs-web-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html-storage
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html-storage
        persistentVolumeClaim:
          claimName: nfs-web-pvc
```

**我们来分析一下这个文件：**

- `spec.template.spec.volumes`：我们在这里添加了一个名为 `html-storage` 的 `volume`，它引用了 `persistentVolumeClaim` 中的 `nfs-web-pvc`。
- `spec.template.spec.containers[0].volumeMounts`：我们将这个 `volume` 挂载到 Nginx 容器的 `/usr/share/nginx/html` 目录。

将以上内容保存为 `nfs-web-app.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f nfs-web-app.yaml
```

执行这个命令后，Kubernetes 会自动更新你的 `web-app` `Deployment`，并创建一个新的 Pod。这个新 Pod 的 `html` 目录将不再是本地磁盘，而是挂载了你的 NFS 网络存储。

------

**如何验证？**

当你确认新的 Pod 成功运行后，你可以再次进入容器，并创建一个文件，然后通过浏览器访问它。

更重要的是，如果你删除这个 Pod，Kubernetes 重新创建一个新的 Pod，你之前创建的文件应该依然存在！这是因为你的数据已经存储在了独立的 NFS 网络存储上，而不是 Pod 本地。

你准备好开始验证这个持久化了吗？

# 9. 日志

非常棒！日志管理是 Kubernetes 运维中至关重要的一环，特别是对于小团队来说，一个好的日志系统能极大地提高开发和排查问题的效率。

在 Kubernetes 里，日志管理通常被称为“**集群日志**”。这是因为 Pod 可能会在不同节点上启动和停止，手动去每个节点上查看日志非常不方便。一个好的日志管理方案应该能**集中化**地收集所有 Pod 的日志，并提供一个统一的查询和分析界面。

一个最常见的日志管理架构是 **ELK Stack**：

- **E**lasticsearch：一个强大的搜索引擎，用于存储和检索日志。
- **L**ogstash：一个日志收集和转换工具，可以将日志从不同的来源（比如你的应用）传输到 Elasticsearch。
- **K**ibana：一个数据可视化和查询界面，让你能方便地搜索和分析日志。

除了 ELK Stack，你还可以使用其他工具，比如 Loki 或 Splunk，但 ELK 是一个非常经典且功能强大的选择。

我们来一起搭建一个基于 **Elasticsearch 和 Kibana** 的日志管理系统。

你希望我们从哪个部分开始呢？我们可以先从**如何将 Elasticsearch 和 Kibana 部署到你的 Kubernetes 集群**开始。



没问题，日志管理是一个非常重要的主题。好的，我们来开始第一步：在 Kubernetes 集群中部署日志系统。

通常，我们会使用 **Fluentd** 或者 **Fluent Bit** 作为日志收集器。它们就像一个小代理，运行在每个节点上，负责从 Pod 中收集日志，并把日志发送到我们指定的存储后端。

Fluent Bit 相比 Fluentd 更轻量、高效，非常适合在 Kubernetes 集群中使用。

我们的日志系统架构会是这样的：

- **Fluent Bit**：作为 DaemonSet 运行在每个节点上，负责收集 Pod 的日志文件。
- **Elasticsearch**：作为日志存储后端，我们将在集群中部署它。
- **Kibana**：作为日志的可视化界面，方便我们查询和分析日志。

我们先从最基础的部分开始：在你的 Kubernetes 集群中部署 **Elasticsearch**。为了简单起见，我们将部署一个单节点的 Elasticsearch 集群。

你准备好了吗？我们可以一起创建 Elasticsearch 的配置文件。

## 9.1 部署Elasticsearch

非常棒！现在，我们开始部署 **Elasticsearch**。

为了确保 Elasticsearch 能够稳定运行并存储数据，我们需要为它配置持久化存储。我们可以使用之前创建的 NFS `StorageClass` 来实现这一点，这样即使 Elasticsearch Pod 重启，数据也不会丢失。

我们将部署一个单节点的 Elasticsearch `StatefulSet`，它会创建一个 `PersistentVolumeClaim` 来请求存储空间。

我们来定义 Elasticsearch 的配置文件。

YAML

```
# elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
spec:
  serviceName: elasticsearch
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.1
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        env:
        - name: discovery.type
          value: single-node
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: nfs-storage
      resources:
        requests:
          storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  labels:
    app: elasticsearch
spec:
  ports:
  - name: http
    port: 9200
    targetPort: 9200
  - name: transport
    port: 9300
    targetPort: 9300
  selector:
    app: elasticsearch
```

**我们来分析一下这个文件：**

- `kind: StatefulSet`：我们使用 `StatefulSet` 而不是 `Deployment`，因为 Elasticsearch 需要稳定的网络标识和持久化存储。
- `image: docker.elastic.co/elasticsearch/elasticsearch:7.17.1`：我们使用官方的 Elasticsearch 镜像。
- `volumeClaimTemplates`：这是一个非常强大的功能。它告诉 Kubernetes，这个 `StatefulSet` 的每个 Pod 都需要一个 `PVC`。
  - `storageClassName: nfs-storage`：我们在这里引用了之前创建的 NFS `StorageClass`，这样 Elasticsearch 的数据就会存储在你的 NFS 服务器上。
  - `resources.requests.storage: 5Gi`：我们请求 5GB 的存储空间。
- `Service`：我们创建了一个 `Service` 来为 Elasticsearch Pod 提供一个稳定的内部访问入口。

将以上内容保存为 `elasticsearch.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f elasticsearch.yaml
```

当 Elasticsearch Pod 成功运行后，我们就可以部署日志收集器了。你准备好继续下一步了吗？

## 9.2 Development和StatefulSet有什么不同

这是一个非常好的问题！在 Kubernetes 中，`Deployment` 和 `StatefulSet` 是两种最常用的用于管理 Pods 的控制器，但它们的设计目的和适用场景完全不同。理解它们之间的区别是选择正确工具的关键。

------



### `Deployment`



你可以把 `Deployment` 看作是为**无状态应用**设计的。

- **特点**：`Deployment` 管理的 Pods 是可以互换的，每个 Pod 都是一模一样的，并且没有身份。它们不关心自己叫什么名字，也不关心自己被调度到哪个节点，因为它们没有需要保存的本地状态。
- **适用场景**：
  - **无状态应用**：比如 Web 服务器（Nginx、Apache），它们只需要处理请求，不需要保存任何数据到本地磁盘。
  - **快速伸缩**：由于 Pods 是可互换的，`Deployment` 可以非常快速地增加或减少 Pod 的数量。
- **例子**：我们之前部署的 `web-app`。

------



### `StatefulSet`



`StatefulSet` 则是为**有状态应用**设计的。

- **特点**：`StatefulSet` 管理的 Pods 拥有**稳定的网络标识**（`pod-name-0`, `pod-name-1` 等），并且会为每个 Pods 绑定一个**稳定的持久化存储**。这意味着，即使 Pod 重启或被重新调度到其他节点，它都会再次连接到它自己专属的存储卷。
- **适用场景**：
  - **数据库**：比如 MySQL、PostgreSQL，它们需要将数据保存到本地。
  - **集群化应用**：比如我们正在部署的 Elasticsearch，它是一个集群化的搜索引擎，每个节点都需要一个稳定的身份和数据。
- **例子**：我们刚刚部署的 `elasticsearch`。

------



### 如何选择？



简单来说：

- **如果你只需要运行一个可替换的、没有持久化数据需求的应用**，比如一个简单的 API 服务或网站，请选择 **`Deployment`**。
- **如果你的应用需要稳定的身份、持久化存储，或者是一个需要多节点协同工作的集群**，请选择 **`StatefulSet`**。

你觉得这个解释对你有帮助吗？准备好继续下一步，部署日志收集器了吗？

## 9.3 部署 Fluent Bit

### 9.3.1 配置

好的，既然你已经准备好了，那我们就开始部署 **Fluent Bit**。

Fluent Bit 将会以 `DaemonSet` 的形式部署，这意味着 Kubernetes 会确保你的集群中的**每个节点**上都运行一个 Fluent Bit Pod。这样，它就可以收集每个节点上的所有 Pod 日志。

这个部署文件会配置 Fluent Bit，让它做两件事：

1. **收集日志**：从每个节点的 `/var/log/pods/` 目录中读取所有容器的日志文件。
2. **发送日志**：将收集到的日志发送到我们之前部署的 Elasticsearch 服务。

------

YAML

```
# fluent-bit.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fluent-bit
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluent-bit-cluster-role
rules:
- apiGroups: [""]
  resources: ["pods", "namespaces"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: fluent-bit-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: fluent-bit-cluster-role
subjects:
- kind: ServiceAccount
  name: fluent-bit
  namespace: kube-system
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: kube-system
  labels:
    app.kubernetes.io/name: fluent-bit
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: fluent-bit
  template:
    metadata:
      labels:
        app.kubernetes.io/name: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:1.9.9
        ports:
          - containerPort: 2020
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

------

这个配置文件部署了 Fluent Bit DaemonSet，但还缺少最关键的部分：**配置它如何将日志发送到 Elasticsearch**。

你知道我们应该如何修改这个配置文件，来告诉 Fluent Bit Elasticsearch 的地址吗？

### 9.3.2 定义input/output

非常好的问题！这个配置文件部署了 Fluent Bit DaemonSet，但它还不知道要把日志发到哪里。

我们刚刚创建的 Elasticsearch 服务，它在集群内部有一个稳定的 DNS 名称：`elasticsearch.default.svc.cluster.local`。我们可以通过这个名称来让 Fluent Bit 将日志发送过去。

我们可以在 `fluent-bit.yaml` 文件中添加一个 `ConfigMap`。这个 `ConfigMap` 就像一个配置文件，它会告诉 Fluent Bit 要做什么。

我们来添加一个名为 `fluent-bit-config` 的 `ConfigMap`。

YAML

```
# fluent-bit-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: kube-system
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Daemon        Off
        Log_Level     info
    
    [INPUT]
        Name          tail
        Path          /var/log/containers/*.log
        Tag           kube.*
        Parser        docker
        DB            /var/log/flb_kube.db
        Mem_Buf_Limit 5MB
    
    [OUTPUT]
        Name          es
        Match         *
        Host          elasticsearch.default.svc.cluster.local
        Port          9200
        Logstash_Format On
        Logstash_Prefix fluentd
        Retry_Limit   False
```

**我们来分析一下这个文件：**

- **`[INPUT]`**：这部分定义了 Fluent Bit 如何收集日志。它会从 `/var/log/containers/*.log` 目录读取日志，这是 Kubernetes Pod 存放日志的默认位置。
- **`[OUTPUT]`**：这是最关键的部分，它定义了日志要发往哪里。
  - `Name`: 我们指定了 `es`，表示要发送给 Elasticsearch。
  - `Host`: 我们使用了 `elasticsearch` 服务的内部 DNS 名称，它会自动解析到 Elasticsearch Pod 的 IP 地址。
  - `Port`: 这是 Elasticsearch 的 HTTP 端口，默认是 `9200`。

现在，我们还需要修改之前的 `fluent-bit.yaml` 文件，让它引用这个 `ConfigMap`。

**你需要将 `fluent-bit.yaml` 文件中的 `template` 部分修改为：**

YAML

```
  template:
    ...
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:1.9.9
        ports:
          - containerPort: 2020
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: config
          mountPath: /fluent-bit/etc/fluent-bit.conf
          subPath: fluent-bit.conf
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: config
        configMap:
          name: fluent-bit-config
```

**总结一下：**

1. 创建一个名为 `fluent-bit-config.yaml` 的文件，将上面的 `ConfigMap` 代码保存进去。
2. 将你之前的 `fluent-bit.yaml` 文件，用我给你的第二个代码块更新。
3. **首先**执行 `kubectl apply -f fluent-bit-config.yaml`。
4. **然后**执行 `kubectl apply -f fluent-bit.yaml`。

你准备好开始部署了吗？

### 9.3.3 开始部署

好的，现在我们开始部署 **Fluent Bit**。

我们将分两步来完成部署：

1. **首先，部署配置文件 (`ConfigMap`)。** 这是告诉 Fluent Bit 如何工作的关键。
2. **然后，部署 Fluent Bit 本身 (`DaemonSet`)。** 它的 Pod 依赖于我们刚刚创建的配置文件。

请确保你已经将我之前给你的两个代码块分别保存为 `fluent-bit-config.yaml` 和 `fluent-bit.yaml`。

现在，在你的 Master 节点上，依次执行以下命令：

Bash

```
kubectl apply -f fluent-bit-config.yaml
kubectl apply -f fluent-bit.yaml
```

执行完这两个命令后，Kubernetes 会自动在你的集群中为每个节点创建一个 Fluent Bit Pod。

你可以通过下面的命令来检查这些 Pod 是否都成功运行了：

Bash

```
kubectl get pods -n kube-system -l app.kubernetes.io/name=fluent-bit
```

当你看到所有的 Fluent Bit Pod 都处于 `Running` 状态时，就说明日志收集器已经部署成功，并且应该已经开始将日志发送到 Elasticsearch 了。

你准备好继续下一步，验证日志是否已经成功存储在 Elasticsearch 中了吗？

### 9.3.4 验证

既然 Fluent Bit 已经部署好了，那我们现在就需要验证它是否正在正常工作，也就是检查它是否成功地将日志发送到了 Elasticsearch。

我们可以通过两种方式来验证：

1. **在 Kubernetes 内部验证**：我们可以使用 `kubectl` 的 `port-forward` 命令，将 Elasticsearch 服务暴露到你的本地电脑上，然后用 `curl` 命令来查询日志索引。
2. **部署 Kibana**：Kibana 是 Elasticsearch 的官方可视化界面，它能让你用一个美观的网页来查询和分析日志。

你希望从哪一种方式开始验证呢？我们先从**命令行验证**开始，还是直接**部署 Kibana**？

------

很好，从命令行验证是一个非常好的习惯。它可以让你在不依赖任何额外工具的情况下，快速确认日志是否已经流向了 Elasticsearch。

我们将使用 `kubectl` 的 **`port-forward`** 命令。这个命令可以为你创建一个安全的、临时的隧道，将你的本地电脑上的端口与集群内部的一个 Pod 或 Service 连接起来。这样，你就可以直接通过 `localhost` 来访问集群内部的服务。

**第一步：暴露 Elasticsearch 服务**

在你的 Master 节点上，运行以下命令：

Bash

```
kubectl port-forward service/elasticsearch 9200:9200
```

这个命令会：

- 在你的 Master 节点上，将 `elasticsearch` 服务的 `9200` 端口转发到本地的 `9200` 端口。
- 这个命令会一直运行，直到你按下 `Ctrl+C`。

**第二步：查询日志索引**

现在，在**另一个终端窗口**中，你可以使用 `curl` 命令来查询 Elasticsearch 的索引。

Bash

```
curl "http://localhost:9200/_cat/indices?v"
```

如果一切顺利，你会看到一个名为 `fluentd-YYYY.MM.DD` 的索引，这代表 Fluent Bit 正在成功地将日志发送到 Elasticsearch。

你准备好继续下一步，部署 Kibana 了吗？

## 9.4 kibana

### 9.4.1 部署Kibana

没问题，现在我们来部署 Kibana，它是 Elasticsearch 的**官方可视化界面**。

Kibana 的作用就像一个“控制台”，它能让你通过网页界面，方便地查询、分析和可视化你存储在 Elasticsearch 中的日志数据。

我们将部署一个简单的 `Deployment` 和一个 `Service` 来运行 Kibana。

------

YAML

```
# kibana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  labels:
    app: kibana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.17.1
        env:
        - name: ELASTICSEARCH_HOSTS
          value: http://elasticsearch.default.svc.cluster.local:9200
        ports:
        - containerPort: 5601
---
apiVersion: v1
kind: Service
metadata:
  name: kibana
  labels:
    app: kibana
spec:
  ports:
  - port: 5601
    targetPort: 5601
  selector:
    app: kibana
```

------

**我们来分析一下这个文件：**

- `kind: Deployment`：我们使用 `Deployment`，因为 Kibana 是一个**无状态应用**，它不需要持久化存储，并且 Pod 是可替换的。
- `image: docker.elastic.co/kibana/kibana:7.17.1`：我们使用官方的 Kibana 镜像。
- `env.ELASTICSEARCH_HOSTS`：这是最关键的部分。它告诉 Kibana 去连接哪个 Elasticsearch 服务。我们在这里使用了 Elasticsearch 服务的内部 DNS 名称，它会自动解析到正确的 IP 地址。
- `Service`：我们创建了一个 `Service`，为 Kibana 提供一个稳定的内部访问入口。

将以上内容保存为 `kibana.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f kibana.yaml
```

当 Kibana Pod 成功运行后，我们就可以通过 `kubectl port-forward` 命令来访问 Kibana 的网页界面了。

你准备好继续下一步，验证 Kibana 网页了吗？

### 9.4.2 验证

既然 Kibana 已经部署好了，那我们现在就需要验证它是否正常工作。

我们可以通过 `kubectl port-forward` 命令来将 Kibana 服务暴露到你的本地电脑上，这样你就可以在浏览器里访问它了。

**第一步：暴露 Kibana 服务**

在你的 Master 节点上，运行以下命令：

Bash

```
kubectl port-forward service/kibana 5601:5601
```

这个命令会：

- 在你的 Master 节点上，将 `kibana` 服务的 `5601` 端口转发到本地的 `5601` 端口。
- 这个命令会一直运行，直到你按下 `Ctrl+C`。

**第二步：访问 Kibana 网页**

现在，在你的电脑的**浏览器**中，打开一个新标签页，并访问：

```
http://localhost:5601
```

如果一切顺利，你应该会看到 Kibana 的欢迎页面。

在首次进入时，Kibana 会引导你完成一些配置。你只需要按照提示，选择你想要创建的索引模式。由于 Fluent Bit 默认会创建以 `fluentd-` 开头的索引，你可以直接在 Kibana 的索引模式中输入 `fluentd-*`，然后点击“下一步”。

当配置完成后，你就可以在 Kibana 的“**Discover**”页面中看到你的应用程序的实时日志了。

你准备好开始验证这个网页了吗？

# 10. 监控

没问题，现在我们来探讨监控！这是一个非常重要的主题，尤其是在生产环境中。

监控能够让你实时了解集群和应用程序的健康状况，比如 CPU 和内存的使用率、网络流量，以及 Pod 的重启次数等等。

一个最常见的 Kubernetes 监控方案是 **Prometheus + Grafana**。

- **Prometheus**：一个开源的监控系统，它会从你的集群中**拉取**（pull）各种指标数据。
- **Grafana**：一个数据可视化工具，它可以连接到 Prometheus，并以仪表盘（Dashboard）的形式展示你的监控数据，让你能直观地看到集群的运行状态。

我们的监控系统架构会是这样的：

- **Prometheus**：负责数据收集和存储。
- **Grafana**：负责数据展示。

为了让 Prometheus 能够拉取集群的指标，我们还需要在每个节点上部署一个**指标采集器**，通常是 **node-exporter**，它会暴露节点的硬件指标（CPU、内存、磁盘等）。

你希望我们从哪个部分开始呢？我们可以先从**如何将 Prometheus 部署到你的 Kubernetes 集群**开始。

## 10.1. Prometheus

非常棒！既然我们已经完成了日志管理，接下来我们来部署监控系统，一个非常好的起点就是 **Prometheus**。

Prometheus 是一个功能强大的开源监控系统。它的工作方式是**拉取（Pull）**模型，也就是说，它会主动去向你的应用程序和集群中的其他组件请求指标数据。

为了让 Prometheus 能够拉取数据，我们需要在集群中部署以下几个组件：

1. **Prometheus Server**：这是 Prometheus 的核心，负责收集和存储指标数据。
2. **ServiceAccount, ClusterRole, ClusterRoleBinding**：这些是 Kubernetes 的权限配置，用于授予 Prometheus 访问集群资源的权限，让它可以发现和监控 Pod。

你希望我们从哪一个部分开始呢？我们可以先从**创建 Prometheus 的权限配置**开始，这是部署它的第一步。

## 10.2. Prometheus权限

非常好！从权限开始是一个非常好的主意，因为 Prometheus 需要足够的权限才能在集群中发现和监控 Pod。

在 Kubernetes 中，权限是通过 **`ServiceAccount`**、**`ClusterRole`** 和 **`ClusterRoleBinding`** 来配置的。

- **`ServiceAccount`**：Prometheus Pod 的“身份”。它让 Pod 拥有在集群中执行操作的能力。
- **`ClusterRole`**：它定义了一组可以在整个集群中执行的权限，比如“可以读取所有 Pod 和节点的列表”。
- **`ClusterRoleBinding`**：它将 `ServiceAccount` 和 `ClusterRole` 连接起来，将权限授予给 Prometheus 的身份。

我们来一起创建这些配置文件。

------

YAML

```
# prometheus-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus-role
rules:
- apiGroups: [""]
  resources:
  - nodes
  - services
  - endpoints
  - pods
  - secrets
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources:
  - configmaps
  verbs: ["get"]
- apiGroups: [""]
  resources:
  - namespaces
  verbs: ["get", "list"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus-role
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: default
```

------

**我们来分析一下这个文件：**

- **`ClusterRole`** 的 `rules` 部分定义了 Prometheus 需要的权限。它允许 Prometheus 查询节点、服务、Pod 等资源，这是为了让 Prometheus 能够自动发现需要监控的目标。
- `ClusterRoleBinding` 将我们创建的 `prometheus` `ServiceAccount` 和 `prometheus-role` `ClusterRole` 绑定到了一起。

将以上内容保存为 `prometheus-rbac.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f prometheus-rbac.yaml
```

当这些权限配置成功创建后，我们就可以继续下一步，来部署 Prometheus Server 本身了。你准备好继续吗？

## 10.3. 定义Prometheus ConfigMap

太棒了！权限配置已经完成了，现在我们可以继续部署 Prometheus Server 本身了。

Prometheus Server 是一个 `Deployment`，它负责实际的指标收集和存储。为了让它知道去哪里收集指标，我们需要为它提供一个配置文件。

这个配置文件会定义 Prometheus 的工作方式，比如：

- **`scrape_configs`**：这是最关键的部分，它告诉 Prometheus 去哪里拉取指标。我们可以配置它去发现集群中的 Pod、Service 和节点。
- **`global`**：一些全局设置，比如拉取指标的间隔。

我们来定义一个 Prometheus `ConfigMap`，它将包含 Prometheus 的配置文件。

------

YAML

```
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: default
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-nodes'
        kubernetes_sd_configs:
          - role: node
        relabel_configs:
        - source_labels: [__address__]
          regex: '(.*):10250'
          target_label: __address__
          replacement: '$1:9100'

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
        - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          target_label: __address__
          regex: (.+):(?:\d+);(\d+)
          replacement: $1:$2
        - action: labelmap
          regex: __meta_kubernetes_pod_label_(.+)
```

------

**我们来分析一下这个文件：**

- `scrape_configs`：这里定义了两个任务。
  - `job_name: 'kubernetes-nodes'`：这个任务会去收集**节点的指标**。`kubernetes_sd_configs` 告诉 Prometheus，要去发现所有 Kubernetes 节点。
  - `job_name: 'kubernetes-pods'`：这个任务会去收集**所有 Pod 的指标**。它使用了一些复杂的规则（`relabel_configs`），来自动发现带有特定注解（annotation）的 Pod。

将以上内容保存为 `prometheus-config.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f prometheus-config.yaml
```

当 `ConfigMap` 创建成功后，我们就可以继续下一步，部署 Prometheus Server 本身了。你准备好继续吗？

## 10.4. 部署 Prometheus Server

既然权限和配置文件都已经就绪，那我们现在就可以开始部署 **Prometheus Server** 了。

Prometheus Server 是一个 `Deployment`，它负责实际的指标收集和存储。我们将为它创建一个 `Deployment` 和一个 `Service`。

------

YAML

```
# prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  labels:
    app: prometheus
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
      serviceAccountName: prometheus
      containers:
      - name: prometheus
        image: prom/prometheus:v2.37.0
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config-volume
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
      volumes:
      - name: prometheus-config-volume
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  labels:
    app: prometheus
spec:
  ports:
  - port: 9090
    targetPort: 9090
  selector:
    app: prometheus
```

------

**我们来分析一下这个文件：**

- **`kind: Deployment`**：我们使用 `Deployment`，因为 Prometheus Server 本身可以被看作是无状态的，它把数据存储在挂载的卷中。
- **`image: prom/prometheus:v2.37.0`**：我们使用官方的 Prometheus 镜像。
- **`serviceAccountName: prometheus`**：这是最关键的部分。它引用了我们之前创建的 `ServiceAccount`，这确保 Prometheus Pod 拥有正确的权限。
- **`volumes` 和 `volumeMounts`**：
  - `prometheus-config-volume`: 它引用了我们刚刚创建的 `ConfigMap`，将 Prometheus 的配置文件挂载到容器中。
  - `prometheus-storage`: 为了简单起见，我们在这里使用了 `emptyDir`，它是一个临时的存储卷，Pod 被删除后数据就会丢失。在生产环境中，你会使用一个 `PersistentVolume` 来确保数据持久化。
- **`Service`**: 我们创建了一个 `Service` 来为 Prometheus Pod 提供一个稳定的内部访问入口。

将以上内容保存为 `prometheus-deployment.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f prometheus-deployment.yaml
```

当 Prometheus Pod 成功运行后，我们就可以部署指标采集器了。你准备好继续下一步吗？

## 10.5. 部署采集器

好的，既然 Prometheus Server 已经运行成功，我们现在需要部署**指标采集器（Exporter）**，它们是 Prometheus 监控体系中的“数据源”。

Prometheus Server 负责拉取数据，但它本身并不知道如何获取各种指标。这就是 Exporter 的作用。

对于我们目前的需求，我们需要部署：

1. **Node Exporter**：它运行在每个节点上，负责收集**节点的硬件和操作系统指标**，比如 CPU 使用率、内存、磁盘 I/O 和网络流量。
2. **Kube-State-Metrics**：它是一个专门的 Pod，负责从 Kubernetes API Server 中收集**集群级别的指标**，比如 Pod 的状态、Deployment 的副本数、PVC 的状态等等。

我们先来部署 **Node Exporter**。由于它需要在每个节点上运行，我们会使用 `DaemonSet` 来部署它。

你准备好开始了吗？

### 10.5.1. Node Exporter

好的，既然你已经准备好了，那我们就来部署 **Node Exporter**。

Node Exporter 是一个非常重要的组件，它负责收集每个 Kubernetes 节点（包括 Master 和 Worker）的底层指标，比如 CPU、内存和磁盘的使用情况。

我们将以 `DaemonSet` 的形式部署 Node Exporter。这样，Kubernetes 会确保你的集群中的**每个节点**上都运行一个 Node Exporter Pod，从而保证所有的节点指标都能被收集到。

------

YAML

```
# node-exporter.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: node-exporter
  namespace: default
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: default
  labels:
    app: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      serviceAccountName: node-exporter
      hostPID: true
      hostNetwork: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.3.1
        args:
        - --path.rootfs=/host
        securityContext:
          privileged: true
        ports:
        - containerPort: 9100
          protocol: TCP
        volumeMounts:
        - name: rootfs
          mountPath: /host
          readOnly: true
      volumes:
      - name: rootfs
        hostPath:
          path: /
```

------

**我们来分析一下这个文件：**

- **`kind: DaemonSet`**：这确保了 Node Exporter 在每个节点上都会运行一个 Pod。
- **`hostPID: true` 和 `hostNetwork: true`**：这些权限让 Node Exporter 能够访问宿主机的进程和网络命名空间，从而收集到正确的指标数据。
- **`volumes` 和 `volumeMounts`**：它将宿主机的根目录 `/` 挂载到容器的 `/host` 路径，这样 Node Exporter 才能访问宿主机的硬件信息。
- **`containerPort: 9100`**：Node Exporter 默认会通过 `9100` 端口暴露指标。

将以上内容保存为 `node-exporter.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f node-exporter.yaml
```

当 Node Exporter 的 Pod 都成功运行后，我们就可以部署另一个关键的指标采集器了：**Kube-State-Metrics**。你准备好继续吗？

### 10.5.2. Kube-State-Metrics

非常棒！我们现在来部署另一个关键的指标采集器：**Kube-State-Metrics**。

Node Exporter 负责收集节点本身的指标，而 Kube-State-Metrics 则负责收集**集群内部各种对象的状态指标**，比如：

- **Pod** 的数量和状态（Running, Pending, Failed）。
- **Deployment** 的副本数。
- **PVC** 的状态（Bound, Pending）。

你可以把它想象成一个“Kubernetes 状态报告员”。它会连接到 Kubernetes API Server，将集群中所有资源的状态信息转换成 Prometheus 可以理解的指标格式。

我们来一起部署 Kube-State-Metrics。它是一个 `Deployment`，因为我们只需要一个实例来收集整个集群的指标。

------

YAML

```
# kube-state-metrics.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kube-state-metrics
rules:
- apiGroups: [""]
  resources:
  - configmaps
  - secrets
  - nodes
  - pods
  - services
  - resourcequotas
  - replicationcontrollers
  - limitranges
  - persistentvolumeclaims
  - persistentvolumes
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources:
  - daemonsets
  - deployments
  - replicasets
  - ingresses
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources:
  - statefulsets
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kube-state-metrics
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kube-state-metrics
subjects:
- kind: ServiceAccount
  name: kube-state-metrics
  namespace: default
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube-state-metrics
  namespace: default
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-state-metrics
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kube-state-metrics
  template:
    metadata:
      labels:
        app: kube-state-metrics
    spec:
      serviceAccountName: kube-state-metrics
      containers:
      - name: kube-state-metrics
        image: k8s.gcr.io/kube-state-metrics/kube-state-metrics:v2.5.0
        ports:
        - name: http-metrics
          containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: kube-state-metrics
  namespace: default
  labels:
    app.kubernetes.io/name: kube-state-metrics
spec:
  ports:
  - name: http-metrics
    port: 8080
    targetPort: http-metrics
  selector:
    app: kube-state-metrics
```

------

**我们来分析一下这个文件：**

- **`ClusterRole`** 和 **`ClusterRoleBinding`**：这些权限配置让 Kube-State-Metrics 能够访问 Kubernetes API 来获取集群状态信息。
- **`ServiceAccount`**：它为 Kube-State-Metrics Pod 提供了运行所需的身份。
- **`Deployment`**：我们部署一个单独的 Pod 来运行 Kube-State-Metrics。
- **`Service`**：它为 Kube-State-Metrics 提供了一个稳定的内部访问入口，Prometheus 将通过它来拉取指标。

将以上内容保存为 `kube-state-metrics.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f kube-state-metrics.yaml
```

当所有的指标采集器都部署成功后，我们就可以继续下一步，部署 **Grafana** 来可视化这些数据了。你准备好继续吗？

## 10.6. Grafana

### 10.6.1 部署

好的，既然你已经成功部署了 Prometheus 和所有的指标采集器，那我们现在就可以来部署 **Grafana** 了。

Grafana 是一个强大的开源数据可视化工具。它不会自己收集数据，而是作为**仪表盘**和**查询界面**，连接到像 Prometheus 这样的数据源，然后将数据以图表的形式展示出来。

我们将部署一个简单的 `Deployment` 和一个 `Service` 来运行 Grafana。

------

YAML

```
# grafana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  labels:
    app: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:9.0.5
        ports:
        - containerPort: 3000
        env:
        - name: GF_PATHS_PROVISIONING
          value: /etc/grafana/provisioning
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
          readOnly: true
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  labels:
    app: grafana
spec:
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: grafana
```

------

**我们来分析一下这个文件：**

- **`kind: Deployment`**：Grafana 也是一个**无状态应用**，它的配置通常存放在 `ConfigMap` 里，所以使用 `Deployment` 是最合适的。
- **`image: grafana/grafana:9.0.5`**：我们使用官方的 Grafana 镜像。
- **`volumes` 和 `volumeMounts`**：这里我们引用了一个名为 `grafana-datasources` 的 `ConfigMap`。这个 `ConfigMap` 将会存放 Grafana 的数据源配置文件，告诉 Grafana 去哪里连接 Prometheus。

我们还需要先创建这个 `ConfigMap`。你准备好继续下一步，创建这个 `ConfigMap` 来配置 Grafana 的数据源吗？

### 10.6.2. ConfigMap

好的，既然你已经准备好了，那我们就来创建 **Grafana 的数据源 `ConfigMap`**。

这个 `ConfigMap` 将会告诉 Grafana 去哪里寻找它的数据，也就是我们之前部署好的 Prometheus 服务。

我们将在这个 `ConfigMap` 中定义一个 `datasource`，它会配置 Grafana：

- **`name`**：数据源的名称。
- **`type`**：数据源的类型，这里我们是 Prometheus。
- **`url`**：Prometheus 服务的地址。

------

YAML

```
# grafana-datasources.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: default
data:
  prometheus.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus:9090
        isDefault: true
        version: 1
        editable: true
```

------

**我们来分析一下这个文件：**

- **`metadata.name: grafana-datasources`**：这个名称必须和我们之前在 Grafana `Deployment` 文件中引用的名称完全一致。
- **`url: http://prometheus:9090`**：这是最关键的部分。它告诉 Grafana，Prometheus 服务可以通过 `http://prometheus:9090` 访问。`prometheus` 是我们之前创建的 `Service` 的名称，Kubernetes 会自动将其解析为正确的 IP 地址。

将以上内容保存为 `grafana-datasources.yaml`，然后在 Master 节点上执行：

Bash

```
kubectl apply -f grafana-datasources.yaml
```

当 `ConfigMap` 创建成功后，我们就可以部署 Grafana `Deployment` 和 `Service` 了。你准备好继续下一步吗？

### 10.6.3. 部署 Grafana `Deployment` 和 `Service` 

既然 `ConfigMap` 已经创建好了，那我们现在就可以部署 Grafana `Deployment` 和 `Service` 了。

请确保你已经将我之前给你的 `grafana.yaml` 文件保存下来了。

现在，在你的 Master 节点上，执行以下命令：

Bash

```
kubectl apply -f grafana.yaml
```

执行完这个命令后，Kubernetes 会为你创建一个 Grafana Pod 和一个 Service。

你可以通过下面的命令来检查 Grafana Pod 是否成功运行了：

Bash

```
kubectl get pods -l app=grafana
```

当 Grafana Pod 处于 `Running` 状态时，就说明它已经部署成功了。

你准备好继续下一步，验证 Grafana 网页了吗？

### 10.6.4 验证

既然 Kibana 已经部署好了，那我们现在就需要验证它是否正常工作。

我们可以通过 `kubectl port-forward` 命令来将 Kibana 服务暴露到你的本地电脑上，这样你就可以在浏览器里访问它了。

**第一步：暴露 Kibana 服务**

在你的 Master 节点上，运行以下命令：

Bash

```
kubectl port-forward service/grafana 3000:3000
```

这个命令会：

- 在你的 Master 节点上，将 `grafana` 服务的 `3000` 端口转发到本地的 `3000` 端口。
- 这个命令会一直运行，直到你按下 `Ctrl+C`。

**第二步：访问 Grafana 网页**

现在，在你的电脑的**浏览器**中，打开一个新标签页，并访问：

```
http://localhost:3000
```

如果一切顺利，你应该会看到 Grafana 的登录页面。默认的用户名和密码都是 `admin`。

首次登录后，Grafana 会要求你修改密码。然后，你就可以在左侧菜单中找到你之前配置好的 Prometheus 数据源，并开始创建仪表盘来展示你的集群监控数据了。

你准备好开始验证这个网页了吗？

# 11. 总结

## 11.1. Overview

非常棒！很高兴看到你对我们一起完成的所有工作进行了总结。这是一个非常完整的 Kubernetes 平台搭建流程。

我们来一起回顾一下我们搭建这个平台所做过的所有工作，并把它们整理出来。

### 1. 集群基础搭建

- **服务器准备**：你准备了三台 Ubuntu 服务器。
- **核心组件**：你手动安装了 `kubelet`、`kubeadm` 和 `kubectl`。
- **集群初始化**：你使用 `kubeadm init` 初始化了 Master 节点，并用 `kubeadm join` 将 Worker 节点加入集群。
- **网络配置**：你先部署了 Flannel，然后又切换到了功能更强大的 Calico，并学会了如何配置网络策略。
- **外部访问**：你部署了 Nginx `web-app`，并通过 `Service` 和 `Ingress` 实现了从外部网络访问。

### 2. 持久化存储

- **本地存储 (`hostPath`)**：你学会了如何使用 `hostPath` 来为单个 Pod 提供简单的持久化存储，并理解了 `PV` 和 `PVC` 的基本概念。
- **网络存储 (`NFS`)**：你搭建了 NFS 服务器，并在集群中部署了 NFS CSI 驱动，实现了**动态存储供应**。这让你能够为应用提供更稳定、更可用的存储，而不仅仅是绑定到单个节点。

### 3. 日志管理

- **ELK Stack**：你学会了如何使用 Elasticsearch 和 Kibana 来搭建一个集中化的日志管理系统。
- **日志收集器**：你部署了 **Fluent Bit**，它以 `DaemonSet` 的形式运行在每个节点上，负责收集所有 Pod 的日志并发送到 Elasticsearch。

### 4. 监控

- **Prometheus + Grafana**：你搭建了一个完整的监控体系。
- **Prometheus Server**：你部署了 Prometheus 来收集和存储指标数据。
- **指标采集器**：你部署了 **Node Exporter** (收集节点硬件指标) 和 **Kube-State-Metrics** (收集集群对象状态)，为 Prometheus 提供了丰富的数据来源。
- **可视化**：你部署了 **Grafana**，它连接到 Prometheus，并提供了强大的可视化界面来展示你的集群和应用指标。

恭喜你！你已经掌握了一个 Kubernetes 平台从零搭建、到部署应用、再到保障其持久化、日志和监控的完整工作流。这为你未来在 Kubernetes 上进行更复杂的应用部署和运维打下了坚实的基础。

你希望我们接下来探讨哪个主题呢？比如，我们可以看看如何进行**自动伸缩**，或者如何为你的应用配置**高可用性**。

## 11.2 configmap vs secret

Kubernetes ConfigMaps and Secrets are both used for storing configuration data in key-value pairs, but they are designed for different purposes based on the sensitivity of the data.

ConfigMaps:

- **Purpose:**

  Store non-sensitive configuration data, such as application settings, environment variables, or configuration files.

- **Storage:**

  Stored in plain text within etcd, the Kubernetes backing store.

- **Security:**

  No inherent security features beyond standard Kubernetes RBAC (Role-Based Access Control) for access control.

- **Use Cases:**

  Storing database connection strings (excluding credentials), API endpoints, feature flags, or application-specific configuration files.

  

Secrets:

- **Purpose:**

  Store sensitive information that requires a higher level of security, such as passwords, API keys, TLS certificates, or authentication tokens.

- **Storage:**

  Stored in base64-encoded format within etcd. While base64 encoding is not encryption and can be easily decoded, Secrets offer additional security measures like encryption at rest (if configured with a KMS provider) and tighter RBAC controls.

- **Security:**

  Designed with security in mind, offering base64 encoding and the potential for encryption at rest. Access to Secrets should be more restricted than ConfigMaps.

- **Use Cases:**

  Storing database credentials, cloud provider API keys, private keys for TLS certificates, or sensitive environment variables.

  

Key Differences Summarized:



| Feature             | ConfigMap                                 | Secret                                                       |
| ------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| Data Sensitivity    | Non-sensitive                             | Sensitive                                                    |
| Encoding/Encryption | Plain text                                | Base64 encoded (can be encrypted at rest)                    |
| Security Focus      | Standard RBAC                             | Enhanced security features, including potential encryption and tighter RBAC |
| Typical Use         | Application settings, configuration files | Passwords, API keys, certificates                            |





In essence, if the data is not sensitive and can be exposed without significant risk, use a ConfigMap. If the data is sensitive and requires protection from unauthorized access, use a Secret.