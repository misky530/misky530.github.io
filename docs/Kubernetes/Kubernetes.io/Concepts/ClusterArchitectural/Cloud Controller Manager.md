# Cloud Controller Manager

**FEATURE STATE:** `Kubernetes v1.11 [beta]`

Cloud infrastructure technologies let you run Kubernetes on public, private, and hybrid clouds. Kubernetes believes in automated, API-driven infrastructure without tight coupling between components.

The cloud-controller-manager is a Kubernetes [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) component that embeds cloud-specific control logic. The cloud controller manager lets you link your cluster into your cloud provider's API, and separates out the components that interact with that cloud platform from components that only interact with your cluster.

By decoupling the interoperability logic between Kubernetes and the underlying cloud infrastructure, the cloud-controller-manager component enables cloud providers to release features at a different pace compared to the main Kubernetes project.

The cloud-controller-manager is structured using a plugin mechanism that allows different cloud providers to integrate their platforms with Kubernetes.

```
云基础设施技术让您可以在公有云、私有云和混合云上运行 Kubernetes。Kubernetes 秉承自动化、API 驱动的基础设施理念，避免组件之间紧密耦合。

云控制器管理器是一个 Kubernetes [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 组件，它嵌入了特定于云的控制逻辑。云控制器管理器允许您将集群链接到云提供商的 API，并将与该云平台交互的组件与仅与您的集群交互的组件分离。

通过解耦 Kubernetes 与底层云基础设施之间的互操作性逻辑，云控制器管理器组件使云提供商能够以不同于主 Kubernetes 项目的速度发布功能。

云控制器管理器采用插件机制构建，允许不同的云提供商将其平台与 Kubernetes 集成。
```

## Design

![Kubernetes components](https://kubernetes.io/images/docs/components-of-kubernetes.svg)

The cloud controller manager runs in the control plane as a replicated set of processes (usually, these are containers in Pods). Each cloud-controller-manager implements multiple [controllers](https://kubernetes.io/docs/concepts/architecture/controller/) in a single process.

#### Note:

You can also run the cloud controller manager as a Kubernetes [addon](https://kubernetes.io/docs/concepts/cluster-administration/addons/) rather than as part of the control plane.

## Cloud controller manager functions

The controllers inside the cloud controller manager include:

### Node controller

The node controller is responsible for updating [Node](https://kubernetes.io/docs/concepts/architecture/nodes/) objects when new servers are created in your cloud infrastructure. The node controller obtains information about the hosts running inside your tenancy with the cloud provider. The node controller performs the following functions:

1. Update a Node object with the corresponding server's unique identifier obtained from the cloud provider API.
2. Annotating and labelling the Node object with cloud-specific information, such as the region the node is deployed into and the resources (CPU, memory, etc) that it has available.
3. Obtain the node's hostname and network addresses.
4. Verifying the node's health. In case a node becomes unresponsive, this controller checks with your cloud provider's API to see if the server has been deactivated / deleted / terminated. If the node has been deleted from the cloud, the controller deletes the Node object from your Kubernetes cluster.

Some cloud provider implementations split this into a node controller and a separate node lifecycle controller.

### Route controller

The route controller is responsible for configuring routes in the cloud appropriately so that containers on different nodes in your Kubernetes cluster can communicate with each other.

Depending on the cloud provider, the route controller might also allocate blocks of IP addresses for the Pod network.

### Service controller

[Services](https://kubernetes.io/docs/concepts/services-networking/service/) integrate with cloud infrastructure components such as managed load balancers, IP addresses, network packet filtering, and target health checking. The service controller interacts with your cloud provider's APIs to set up load balancers and other infrastructure components when you declare a Service resource that requires them.

## Authorization

This section breaks down the access that the cloud controller manager requires on various API objects, in order to perform its operations.

### Node controller

The Node controller only works with Node objects. It requires full access to read and modify Node objects.

`v1/Node`:

- get
- list
- create
- update
- patch
- watch
- delete

### Route controller

The route controller listens to Node object creation and configures routes appropriately. It requires Get access to Node objects.

`v1/Node`:

- get

### Service controller

The service controller watches for Service object **create**, **update** and **delete** events and then configures load balancers for those Services appropriately.

To access Services, it requires **list**, and **watch** access. To update Services, it requires **patch** and **update** access to the `status` subresource.

`v1/Service`:

- list
- get
- watch
- patch
- update

### Others

The implementation of the core of the cloud controller manager requires access to create Event objects, and to ensure secure operation, it requires access to create ServiceAccounts.

`v1/Event`:

- create
- patch
- update

`v1/ServiceAccount`:

- create

The [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) ClusterRole for the cloud controller manager looks like:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cloud-controller-manager
rules:
- apiGroups:
  - ""
  resources:
  - events
  verbs:
  - create
  - patch
  - update
- apiGroups:
  - ""
  resources:
  - nodes
  verbs:
  - '*'
- apiGroups:
  - ""
  resources:
  - nodes/status
  verbs:
  - patch
- apiGroups:
  - ""
  resources:
  - services
  verbs:
  - list
  - watch
- apiGroups:
  - ""
  resources:
  - services/status
  verbs:
  - patch
  - update
- apiGroups:
  - ""
  resources:
  - serviceaccounts
  verbs:
  - create
- apiGroups:
  - ""
  resources:
  - persistentvolumes
  verbs:
  - get
  - list
  - update
  - watch
```

