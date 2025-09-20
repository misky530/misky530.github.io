# Kubernetes Components

An overview of the key components that make up a Kubernetes cluster.

This page provides a high-level overview of the essential components that make up a Kubernetes cluster.

```
Kubernetes集群的关键组件总览
本页从高层次概述了一个Kubernetes集群基本的组件
```

![components-of-kubernetes](assets/components-of-kubernetes.svg)

The components of a Kubernetes cluster

## Core Components

A Kubernetes cluster consists of a control plane and one or more worker nodes. Here's a brief overview of the main components:

```
一个Kubernetes集群的控制面板由一个控制面板和一个或者多个worker node组成， 下面是主要组件的总览摘要
```



### Control Plane Components

Manage the overall state of the cluster:

- [kube-apiserver](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver)

  The core component server that exposes the Kubernetes HTTP API.

- [etcd](https://kubernetes.io/docs/concepts/architecture/#etcd)

  Consistent and highly-available key value store for all API server data.

- [kube-scheduler](https://kubernetes.io/docs/concepts/architecture/#kube-scheduler)

  Looks for Pods not yet bound to a node, and assigns each Pod to a suitable node.

  ```
  查看未绑定到节点的Pods， 分配每个Pod到合适的节点
  ```

- [kube-controller-manager](https://kubernetes.io/docs/concepts/architecture/#kube-controller-manager)

  Runs [controllers](https://kubernetes.io/docs/concepts/architecture/controller/) to implement Kubernetes API behavior.

- [cloud-controller-manager](https://kubernetes.io/docs/concepts/architecture/#cloud-controller-manager) (optional)

  Integrates with underlying cloud provider(s).

  ```
  与底层云提供商集成
  ```

  

### Node Components

Run on every node, maintaining running pods and providing the Kubernetes runtime environment:

运行在每个节点 ，维护运行中的Pds和提供Kubernetes 运行时环境



- [kubelet](https://kubernetes.io/docs/concepts/architecture/#kubelet)

  Ensures that Pods are running, including their containers.

- [kube-proxy](https://kubernetes.io/docs/concepts/architecture/#kube-proxy) (optional)

  Maintains network rules on nodes to implement [Services](https://kubernetes.io/docs/concepts/services-networking/service/).

- [Container runtime](https://kubernetes.io/docs/concepts/architecture/#container-runtime)

  Software responsible for running containers. Read [Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) to learn more.

🛇 This item links to a third party project or product that is not part of Kubernetes itself. [More information](https://kubernetes.io/docs/concepts/overview/components/#third-party-content-disclaimer)

Your cluster may require additional software on each node; for example, you might also run [systemd](https://systemd.io/) on a Linux node to supervise local components.

## Addons

Addons extend the functionality of Kubernetes. A few important examples include:

```
插件扩展Kubernetes的功能， 下面是一些常用的重要插件
```

- [DNS](https://kubernetes.io/docs/concepts/architecture/#dns)

  For cluster-wide DNS resolution.

- [Web UI](https://kubernetes.io/docs/concepts/architecture/#web-ui-dashboard) (Dashboard)

  For cluster management via a web interface.

- [Container Resource Monitoring](https://kubernetes.io/docs/concepts/architecture/#container-resource-monitoring)

  For collecting and storing container metrics.

- [Cluster-level Logging](https://kubernetes.io/docs/concepts/architecture/#cluster-level-logging)

  For saving container logs to a central log store.

## Flexibility in Architecture

Kubernetes allows for flexibility in how these components are deployed and managed. The architecture can be adapted to various needs, from small development environments to large-scale production deployments.

For more detailed information about each component and various ways to configure your cluster architecture, see the [Cluster Architecture](https://kubernetes.io/docs/concepts/architecture/) page.

Items on this page refer to third party products or projects that provide functionality required by Kubernetes. The Kubernetes project authors aren't responsible for those third-party products or projects. See the [CNCF website guidelines](https://github.com/cncf/foundation/blob/master/website-guidelines.md) for more details.

You should read the [content guide](https://kubernetes.io/docs/contribute/style/content-guide/#third-party-content) before proposing a change that adds an extra third-party link.

```
Kubernetes允许灵活的管理和部署这些组件， 这个架构能满足各种需要， 从小的开发环境到大模型生产环境部署。
For more detailed information about each component and various ways to configure your cluster architecture, see the [Cluster Architecture](https://kubernetes.io/docs/concepts/architecture/) page.


```

