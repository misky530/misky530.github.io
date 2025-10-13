# Communication between Nodes and the Control Plane

This document catalogs the communication paths between the [API server](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver) and the Kubernetes [cluster](https://kubernetes.io/docs/reference/glossary/?all=true#term-cluster). The intent is to allow users to customize their installation to harden the network configuration such that the cluster can be run on an untrusted network (or on fully public IPs on a cloud provider).

```
本文档列出了 API 服务器和 Kubernetes 集群之间的通信路径。其目的是允许用户自定义安装以强化网络配置，使集群能够在不受信任的网络上（或在云提供商的完全公开 IP 上运行）运行。
```

## Node to Control Plane

Kubernetes has a "hub-and-spoke" API pattern. All API usage from nodes (or the pods they run) terminates at the API server. None of the other control plane components are designed to expose remote services. The API server is configured to listen for remote connections on a secure HTTPS port (typically 443) with one or more forms of client [authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/) enabled. One or more forms of [authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/) should be enabled, especially if [anonymous requests](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#anonymous-requests) or [service account tokens](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens) are allowed.

Nodes should be provisioned with the public root [certificate](https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/) for the cluster such that they can connect securely to the API server along with valid client credentials. A good approach is that the client credentials provided to the kubelet are in the form of a client certificate. See [kubelet TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/) for automated provisioning of kubelet client certificates.

[Pods](https://kubernetes.io/docs/concepts/workloads/pods/) that wish to connect to the API server can do so securely by leveraging a service account so that Kubernetes will automatically inject the public root certificate and a valid bearer token into the pod when it is instantiated. The `kubernetes` service (in `default` namespace) is configured with a virtual IP address that is redirected (via `kube-proxy`) to the HTTPS endpoint on the API server.

The control plane components also communicate with the API server over the secure port.

As a result, the default operating mode for connections from the nodes and pod running on the nodes to the control plane is secured by default and can run over untrusted and/or public networks.

## Control plane to node

There are two primary communication paths from the control plane (the API server) to the nodes. The first is from the API server to the [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet) process which runs on each node in the cluster. The second is from the API server to any node, pod, or service through the API server's *proxy* functionality.

### API server to kubelet

The connections from the API server to the kubelet are used for:

- Fetching logs for pods.
- Attaching (usually through `kubectl`) to running pods.
- Providing the kubelet's port-forwarding functionality.

These connections terminate at the kubelet's HTTPS endpoint. By default, the API server does not verify the kubelet's serving certificate, which makes the connection subject to man-in-the-middle attacks and **unsafe** to run over untrusted and/or public networks.

To verify this connection, use the `--kubelet-certificate-authority` flag to provide the API server with a root certificate bundle to use to verify the kubelet's serving certificate.

If that is not possible, use [SSH tunneling](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/#ssh-tunnels) between the API server and kubelet if required to avoid connecting over an untrusted or public network.

Finally, [Kubelet authentication and/or authorization](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/) should be enabled to secure the kubelet API.

```
## 节点到控制平面

Kubernetes 采用“中心辐射型” API 模式。所有来自节点（或其运行的 Pod）的 API 使用都终止于 API 服务器。其他控制平面组件均未设计用于公开远程服务。API 服务器配置为在安全的 HTTPS 端口（通常为 443）上监听远程连接，并启用一种或多种客户端身份验证。应启用一种或多种授权方式，尤其是在允许匿名请求或服务账户令牌的情况下。

应为节点配置集群的公共根证书，以便它们能够使用有效的客户端凭据安全地连接到 API 服务器。一个好的做法是，以客户端证书的形式向 kubelet 提供客户端凭据。请参阅 [kubelet TLS 引导](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)，了解如何自动配置 kubelet 客户端证书。

希望连接到 API 服务器的 [Pod](https://kubernetes.io/docs/concepts/workloads/pods/) 可以通过服务帐号安全地进行连接，这样 Kubernetes 就会在 Pod 实例化时自动将公共根证书和有效的持有者令牌注入其中。“kubernetes”服务（位于“default”命名空间中）配置了一个虚拟 IP 地址，该地址会通过“kube-proxy”重定向到 API 服务器上的 HTTPS 端点。

控制平面组件也通过安全端口与 API 服务器通信。

因此，从节点以及节点上运行的 Pod 到控制平面的连接默认操作模式是安全的，并且可以在不受信任的网络和/或公共网络上运行。

## 控制平面到节点

从控制平面（API 服务器）到节点的主要通信路径有两条。第一条是从 API 服务器到 [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet) 进程，该进程在集群中的每个节点上运行。第二条是从 API 服务器通过 API 服务器的 *代理* 功能到任何节点、Pod 或服务。

### API 服务器到 kubelet

从 API 服务器到 kubelet 的连接用于：

- 获取 Pod 的日志。
- 连接（通常通过 `kubectl`）到正在运行的 Pod。
- 提供 kubelet 的端口转发功能。

这些连接终止于 kubelet 的 HTTPS 端点。默认情况下，API 服务器不会验证 kubelet 的服务证书，这使得连接容易受到中间人攻击，并且在不受信任和/或公共网络上运行**不安全**。

要验证此连接，请使用 `--kubelet-certificate-authority` 标志为 API 服务器提供根证书包，用于验证 kubelet 的服务证书。

如果无法验证，请在 API 服务器和 kubelet 之间使用 [SSH 隧道](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/#ssh-tunnels)，以避免通过不受信任或公共网络进行连接。

最后，应启用 [Kubelet 身份验证和/或授权](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/) 来保护 kubelet API。
```

### API server to nodes, pods, and services

The connections from the API server to a node, pod, or service default to plain HTTP connections and are therefore neither authenticated nor encrypted. They can be run over a secure HTTPS connection by prefixing `https:` to the node, pod, or service name in the API URL, but they will not validate the certificate provided by the HTTPS endpoint nor provide client credentials. So while the connection will be encrypted, it will not provide any guarantees of integrity. These connections **are not currently safe** to run over untrusted or public networks.

### SSH tunnels

Kubernetes supports [SSH tunnels](https://www.ssh.com/academy/ssh/tunneling) to protect the control plane to nodes communication paths. In this configuration, the API server initiates an SSH tunnel to each node in the cluster (connecting to the SSH server listening on port 22) and passes all traffic destined for a kubelet, node, pod, or service through the tunnel. This tunnel ensures that the traffic is not exposed outside of the network in which the nodes are running.

#### Note:

SSH tunnels are currently deprecated, so you shouldn't opt to use them unless you know what you are doing. The [Konnectivity service](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/#konnectivity-service) is a replacement for this communication channel.

### Konnectivity service

**FEATURE STATE:** `Kubernetes v1.18 [beta]`

As a replacement to the SSH tunnels, the Konnectivity service provides TCP level proxy for the control plane to cluster communication. The Konnectivity service consists of two parts: the Konnectivity server in the control plane network and the Konnectivity agents in the nodes network. The Konnectivity agents initiate connections to the Konnectivity server and maintain the network connections. After enabling the Konnectivity service, all control plane to nodes traffic goes through these connections.

Follow the [Konnectivity service task](https://kubernetes.io/docs/tasks/extend-kubernetes/setup-konnectivity/) to set up the Konnectivity service in your cluster

```
### API 服务器到节点、Pod 和服务

API 服务器到节点、Pod 或服务的连接默认为纯 HTTP 连接，因此既不经过身份验证也不加密。它们可以通过在 API URL 中为节点、Pod 或服务名称添加前缀“https:”来通过安全的 HTTPS 连接运行，但它们不会验证 HTTPS 端点提供的证书，也不会提供客户端凭据。因此，虽然连接会被加密，但它无法提供任何完整性保证。这些连接**目前**在不受信任或公共网络上运行并不安全。

### SSH 隧道

Kubernetes 支持 [SSH 隧道](https://www.ssh.com/academy/ssh/tunneling) 来保护控制平面到节点的通信路径。在此配置中，API 服务器会启动到集群中每个节点的 SSH 隧道（连接到监听端口 22 的 SSH 服务器），并通过该隧道传输所有发往 kubelet、节点、Pod 或服务的流量。此隧道确保流量不会暴露在节点运行的网络之外。

#### 注意：

SSH 隧道目前已弃用，因此除非您知道自己在做什么，否则不应选择使用它们。[Konnectivity 服务](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/#konnectivity-service) 是此通信通道的替代方案。

### Konnectivity 服务

**功能状态**：`Kubernetes v1.18 [beta]`

作为 SSH 隧道的替代方案，Konnectivity 服务为控制平面到集群的通信提供 TCP 级代理。Konnectivity 服务由两部分组成：控制平面网络中的 Konnectivity 服务器和节点网络中的 Konnectivity 代理。Konnectivity 代理发起与 Konnectivity 服务器的连接并维护网络连接。启用 Konnectivity 服务后，所有控制平面到节点的流量都会通过这些连接。

请按照 [Konnectivity 服务任务](https://kubernetes.io/docs/tasks/extend-kubernetes/setup-konnectivity/) 在您的集群中设置 Konnectivity 服务
```

