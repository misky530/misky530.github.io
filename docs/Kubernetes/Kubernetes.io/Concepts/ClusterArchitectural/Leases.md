# Leases

Distributed systems often have a need for *leases*, which provide a mechanism to lock shared resources and coordinate activity between members of a set. In Kubernetes, the lease concept is represented by [Lease](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/) objects in the `coordination.k8s.io` [API Group](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#api-groups-and-versioning), which are used for system-critical capabilities such as node heartbeats and component-level leader election.

## Node heartbeats

Kubernetes uses the Lease API to communicate kubelet node heartbeats to the Kubernetes API server. For every `Node` , there is a `Lease` object with a matching name in the `kube-node-lease` namespace. Under the hood, every kubelet heartbeat is an **update** request to this `Lease` object, updating the `spec.renewTime` field for the Lease. The Kubernetes control plane uses the time stamp of this field to determine the availability of this `Node`.

See [Node Lease objects](https://kubernetes.io/docs/concepts/architecture/nodes/#node-heartbeats) for more details.

## Leader election

Kubernetes also uses Leases to ensure only one instance of a component is running at any given time. This is used by control plane components like `kube-controller-manager` and `kube-scheduler` in HA configurations, where only one instance of the component should be actively running while the other instances are on stand-by.

Read [coordinated leader election](https://kubernetes.io/docs/concepts/cluster-administration/coordinated-leader-election/) to learn about how Kubernetes builds on the Lease API to select which component instance acts as leader.

## API server identity

**FEATURE STATE:** `Kubernetes v1.26 [beta]` (enabled by default: true)

Starting in Kubernetes v1.26, each `kube-apiserver` uses the Lease API to publish its identity to the rest of the system. While not particularly useful on its own, this provides a mechanism for clients to discover how many instances of `kube-apiserver` are operating the Kubernetes control plane. Existence of kube-apiserver leases enables future capabilities that may require coordination between each kube-apiserver.

You can inspect Leases owned by each kube-apiserver by checking for lease objects in the `kube-system` namespace with the name `apiserver-<sha256-hash>`. Alternatively you can use the label selector `apiserver.kubernetes.io/identity=kube-apiserver`:

```
# 租约

分布式系统通常需要使用“租约”，它提供了一种锁定共享资源并协调集合成员之间活动的机制。在 Kubernetes 中，租约概念由 `coordination.k8s.io` [API 组](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#api-groups-and-versioning) 中的 [Lease](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/) 对象表示，这些对象用于系统关键功能，例如节点心跳和组件级领导者选举。

## 节点心跳

Kubernetes 使用 Lease API 将 kubelet 节点心跳传递给 Kubernetes API 服务器。对于每个 `Node`，在 `kube-node-lease` 命名空间中都有一个名称匹配的 `Lease` 对象。本质上，每个 kubelet 心跳都是对此“Lease”对象的**更新**请求，用于更新该“Lease”的“spec.renewTime”字段。Kubernetes 控制平面使用此字段的时间戳来确定此“Node”的可用性。

更多详细信息，请参阅[Node Lease 对象](https://kubernetes.io/docs/concepts/architecture/nodes/#node-heartbeats)。

## 领导者选举

Kubernetes 还使用 Lease 来确保组件在任何给定时间只有一个实例处于运行状态。这在 HA 配置中被控制平面组件（例如“kube-controller-manager”和“kube-scheduler”）使用，在这些配置中，组件只有一个实例应该处于活动运行状态，而其他实例处于待命状态。

阅读[协调领导者选举](https://kubernetes.io/docs/concepts/cluster-administration/coordinated-leader-election/)，了解 Kubernetes 如何基于 Lease API 来选择哪个组件实例作为领导者。

## API 服务器身份

**功能状态**：`Kubernetes v1.26 [beta]`（默认启用：true）

从 Kubernetes v1.26 开始，每个 `kube-apiserver` 都使用 Lease API 将其身份发布到系统的其余部分。虽然这本身并不特别有用，但它为客户端提供了一种机制，可以发现有多少个 `kube-apiserver` 实例正在操作 Kubernetes 控制平面。kube-apiserver 租约的存在使未来可能需要每个 kube-apiserver 之间进行协调的功能成为可能。

您可以通过检查 `kube-system` 命名空间中名为 `apiserver-<sha256-hash>` 的租约对象来检查每个 kube-apiserver 拥有的租约。或者，您也可以使用标签选择器 `apiserver.kubernetes.io/identity=kube-apiserver`：
```



```shell
kubectl -n kube-system get lease -l apiserver.kubernetes.io/identity=kube-apiserver
NAME                                        HOLDER                                                                           AGE
apiserver-07a5ea9b9b072c4a5f3d1c3702        apiserver-07a5ea9b9b072c4a5f3d1c3702_0c8914f7-0f35-440e-8676-7844977d3a05        5m33s
apiserver-7be9e061c59d368b3ddaf1376e        apiserver-7be9e061c59d368b3ddaf1376e_84f2a85d-37c1-4b14-b6b9-603e62e4896f        4m23s
apiserver-1dfef752bcb36637d2763d1868        apiserver-1dfef752bcb36637d2763d1868_c5ffa286-8a9a-45d4-91e7-61118ed58d2e        4m43s
```

The SHA256 hash used in the lease name is based on the OS hostname as seen by that API server. Each kube-apiserver should be configured to use a hostname that is unique within the cluster. New instances of kube-apiserver that use the same hostname will take over existing Leases using a new holder identity, as opposed to instantiating new Lease objects. You can check the hostname used by kube-apiserver by checking the value of the `kubernetes.io/hostname` label:

```shell
kubectl -n kube-system get lease apiserver-07a5ea9b9b072c4a5f3d1c3702 -o yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  creationTimestamp: "2023-07-02T13:16:48Z"
  labels:
    apiserver.kubernetes.io/identity: kube-apiserver
    kubernetes.io/hostname: master-1
  name: apiserver-07a5ea9b9b072c4a5f3d1c3702
  namespace: kube-system
  resourceVersion: "334899"
  uid: 90870ab5-1ba9-4523-b215-e4d4e662acb1
spec:
  holderIdentity: apiserver-07a5ea9b9b072c4a5f3d1c3702_0c8914f7-0f35-440e-8676-7844977d3a05
  leaseDurationSeconds: 3600
  renewTime: "2023-07-04T21:58:48.065888Z"
```

Expired leases from kube-apiservers that no longer exist are garbage collected by new kube-apiservers after 1 hour.

You can disable API server identity leases by disabling the `APIServerIdentity` [feature gate](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/).

## Workloads

Your own workload can define its own use of Leases. For example, you might run a custom [controller](https://kubernetes.io/docs/concepts/architecture/controller/) where a primary or leader member performs operations that its peers do not. You define a Lease so that the controller replicas can select or elect a leader, using the Kubernetes API for coordination. If you do use a Lease, it's a good practice to define a name for the Lease that is obviously linked to the product or component. For example, if you have a component named Example Foo, use a Lease named `example-foo`.

If a cluster operator or another end user could deploy multiple instances of a component, select a name prefix and pick a mechanism (such as hash of the name of the Deployment) to avoid name collisions for the Leases.

You can use another approach so long as it achieves the same outcome: different software products do not conflict with one another.

```
kube-apiserver 中已过期且不再存在的租约将在 1 小时后被新的 kube-apiserver 垃圾回收。

您可以通过禁用 `APIServerIdentity` [功能门控](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/) 来禁用 API 服务器身份租约。

## 工作负载

您自己的工作负载可以定义其对租约的使用。例如，您可以运行一个自定义[控制器](https://kubernetes.io/docs/concepts/architecture/controller/)，其中主成员或领导成员执行其对等成员不执行的操作。您可以定义租约，以便控制器副本可以使用 Kubernetes API 进行协调来选择或选举领导成员。如果您确实使用租约，最好为租约定义一个与产品或组件明显关联的名称。例如，如果您有一个名为 Example Foo 的组件，请使用名为“example-foo”的租约。

如果集群运维人员或其他最终用户可以部署某个组件的多个实例，请选择一个名称前缀并选择一种机制（例如 Deployment 名称的哈希值）来避免租约的名称冲突。

您可以使用其他方法，只要它能达到相同的效果：不同的软件产品不会相互冲突。
```

