# Overview

Kubernetes is a portable, extensible, open source platform for managing containerized workloads and services, that facilitates both declarative configuration and automation. It has a large, rapidly growing ecosystem. Kubernetes services, support, and tools are widely available.

This page is an overview of Kubernetes.

The name Kubernetes originates from Greek, meaning helmsman or pilot. K8s as an abbreviation results from counting the eight letters between the "K" and the "s". Google open-sourced the Kubernetes project in 2014. Kubernetes combines [over 15 years of Google's experience](https://kubernetes.io/blog/2015/04/borg-predecessor-to-kubernetes/) running production workloads at scale with best-of-breed ideas and practices from the community.

## Why you need Kubernetes and what it can do

Containers are a good way to bundle and run your applications. In a production environment, you need to manage the containers that run the applications and ensure that there is no downtime. For example, if a container goes down, another container needs to start. Wouldn't it be easier if this behavior was handled by a system?

```
容器是运行和绑定应用程序的好方法.在产品环境,你需要管理运行应用的容器并保证它们没有停机时间.比如,一个容器停止了,另外一个容器就会启动.还有比这些更容易的吗?如果让系统来处理这些行为.
```

That's how Kubernetes comes to the rescue! Kubernetes provides you with a framework to run distributed systems resiliently. It takes care of scaling and failover for your application, provides deployment patterns, and more. For example: Kubernetes can easily manage a canary deployment for your system.

```
Kubernetes就是这样来救援的.Kubernetes为您提供了一个弹性的运行分布式应用的框架,它为您的应用程序的扩展,故障转换,发布模式等等.比如,Kubernetes可以使用Canary发布来管理你的系统.
```

Kubernetes provides you with:

- **Service discovery and load balancing** Kubernetes can expose a container using the DNS name or using their own IP address. If traffic to a container is high, Kubernetes is able to load balance and distribute the network traffic so that the deployment is stable.

  ```
  服务发现和负载均衡,Kubernetes能使用DNS Name或者它们的IP来公开容器,如果容器流量过高,Kubernetes负载均衡和分配流量,以便部署稳定.
  ```

  

- **Storage orchestration** Kubernetes allows you to automatically mount a storage system of your choice, such as local storages, public cloud providers, and more.

  ```
  存储编排,Kubernetes允许你按照自己的意愿挂载存储系统,比如local storages, public colud providers, and more.
  ```

  

- **Automated rollouts and rollbacks** You can describe the desired state for your deployed containers using Kubernetes, and it can change the actual state to the desired state at a controlled rate. For example, you can automate Kubernetes to create new containers for your deployment, remove existing containers and adopt all their resources to the new container.

  ```
  你可以使用Kubernetes描述你期望的状态在你发布的容器中,它能以可控的比率(rate)将容器的实际状态更改为你期望的状态
  ```

  

- **Automatic bin packing** You provide Kubernetes with a cluster of nodes that it can use to run containerized tasks. You tell Kubernetes how much CPU and memory (RAM) each container needs. Kubernetes can fit containers onto your nodes to make the best use of your resources.

  ```
  你提供了Kubernetes nodes集群,它可以运行容器化任务,你告诉Kubernetes每个容器需要多少CPU和RAM, Kubernetes可以将容器适合到你的节点上,以充分使用资源.
  ```

  

- **Self-healing** Kubernetes restarts containers that fail, replaces containers, kills containers that don't respond to your user-defined health check, and doesn't advertise them to clients until they are ready to serve.

- **Secret and configuration management** Kubernetes lets you store and manage sensitive information, such as passwords, OAuth tokens, and SSH keys. You can deploy and update secrets and application configuration without rebuilding your container images, and without exposing secrets in your stack configuration.

- **Batch execution** In addition to services, Kubernetes can manage your batch and CI workloads, replacing containers that fail, if desired.

- **Horizontal scaling** Scale your application up and down with a simple command, with a UI, or automatically based on CPU usage.

- **IPv4/IPv6 dual-stack** Allocation of IPv4 and IPv6 addresses to Pods and Services

- **Designed for extensibility** Add features to your Kubernetes cluster without changing upstream source code