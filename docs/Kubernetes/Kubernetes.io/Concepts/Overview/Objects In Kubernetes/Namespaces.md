# Namespaces

In Kubernetes, *namespaces* provide a mechanism for isolating groups of resources within a single cluster. Names of resources need to be unique within a namespace, but not across namespaces. Namespace-based scoping is applicable only for namespaced [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) *(e.g. Deployments, Services, etc.)* and not for cluster-wide objects *(e.g. StorageClass, Nodes, PersistentVolumes, etc.)*.

```
在Kubernetes,namespace提供了一个机制在单个集群中用来隔离资源组.资源的名称必须是唯一的.资源组的名称在namespace内必须是唯一的,但跨命令空间则不需要.基于Namespace的作用域仅用于命名空间内(比如deployment,service等),不适用于对于集群范围内(如,stroageClass,nodes,PVC等)
```

## When to Use Multiple Namespaces

Namespaces are intended for use in environments with many users spread across multiple teams, or projects. For clusters with a few to tens of users, you should not need to create or think about namespaces at all. Start using namespaces when you need the features they provide.

Namespaces provide a scope for names. Names of resources need to be unique within a namespace, but not across namespaces. Namespaces cannot be nested inside one another and each Kubernetes resource can only be in one namespace.

Namespaces are a way to divide cluster resources between multiple users (via [resource quota](https://kubernetes.io/docs/concepts/policy/resource-quotas/)).

It is not necessary to use multiple namespaces to separate slightly different resources, such as different versions of the same software: use [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels) to distinguish resources within the same namespace.

#### Note:

For a production cluster, consider *not* using the `default` namespace. Instead, make other namespaces and use those.

```
什么时候使用多命名空间?
命名空间适用于用户众多,分布在多个不同的团队和项目中.集群中的几个或者几十个用户, 你完全不需要创建或者考虑命令空间.当你真正需要命令空间的功能时,请开始使用它.
命名空间提供了一个名称作用域, 资源的名称在命令空间内必须是唯一的,但跨命令空间可以不同,命令空间不能嵌套,每一个Kubernetes资源只能在一个命名空间内.
命名空间是一个不同的用户间划分资源的方法(通过资源配额)
没有必要使用多个命名空间来区分略有不同的资源, 比如应用程序的不同的版本,使用label区分资源在同一命名空间内.

Note:
在产品集群中,请不要使用default命名空间, 请使用其他的命令空间来代替.


```

## Initial namespaces

Kubernetes starts with four initial namespaces:

- `default`

  Kubernetes includes this namespace so that you can start using your new cluster without first creating a namespace.

- `kube-node-lease`

  This namespace holds [Lease](https://kubernetes.io/docs/concepts/architecture/leases/) objects associated with each node. Node leases allow the kubelet to send [heartbeats](https://kubernetes.io/docs/concepts/architecture/nodes/#node-heartbeats) so that the control plane can detect node failure.

- `kube-public`

  This namespace is readable by *all* clients (including those not authenticated). This namespace is mostly reserved for cluster usage, in case that some resources should be visible and readable publicly throughout the whole cluster. The public aspect of this namespace is only a convention, not a requirement.

- `kube-system`

  The namespace for objects created by the Kubernetes system.

```
Kubernetes 初始时有四个命名空间：

- `default`

Kubernetes 包含此命名空间，以便您无需先创建命名空间即可开始使用新集群。

- `kube-node-lease`

此命名空间包含与每个节点关联的 [Lease] 对象。节点租约允许 kubelet 发送 [心跳]，以便控制平面能够检测到节点故障。

- `kube-public`

此命名空间可供*所有*客户端（包括未经身份验证的客户端）读取。此命名空间主要用于集群使用，以防某些资源需要在整个集群范围内公开可见且可读。此命名空间的公开性只是一种约定，而非强制要求。

- `kube-system`

Kubernetes 系统创建的对象的命名空间。
```

## Working with Namespaces

Creation and deletion of namespaces are described in the [Admin Guide documentation for namespaces](https://kubernetes.io/docs/tasks/administer-cluster/namespaces/).

#### Note:

Avoid creating namespaces with the prefix `kube-`, since it is reserved for Kubernetes system namespaces.

### Viewing namespaces

You can list the current namespaces in a cluster using:

```shell
kubectl get namespace
NAME              STATUS   AGE
default           Active   1d
kube-node-lease   Active   1d
kube-public       Active   1d
kube-system       Active   1d
```

### Setting the namespace for a request

To set the namespace for a current request, use the `--namespace` flag.

For example:

```shell
kubectl run nginx --image=nginx --namespace=<insert-namespace-name-here>
kubectl get pods --namespace=<insert-namespace-name-here>
```

### Setting the namespace preference

You can permanently save the namespace for all subsequent kubectl commands in that context.

```shell
kubectl config set-context --current --namespace=<insert-namespace-name-here>
# Validate it
kubectl config view --minify | grep namespace:
```

## Namespaces and DNS

When you create a [Service](https://kubernetes.io/docs/concepts/services-networking/service/), it creates a corresponding [DNS entry](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/). This entry is of the form `<service-name>.<namespace-name>.svc.cluster.local`, which means that if a container only uses `<service-name>`, it will resolve to the service which is local to a namespace. This is useful for using the same configuration across multiple namespaces such as Development, Staging and Production. If you want to reach across namespaces, you need to use the fully qualified domain name (FQDN).

As a result, all namespace names must be valid [RFC 1123 DNS labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names).

#### Warning:

By creating namespaces with the same name as [public top-level domains](https://data.iana.org/TLD/tlds-alpha-by-domain.txt), Services in these namespaces can have short DNS names that overlap with public DNS records. Workloads from any namespace performing a DNS lookup without a [trailing dot](https://datatracker.ietf.org/doc/html/rfc1034#page-8) will be redirected to those services, taking precedence over public DNS.

To mitigate this, limit privileges for creating namespaces to trusted users. If required, you could additionally configure third-party security controls, such as [admission webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/), to block creating any namespace with the name of [public TLDs](https://data.iana.org/TLD/tlds-alpha-by-domain.txt).

```
## 命名空间和 DNS

创建 [服务](https://kubernetes.io/docs/concepts/services-networking/service/) 时，它会创建一个相应的 [DNS 条目](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)。此条目的格式为 `<service-name>.<namespace-name>.svc.cluster.local`，这意味着如果容器仅使用 `<service-name>`，它将解析到命名空间本地的服务。这对于在多个命名空间（例如开发、预发布和生产）中使用相同的配置非常有用。如果要跨命名空间访问，则需要使用完全限定域名 (FQDN)。

因此，所有命名空间名称都必须是有效的 [RFC 1123 DNS 标签](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names)。

#### 警告：

通过创建与 [公共顶级域名](https://data.iana.org/TLD/tlds-alpha-by-domain.txt) 同名的命名空间，这些命名空间中的服务可能会使用与公共 DNS 记录重叠的短 DNS 名称。任何执行不带 [尾随点](https://datatracker.ietf.org/doc/html/rfc1034#page-8) DNS 查找的命名空间中的工作负载都将被重定向到这些服务，并优先于公共 DNS。

为了缓解此问题，请将创建命名空间的权限限制为受信任用户。如果需要，您还可以配置第三方安全控制，例如 [admission webhook](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)，以阻止创建任何名为 [公共 TLD](https://data.iana.org/TLD/tlds-alpha-by-domain.txt) 的命名空间。
```



## Not all objects are in a namespace

Most Kubernetes resources (e.g. pods, services, replication controllers, and others) are in some namespaces. However namespace resources are not themselves in a namespace. And low-level resources, such as [nodes](https://kubernetes.io/docs/concepts/architecture/nodes/) and [persistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/), are not in any namespace.

To see which Kubernetes resources are and aren't in a namespace:

```shell
# In a namespace
kubectl api-resources --namespaced=true

# Not in a namespace
kubectl api-resources --namespaced=false
```

## Automatic labelling

**FEATURE STATE:** `Kubernetes 1.22 [stable]`

The Kubernetes control plane sets an immutable [label](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels) `kubernetes.io/metadata.name` on all namespaces. The value of the label is the namespace name