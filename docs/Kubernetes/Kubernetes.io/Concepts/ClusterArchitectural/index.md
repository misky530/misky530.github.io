# Cluster Architecture

The architectural concepts behind Kubernetes.

A Kubernetes cluster consists of a control plane plus a set of worker machines, called nodes, that run containerized applications. Every cluster needs at least one worker node in order to run Pods.

The worker node(s) host the Pods that are the components of the application workload. The control plane manages the worker nodes and the Pods in the cluster. In production environments, the control plane usually runs across multiple computers and a cluster usually runs multiple nodes, providing fault-tolerance and high availability.

This document outlines the various components you need to have for a complete and working Kubernetes cluster.

```
Kubernetes 集群由一个控制平面和一组​​运行容器化应用程序的工作节点（称为节点）组成。每个集群至少需要一个工作节点来运行 Pod。

工作节点托管构成应用程序工作负载的 Pod。控制平面管理集群中的工作节点和 Pod。在生产环境中，控制平面通常跨多台计算机运行，而集群通常运行多个节点，以提供容错能力和高可用性。

本文档概述了构建完整且正常运行的 Kubernetes 集群所需的各种组件。
```

![The control plane (kube-apiserver, etcd, kube-controller-manager, kube-scheduler) and several nodes. Each node is running a kubelet and kube-proxy.](https://kubernetes.io/images/docs/kubernetes-cluster-architecture.svg)

Figure 1. Kubernetes cluster components.


## Control plane components

The control plane's components make global decisions about the cluster (for example, scheduling), as well as detecting and responding to cluster events (for example, starting up a new [pod](https://kubernetes.io/docs/concepts/workloads/pods/) when a Deployment's `replicas` field is unsatisfied).

Control plane components can be run on any machine in the cluster. However, for simplicity, setup scripts typically start all control plane components on the same machine, and do not run user containers on this machine. See [Creating Highly Available clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/) for an example control plane setup that runs across multiple machines.

### kube-apiserver

The API server is a component of the Kubernetes [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) that exposes the Kubernetes API. The API server is the front end for the Kubernetes control plane.

The main implementation of a Kubernetes API server is [kube-apiserver](https://kubernetes.io/docs/reference/generated/kube-apiserver/). kube-apiserver is designed to scale horizontally—that is, it scales by deploying more instances. You can run several instances of kube-apiserver and balance traffic between those instances.

### etcd

Consistent and highly-available key value store used as Kubernetes' backing store for all cluster data.

If your Kubernetes cluster uses etcd as its backing store, make sure you have a [back up](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#backing-up-an-etcd-cluster) plan for the data.

You can find in-depth information about etcd in the official [documentation](https://etcd.io/docs/).

### kube-scheduler

Control plane component that watches for newly created [Pods](https://kubernetes.io/docs/concepts/workloads/pods/) with no assigned [node](https://kubernetes.io/docs/concepts/architecture/nodes/), and selects a node for them to run on.

Factors taken into account for scheduling decisions include: individual and collective [resource](https://kubernetes.io/docs/reference/glossary/?all=true#term-infrastructure-resource) requirements, hardware/software/policy constraints, affinity and anti-affinity specifications, data locality, inter-workload interference, and deadlines.

### kube-controller-manager

Control plane component that runs [controller](https://kubernetes.io/docs/concepts/architecture/controller/) processes.

Logically, each [controller](https://kubernetes.io/docs/concepts/architecture/controller/) is a separate process, but to reduce complexity, they are all compiled into a single binary and run in a single process.

There are many different types of controllers. Some examples of them are:

- Node controller: Responsible for noticing and responding when nodes go down.
- Job controller: Watches for Job objects that represent one-off tasks, then creates Pods to run those tasks to completion.
- EndpointSlice controller: Populates EndpointSlice objects (to provide a link between Services and Pods).
- ServiceAccount controller: Create default ServiceAccounts for new namespaces.

The above is not an exhaustive list.

### cloud-controller-manager

A Kubernetes [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) component that embeds cloud-specific control logic. The cloud controller manager lets you link your cluster into your cloud provider's API, and separates out the components that interact with that cloud platform from components that only interact with your cluster.

The cloud-controller-manager only runs controllers that are specific to your cloud provider. If you are running Kubernetes on your own premises, or in a learning environment inside your own PC, the cluster does not have a cloud controller manager.

As with the kube-controller-manager, the cloud-controller-manager combines several logically independent control loops into a single binary that you run as a single process. You can scale horizontally (run more than one copy) to improve performance or to help tolerate failures.

The following controllers can have cloud provider dependencies:

- Node controller: For checking the cloud provider to determine if a node has been deleted in the cloud after it stops responding
- Route controller: For setting up routes in the underlying cloud infrastructure
- Service controller: For creating, updating and deleting cloud provider load balancers

```
## 控制平面组件

控制平面的组件负责对集群进行全局决策（例如，调度），并检测和响应集群事件（例如，当 Deployment 的 `replicas` 字段未满足要求时，启动新的 [pod](https://kubernetes.io/docs/concepts/workloads/pods/)。

控制平面组件可以在集群中的任何机器上运行。但是，为了简单起见，安装脚本通常在同一台机器上启动所有控制平面组件，并且不在此机器上运行用户容器。有关跨多台机器运行的控制平面设置示例，请参阅[使用 kubeadm 创建高可用集群](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)。

### kube-apiserver

API 服务器是 Kubernetes [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 的一个组件，用于公开 Kubernetes API。API 服务器是 Kubernetes 控制平面的前端。

Kubernetes API 服务器的主要实现是 [kube-apiserver](https://kubernetes.io/docs/reference/generated/kube-apiserver/)。kube-apiserver 旨在实现水平扩展，即通过部署更多实例来实现扩展。您可以运行多个 kube-apiserver 实例，并在这些实例之间均衡流量。

### etcd

一致性高可用性键值存储，用作 Kubernetes 所有集群数据的后备存储。

如果您的 Kubernetes 集群使用 etcd 作为其后备存储，请确保您已为数据制定了备份计划。

您可以在官方文档中找到有关 etcd 的详细信息。

### kube-scheduler

控制平面组件，用于监视新创建的未分配节点的 Pod，并选择一个节点供其运行。

调度决策需要考虑的因素包括：单个和多个[资源](https://kubernetes.io/docs/reference/glossary/?all=true#term-infrastructure-resource) 需求、硬件/软件/策略约束、亲和性和反亲和性规范、数据本地性、工作负载间干扰以及截止期限。

### kube-controller-manager

运行[控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 进程的控制平面组件。

逻辑上，每个[控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 都是一个独立的进程，但为了降低复杂性，它们都被编译成一个二进制文件并在一个进程中运行。

控制器有很多不同的类型。以下是一些示例：

- 节点控制器：负责在节点发生故障时进行通知和响应。
- 作业控制器：监视代表一次性任务的作业对象，然后创建 Pod 来运行这些任务直至完成。
- 端点切片控制器：填充端点切片对象（用于在服务和 Pod 之间建立链接）。
- 服务帐户控制器：为新的命名空间创建默认的服务帐户。

以上并非详尽列表。

### 云控制器管理器

一个 Kubernetes [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 组件，嵌入了特定于云平台的控制逻辑。云控制器管理器允许您将集群链接到云提供商的 API，并将与该云平台交互的组件与仅与您的集群交互的组件分离。

云控制器管理器仅运行特定于您的云提供商的控制器。如果您在自己的本地或个人电脑的学习环境中运行 Kubernetes，则集群没有云控制器管理器。

与 kube-controller-manager 一样，cloud-controller-manager 将多个逻辑上独立的控制循环组合成一个二进制文件，并作为单个进程运行。您可以水平扩展（运行多个副本）以提高性能或增强容错能力。

以下控制器可以依赖云提供商：

- 节点控制器：用于检查云提供商，以确定节点停止响应后是否已在云中删除
- 路由控制器：用于在底层云基础架构中设置路由
- 服务控制器：用于创建、更新和删除云提供商负载均衡器
```



------

## Node components

Node components run on every node, maintaining running pods and providing the Kubernetes runtime environment.

### kubelet

An agent that runs on each [node](https://kubernetes.io/docs/concepts/architecture/nodes/) in the cluster. It makes sure that [containers](https://kubernetes.io/docs/concepts/containers/) are running in a [Pod](https://kubernetes.io/docs/concepts/workloads/pods/).

The [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) takes a set of PodSpecs that are provided through various mechanisms and ensures that the containers described in those PodSpecs are running and healthy. The kubelet doesn't manage containers which were not created by Kubernetes.

### kube-proxy (optional)



kube-proxy is a network proxy that runs on each [node](https://kubernetes.io/docs/concepts/architecture/nodes/) in your cluster, implementing part of the Kubernetes [Service](https://kubernetes.io/docs/concepts/services-networking/service/) concept.

[kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) maintains network rules on nodes. These network rules allow network communication to your Pods from network sessions inside or outside of your cluster.

kube-proxy uses the operating system packet filtering layer if there is one and it's available. Otherwise, kube-proxy forwards the traffic itself.

If you use a [network plugin](https://kubernetes.io/docs/concepts/architecture/#network-plugins) that implements packet forwarding for Services by itself, and providing equivalent behavior to kube-proxy, then you do not need to run kube-proxy on the nodes in your cluster.



### Container runtime

A fundamental component that empowers Kubernetes to run containers effectively. It is responsible for managing the execution and lifecycle of containers within the Kubernetes environment.

Kubernetes supports container runtimes such as [containerd](https://containerd.io/docs/), [CRI-O](https://cri-o.io/#what-is-cri-o), and any other implementation of the [Kubernetes CRI (Container Runtime Interface)](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/container-runtime-interface.md).

## Addons

Addons use Kubernetes resources ([DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset), [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), etc) to implement cluster features. Because these are providing cluster-level features, namespaced resources for addons belong within the `kube-system` namespace.

Selected addons are described below; for an extended list of available addons, please see [Addons](https://kubernetes.io/docs/concepts/cluster-administration/addons/).

### DNS

While the other addons are not strictly required, all Kubernetes clusters should have [cluster DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/), as many examples rely on it.

Cluster DNS is a DNS server, in addition to the other DNS server(s) in your environment, which serves DNS records for Kubernetes services.

Containers started by Kubernetes automatically include this DNS server in their DNS searches.

### Web UI (Dashboard)

[Dashboard](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/) is a general purpose, web-based UI for Kubernetes clusters. It allows users to manage and troubleshoot applications running in the cluster, as well as the cluster itself.

### Container resource monitoring

[Container Resource Monitoring](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-usage-monitoring/) records generic time-series metrics about containers in a central database, and provides a UI for browsing that data.

### Cluster-level Logging

A [cluster-level logging](https://kubernetes.io/docs/concepts/cluster-administration/logging/) mechanism is responsible for saving container logs to a central log store with a search/browsing interface.

### Network plugins

[Network plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) are software components that implement the container network interface (CNI) specification. They are responsible for allocating IP addresses to pods and enabling them to communicate with each other within the cluster.

## Architecture variations

While the core components of Kubernetes remain consistent, the way they are deployed and managed can vary. Understanding these variations is crucial for designing and maintaining Kubernetes clusters that meet specific operational needs.

### Control plane deployment options

The control plane components can be deployed in several ways:

- Traditional deployment

  Control plane components run directly on dedicated machines or VMs, often managed as systemd services.

- Static Pods

  Control plane components are deployed as static Pods, managed by the kubelet on specific nodes. This is a common approach used by tools like kubeadm.

- Self-hosted

  The control plane runs as Pods within the Kubernetes cluster itself, managed by Deployments and StatefulSets or other Kubernetes primitives.

- Managed Kubernetes services

  Cloud providers often abstract away the control plane, managing its components as part of their service offering.

### Workload placement considerations

The placement of workloads, including the control plane components, can vary based on cluster size, performance requirements, and operational policies:

- In smaller or development clusters, control plane components and user workloads might run on the same nodes.
- Larger production clusters often dedicate specific nodes to control plane components, separating them from user workloads.
- Some organizations run critical add-ons or monitoring tools on control plane nodes.

### Cluster management tools

Tools like kubeadm, kops, and Kubespray offer different approaches to deploying and managing clusters, each with its own method of component layout and management.

The flexibility of Kubernetes architecture allows organizations to tailor their clusters to specific needs, balancing factors such as operational complexity, performance, and management overhead.

### Customization and extensibility

Kubernetes architecture allows for significant customization:

- Custom schedulers can be deployed to work alongside the default Kubernetes scheduler or to replace it entirely.
- API servers can be extended with CustomResourceDefinitions and API Aggregation.
- Cloud providers can integrate deeply with Kubernetes using the cloud-controller-manager.

The flexibility of Kubernetes architecture allows organizations to tailor their clusters to specific needs, balancing factors such as operational complexity, performance, and management overhead.

```
## 节点组件

节点组件在每个节点上运行，维护正在运行的 Pod 并提供 Kubernetes 运行时环境。

### kubelet

在集群中每个 [节点](https://kubernetes.io/docs/concepts/architecture/nodes/) 上运行的代理。它确保 [容器](https://kubernetes.io/docs/concepts/containers/) 在 [Pod](https://kubernetes.io/docs/concepts/workloads/pods/) 中运行。

[kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) 接收通过各种机制提供的一组 PodSpec，并确保这些 PodSpec 中描述的容器正常运行且健康。kubelet 不管理非 Kubernetes 创建的容器。

### kube-proxy（可选）

kube-proxy 是一个网络代理，运行在集群中的每个 [节点](https://kubernetes.io/docs/concepts/architecture/nodes/) 上，实现了 Kubernetes [服务](https://kubernetes.io/docs/concepts/services-networking/service/) 概念的一部分。

[kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) 维护节点上的网络规则。这些网络规则允许从集群内部或外部的网络会话与 Pod 进行网络通信。

如果存在操作系统数据包过滤层且该层可用，kube-proxy 会使用它。否则，kube-proxy 会自行转发流量。

如果您使用 [网络插件](https://kubernetes.io/docs/concepts/architecture/#network-plugins)，该插件本身实现了服务的数据包转发，并提供与 kube-proxy 等效的行为，则无需在集群中的节点上运行 kube-proxy。

### 容器运行时

容器运行时是 Kubernetes 有效运行容器的基础组件。它负责管理 Kubernetes 环境中容器的执行和生命周期。

Kubernetes 支持容器运行时，例如 [containerd](https://containerd.io/docs/)、[CRI-O](https://cri-o.io/#what-is-cri-o) 以及任何其他 [Kubernetes CRI（容器运行时接口）](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/container-runtime-interface.md) 的实现。

## 插件

插件使用 Kubernetes 资源（[DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset)、[Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) 等）来实现集群功能。由于这些插件提供的是集群级别的功能，因此插件的命名空间资源应位于 `kube-system` 命名空间内。

部分插件如下所述；有关可用插件的扩展列表，请参阅 [插件](https://kubernetes.io/docs/concepts/cluster-administration/addons/)。

### DNS

虽然其他插件并非严格要求，但所有 Kubernetes 集群都应该具有 [集群 DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)，因为许多示例都依赖于它。

集群 DNS 是您环境中其他 DNS 服务器之外的 DNS 服务器，它为 Kubernetes 服务提供 DNS 记录。

Kubernetes 启动的容器会自动将此 DNS 服务器包含在其 DNS 搜索中。

### Web UI（仪表板）

[仪表板](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/) 是一个通用的、基于 Web 的 Kubernetes 集群 UI。它允许用户管理和排查集群中运行的应用程序以及集群本身的故障。

### 容器资源监控

[容器资源监控](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-usage-monitoring/) 在中央数据库中记录有关容器的通用时间序列指标，并提供用于浏览这些数据的 UI。

### 集群级日志记录

[集群级日志记录](https://kubernetes.io/docs/concepts/cluster-administration/logging/) 机制负责将容器日志保存到具有搜索/浏览界面的中央日志存储中。

### 网络插件

[网络插件](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) 是实现容器网络接口 (CNI) 规范的软件组件。它们负责为 Pod 分配 IP 地址，并使它们能够在集群内相互通信。

## 架构变化

虽然 Kubernetes 的核心组件保持一致，但它们的部署和管理方式可能会有所不同。了解这些变化对于设计和维护满足特定运维需求的 Kubernetes 集群至关重要。

### 控制平面部署选项

控制平面组件可以通过多种方式部署：

- 传统部署

控制平面组件直接在专用机器或虚拟机上运行，​​通常作为 systemd 服务进行管理。

- 静态 Pod

控制平面组件部署为静态 Pod，由特定节点上的 kubelet 管理。这是工具常用的方法
```



## What's next

Learn more about the following:

- [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/) and [their communication](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/) with the control plane.
- Kubernetes [controllers](https://kubernetes.io/docs/concepts/architecture/controller/).
- [kube-scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/) which is the default scheduler for Kubernetes.
- Etcd's official [documentation](https://etcd.io/docs/).
- Several [container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) in Kubernetes.
- Integrating with cloud providers using [cloud-controller-manager](https://kubernetes.io/docs/concepts/architecture/cloud-controller/).
- [kubectl](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands) commands.