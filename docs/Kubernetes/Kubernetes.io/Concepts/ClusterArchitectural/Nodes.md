# Nodes

Kubernetes runs your [workload](https://kubernetes.io/docs/concepts/workloads/) by placing containers into Pods to run on *Nodes*. A node may be a virtual or physical machine, depending on the cluster. Each node is managed by the [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) and contains the services necessary to run [Pods](https://kubernetes.io/docs/concepts/workloads/pods/).

Typically you have several nodes in a cluster; in a learning or resource-limited environment, you might have only one node.

The [components](https://kubernetes.io/docs/concepts/architecture/#node-components) on a node include the [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet), a [container runtime](https://kubernetes.io/docs/setup/production-environment/container-runtimes), and the [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/).

```
Kubernetes 通过将容器放入 Pod 中并在 *节点* 上运行来运行您的 [工作负载](https://kubernetes.io/docs/concepts/workloads/)。节点可以是虚拟机或物理机，具体取决于集群。每个节点由 [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 管理，并包含运行 [Pod](https://kubernetes.io/docs/concepts/workloads/pods/) 所需的服务。

通常，一个集群中有多个节点；在学习或资源有限的环境中，您可能只有一个节点。

节点上的组件包括 kubelet、容器运行时和 kube-proxy。
```

## Management

There are two main ways to have Nodes added to the [API server](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver):

1. The kubelet on a node self-registers to the control plane
2. You (or another human user) manually add a Node object

After you create a Node [object](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects), or the kubelet on a node self-registers, the control plane checks whether the new Node object is valid. For example, if you try to create a Node from the following JSON manifest:

```json
{
  "kind": "Node",
  "apiVersion": "v1",
  "metadata": {
    "name": "10.240.79.157",
    "labels": {
      "name": "my-first-k8s-node"
    }
  }
}
```

Kubernetes creates a Node object internally (the representation). Kubernetes checks that a kubelet has registered to the API server that matches the `metadata.name` field of the Node. If the node is healthy (i.e. all necessary services are running), then it is eligible to run a Pod. Otherwise, that node is ignored for any cluster activity until it becomes healthy.

#### Note:

Kubernetes keeps the object for the invalid Node and continues checking to see whether it becomes healthy.

You, or a [controller](https://kubernetes.io/docs/concepts/architecture/controller/), must explicitly delete the Node object to stop that health checking.

The name of a Node object must be a valid [DNS subdomain name](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-subdomain-names).

### Node name uniqueness

The [name](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names) identifies a Node. Two Nodes cannot have the same name at the same time. Kubernetes also assumes that a resource with the same name is the same object. In case of a Node, it is implicitly assumed that an instance using the same name will have the same state (e.g. network settings, root disk contents) and attributes like node labels. This may lead to inconsistencies if an instance was modified without changing its name. If the Node needs to be replaced or updated significantly, the existing Node object needs to be removed from API server first and re-added after the update.

### Self-registration of Nodes

When the kubelet flag `--register-node` is true (the default), the kubelet will attempt to register itself with the API server. This is the preferred pattern, used by most distros.

For self-registration, the kubelet is started with the following options:

- `--kubeconfig` - Path to credentials to authenticate itself to the API server.

- `--cloud-provider` - How to talk to a [cloud provider](https://kubernetes.io/docs/reference/glossary/?all=true#term-cloud-provider) to read metadata about itself.

- `--register-node` - Automatically register with the API server.

- `--register-with-taints` - Register the node with the given list of [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) (comma separated `<key>=<value>:<effect>`).

  No-op if `register-node` is false.

- `--node-ip` - Optional comma-separated list of the IP addresses for the node. You can only specify a single address for each address family. For example, in a single-stack IPv4 cluster, you set this value to be the IPv4 address that the kubelet should use for the node. See [configure IPv4/IPv6 dual stack](https://kubernetes.io/docs/concepts/services-networking/dual-stack/#configure-ipv4-ipv6-dual-stack) for details of running a dual-stack cluster.

  If you don't provide this argument, the kubelet uses the node's default IPv4 address, if any; if the node has no IPv4 addresses then the kubelet uses the node's default IPv6 address.

- `--node-labels` - [Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels) to add when registering the node in the cluster (see label restrictions enforced by the [NodeRestriction admission plugin](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction)).

- `--node-status-update-frequency` - Specifies how often kubelet posts its node status to the API server.

When the [Node authorization mode](https://kubernetes.io/docs/reference/access-authn-authz/node/) and [NodeRestriction admission plugin](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) are enabled, kubelets are only authorized to create/modify their own Node resource.

#### Note:

As mentioned in the [Node name uniqueness](https://kubernetes.io/docs/concepts/architecture/nodes/#node-name-uniqueness) section, when Node configuration needs to be updated, it is a good practice to re-register the node with the API server. For example, if the kubelet is being restarted with a new set of `--node-labels`, but the same Node name is used, the change will not take effect, as labels are only set (or modified) upon Node registration with the API server.

Pods already scheduled on the Node may misbehave or cause issues if the Node configuration will be changed on kubelet restart. For example, already running Pod may be tainted against the new labels assigned to the Node, while other Pods, that are incompatible with that Pod will be scheduled based on this new label. Node re-registration ensures all Pods will be drained and properly re-scheduled.

```
### 节点自注册

当 kubelet 标志 `--register-node` 为 true（默认值）时，kubelet 将尝试向 API 服务器注册自身。这是大多数发行版使用的首选模式。

对于自注册，kubelet 使用以下选项启动：

- `--kubeconfig` - 用于向 API 服务器验证自身身份的凭证路径。

- `--cloud-provider` - 如何与[云提供商](https://kubernetes.io/docs/reference/glossary/?all=true#term-cloud-provider)通信以读取自身的元数据。

- `--register-node` - 自动向 API 服务器注册。

- `--register-with-taints` - 使用给定的 [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) 列表注册节点（以逗号分隔的 `<key>=<value>:<effect>`）。

如果 `register-node` 为 false，则为空操作。

- `--node-ip` - 可选，以逗号分隔的节点 IP 地址列表。每个地址族只能指定一个地址。例如，在单栈 IPv4 集群中，将此值设置为 kubelet 应为该节点使用的 IPv4 地址。有关运行双栈集群的详细信息，请参阅[配置 IPv4/IPv6 双栈](https://kubernetes.io/docs/concepts/services-networking/dual-stack/#configure-ipv4-ipv6-dual-stack)。

如果您未提供此参数，kubelet 将使用节点的默认 IPv4 地址（如果有）；如果节点没有 IPv4 地址，则 kubelet 将使用节点的默认 IPv6 地址。

- `--node-labels` - 在集群中注册节点时要添加的 [标签](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels)（请参阅由 [NodeRestriction 准入插件](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) 强制执行的标签限制）。

- `--node-status-update-frequency` - 指定 kubelet 将其节点状态发布到 API 服务器的频率。

启用 [节点授权模式](https://kubernetes.io/docs/reference/access-authn-authz/node/) 和 [节点限制准入插件](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) 后，kubelet 仅被授权创建/修改其自身的节点资源。

#### 注意：

如 [节点名称唯一性](https://kubernetes.io/docs/concepts/architecture/nodes/#node-name-uniqueness) 部分所述，当需要更新节点配置时，建议将节点重新注册到 API 服务器。例如，如果使用一组新的 `--node-labels` 重新启动 kubelet，但使用的节点名称相同，则更改将不会生效，因为标签仅在节点注册到 API 服务器时设置（或修改）。

如果在 kubelet 重启时更改节点配置，则已在节点上调度的 Pod 可能会出现异常或引发问题。例如，已在运行的 Pod 可能会因分配给该节点的新标签而被污染，而其他与该 Pod 不兼容的 Pod 将根据此新标签进行调度。节点重新注册可确保所有 Pod 都将被清空并正确地重新调度。
```

### Manual Node administration

You can create and modify Node objects using [kubectl](https://kubernetes.io/docs/reference/kubectl/).

When you want to create Node objects manually, set the kubelet flag `--register-node=false`.

You can modify Node objects regardless of the setting of `--register-node`. For example, you can set labels on an existing Node or mark it unschedulable.

You can set optional node role(s) for nodes by adding one or more `node-role.kubernetes.io/<role>: <role>` labels to the node where characters of `<role>` are limited by the [syntax](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set) rules for labels.

Kubernetes ignores the label value for node roles; by convention, you can set it to the same string you used for the node role in the label key.

You can use labels on Nodes in conjunction with node selectors on Pods to control scheduling. For example, you can constrain a Pod to only be eligible to run on a subset of the available nodes.

Marking a node as unschedulable prevents the scheduler from placing new pods onto that Node but does not affect existing Pods on the Node. This is useful as a preparatory step before a node reboot or other maintenance.

```
### 手动节点管理

您可以使用 [kubectl](https://kubernetes.io/docs/reference/kubectl/) 创建和修改节点对象。

如果您想手动创建节点对象，请设置 kubelet 标志 `--register-node=false`。

无论 `--register-node` 的设置如何，您都可以修改节点对象。例如，您可以在现有节点上设置标签，或将其标记为不可调度。

您可以通过向节点添加一个或多个 `node-role.kubernetes.io/<role>: <role>` 标签来为节点设置可选的节点角色，其中 `<role>` 的字符受标签的 [语法](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set) 规则的限制。

Kubernetes 会忽略节点角色的标签值；按照惯例，您可以将其设置为与标签键中节点角色相同的字符串。

您可以将节点上的标签与 Pod 上的节点选择器结合使用来控制调度。例如，您可以限制 Pod 只能在可用节点的子集上运行。

将节点标记为不可调度会阻止调度程序将新的 Pod 放置到该节点上，但不会影响该节点上现有的 Pod。这在节点重启或其他维护前的准备步骤中非常有用。
```

To mark a Node unschedulable, run:

```shell
kubectl cordon $NODENAME
```

See [Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/) for more details.

#### Note:

Pods that are part of a [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset) tolerate being run on an unschedulable Node. DaemonSets typically provide node-local services that should run on the Node even if it is being drained of workload applications.

## Node status

A Node's status contains the following information:

- [Addresses](https://kubernetes.io/docs/reference/node/node-status/#addresses)
- [Conditions](https://kubernetes.io/docs/reference/node/node-status/#condition)
- [Capacity and Allocatable](https://kubernetes.io/docs/reference/node/node-status/#capacity)
- [Info](https://kubernetes.io/docs/reference/node/node-status/#info)

You can use `kubectl` to view a Node's status and other details:

```shell
kubectl describe node <insert-node-name-here>
```

See [Node Status](https://kubernetes.io/docs/reference/node/node-status/) for more details.

## Node heartbeats

Heartbeats, sent by Kubernetes nodes, help your cluster determine the availability of each node, and to take action when failures are detected.

For nodes there are two forms of heartbeats:

- Updates to the [`.status`](https://kubernetes.io/docs/reference/node/node-status/) of a Node.
- [Lease](https://kubernetes.io/docs/concepts/architecture/leases/) objects within the `kube-node-lease` [namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces). Each Node has an associated Lease object.

## Node controller

The node [controller](https://kubernetes.io/docs/concepts/architecture/controller/) is a Kubernetes control plane component that manages various aspects of nodes.

The node controller has multiple roles in a node's life. The first is assigning a CIDR block to the node when it is registered (if CIDR assignment is turned on).

The second is keeping the node controller's internal list of nodes up to date with the cloud provider's list of available machines. When running in a cloud environment and whenever a node is unhealthy, the node controller asks the cloud provider if the VM for that node is still available. If not, the node controller deletes the node from its list of nodes.

The third is monitoring the nodes' health. The node controller is responsible for:

- In the case that a node becomes unreachable, updating the `Ready` condition in the Node's `.status` field. In this case the node controller sets the `Ready` condition to `Unknown`.
- If a node remains unreachable: triggering [API-initiated eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/) for all of the Pods on the unreachable node. By default, the node controller waits 5 minutes between marking the node as `Unknown` and submitting the first eviction request.

By default, the node controller checks the state of each node every 5 seconds. This period can be configured using the `--node-monitor-period` flag on the `kube-controller-manager` component.

```
节点[控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 是 Kubernetes 控制平面组件，用于管理节点的各个方面。

节点控制器在节点的生命周期中扮演多个角色。首先，在节点注册时为其分配 CIDR 块（如果已启用 CIDR 分配）。

其次，节点控制器会将节点控制器的内部节点列表与云提供商的可用机器列表保持同步。在云环境中运行时，如果某个节点状态不佳，节点控制器会询问云提供商该节点的虚拟机是否仍然可用。如果不可用，节点控制器会将该节点从其节点列表中删除。

第三，节点控制器负责监控节点的健康状况。

- 如果某个节点无法访问，则更新节点 `.status` 字段中的 `Ready` 状态。在这种情况下，节点控制器会将 `Ready` 状态设置为 `Unknown`。
- 如果某个节点仍然无法访问：触发 [API 发起的驱逐](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/)，驱逐该节点上的所有 Pod。默认情况下，节点控制器在将节点标记为“未知”和提交第一个驱逐请求之间会等待 5 分钟。

默认情况下，节点控制器每 5 秒检查一次每个节点的状态。此周期可以使用 `kube-controller-manager` 组件上的 `--node-monitor-period` 标志进行配置。
```

### Rate limits on eviction

In most cases, the node controller limits the eviction rate to `--node-eviction-rate` (default 0.1) per second, meaning it won't evict pods from more than 1 node per 10 seconds.

The node eviction behavior changes when a node in a given availability zone becomes unhealthy. The node controller checks what percentage of nodes in the zone are unhealthy (the `Ready` condition is `Unknown` or `False`) at the same time:

- If the fraction of unhealthy nodes is at least `--unhealthy-zone-threshold` (default 0.55), then the eviction rate is reduced.
- If the cluster is small (i.e. has less than or equal to `--large-cluster-size-threshold` nodes - default 50), then evictions are stopped.
- Otherwise, the eviction rate is reduced to `--secondary-node-eviction-rate` (default 0.01) per second.

The reason these policies are implemented per availability zone is because one availability zone might become partitioned from the control plane while the others remain connected. If your cluster does not span multiple cloud provider availability zones, then the eviction mechanism does not take per-zone unavailability into account.

A key reason for spreading your nodes across availability zones is so that the workload can be shifted to healthy zones when one entire zone goes down. Therefore, if all nodes in a zone are unhealthy, then the node controller evicts at the normal rate of `--node-eviction-rate`. The corner case is when all zones are completely unhealthy (none of the nodes in the cluster are healthy). In such a case, the node controller assumes that there is some problem with connectivity between the control plane and the nodes, and doesn't perform any evictions. (If there has been an outage and some nodes reappear, the node controller does evict pods from the remaining nodes that are unhealthy or unreachable).

The node controller is also responsible for evicting pods running on nodes with `NoExecute` taints, unless those pods tolerate that taint. The node controller also adds [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) corresponding to node problems like node unreachable or not ready. This means that the scheduler won't place Pods onto unhealthy nodes.

```
### 驱逐速率限制

在大多数情况下，节点控制器将驱逐速率限制为每秒 `--node-eviction-rate`（默认值为 0.1），这意味着每 10 秒不会从超过 1 个节点驱逐 Pod。

当给定可用区域中的节点变为不健康状态时，节点驱逐行为会发生变化。节点控制器会同时检查区域中不健康节点的百分比（“Ready”状态为“Unknown”或“False”）：

- 如果不健康节点的比例至少为 `--unhealthy-zone-threshold`（默认值为 0.55），则降低驱逐速率。
- 如果集群较小（即节点数小于或等于 `--large-cluster-size-threshold` - 默认值为 50），则停止驱逐。
- 否则，驱逐率将降低至每秒 `--secondary-node-eviction-rate`（默认值为 0.01）。

这些策略之所以按可用区实施，是因为一个可用区可能与控制平面隔离，而其他可用区仍保持连接。如果您的集群不跨多个云提供商可用区，则驱逐机制不会考虑每个可用区的不可用性。

将节点分布在可用区之间的一个关键原因是，当一个可用区整个宕机时，工作负载可以转移到健康的可用区。因此，如果某个可用区中的所有节点都不健康，则节点控制器将以正常的 `--node-eviction-rate` 速率驱逐节点。特殊情况是所有可用区都完全不健康（集群中所有节点都不健康）。在这种情况下，节点控制器会假定控制平面和节点之间的连接存在问题，并且不会执行任何驱逐操作。 （如果发生中断并且某些节点重新出现，节点控制器会从剩余的不健康或无法访问的节点中驱逐 Pod）。

节点控制器还负责驱逐在带有“NoExecute”污点的节点上运行的 Pod，除非这些 Pod 能够容忍该污点。节点控制器还会添加与节点问题（例如节点无法访问或未就绪）对应的[污点](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)。这意味着调度程序不会将 Pod 部署到不健康的节点上。
```

## Resource capacity tracking

Node objects track information about the Node's resource capacity: for example, the amount of memory available and the number of CPUs. Nodes that [self register](https://kubernetes.io/docs/concepts/architecture/nodes/#self-registration-of-nodes) report their capacity during registration. If you [manually](https://kubernetes.io/docs/concepts/architecture/nodes/#manual-node-administration) add a Node, then you need to set the node's capacity information when you add it.

The Kubernetes [scheduler](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/) ensures that there are enough resources for all the Pods on a Node. The scheduler checks that the sum of the requests of containers on the node is no greater than the node's capacity. That sum of requests includes all containers managed by the kubelet, but excludes any containers started directly by the container runtime, and also excludes any processes running outside of the kubelet's control.

#### Note:

If you want to explicitly reserve resources for non-Pod processes, see [reserve resources for system daemons](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/#system-reserved).

## Node topology

**FEATURE STATE:** `Kubernetes v1.27 [stable]` (enabled by default: true)

If you have enabled the `TopologyManager` [feature gate](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/), then the kubelet can use topology hints when making resource assignment decisions. See [Control Topology Management Policies on a Node](https://kubernetes.io/docs/tasks/administer-cluster/topology-manager/) for more information.

```
## 资源容量跟踪

节点对象跟踪节点资源容量的信息：例如，可用内存量和 CPU 数量。[自注册](https://kubernetes.io/docs/concepts/architecture/nodes/#self-registration-of-nodes) 的节点会在注册过程中报告其容量。如果您[手动](https://kubernetes.io/docs/concepts/architecture/nodes/#manual-node-administration) 添加节点，则需要在添加时设置节点的容量信息。

Kubernetes [调度程序](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/) 确保节点上的所有 Pod 都有足够的资源。调度程序会检查节点上所有容器的请求总数是否不超过节点的容量。该请求总数包含 kubelet 管理的所有容器，但不包括容器运行时直接启动的任何容器，也不包括任何在 kubelet 控制范围之外运行的进程。

#### 注意：

如果您想明确为非 Pod 进程预留资源，请参阅[为系统守护进程预留资源](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/#system-reserved)。

## 节点拓扑

**功能状态**：`Kubernetes v1.27 [stable]`（默认启用：true）

如果您已启用 `TopologyManager` [功能门控](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)，则 kubelet 可以在进行资源分配决策时使用拓扑提示。请参阅[控制节点上的拓扑管理策略](https://kubernetes.io/docs/tasks/administer-cluster/topology-manager/)了解更多信息。
```



## 