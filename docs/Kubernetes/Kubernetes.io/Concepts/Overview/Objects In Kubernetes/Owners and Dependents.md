# Owners and Dependents

In Kubernetes, some [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) are *owners* of other objects. For example, a [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/) is the owner of a set of Pods. These owned objects are *dependents* of their owner.

Ownership is different from the [labels and selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) mechanism that some resources also use. For example, consider a Service that creates `EndpointSlice` objects. The Service uses [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels) to allow the control plane to determine which `EndpointSlice` objects are used for that Service. In addition to the labels, each `EndpointSlice` that is managed on behalf of a Service has an owner reference. Owner references help different parts of Kubernetes avoid interfering with objects they don’t control.

```
# 所有者和依赖项

在 Kubernetes 中，某些[对象](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects)是其他对象的*所有者*。例如，[ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)是一组 Pod 的所有者。这些被拥有的对象是其所有者的*依赖项*。

所有权与某些资源也使用的[标签和选择器](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)机制不同。例如，考虑一个创建“EndpointSlice”对象的服务。服务使用标签 (labels) 允许控制平面确定哪些“EndpointSlice”对象用于该服务。除了标签之外，代表服务管理的每个“EndpointSlice”都有一个所有者引用 (owner reference)。所有者引用可以帮助 Kubernetes 的不同部分避免干扰不受其控制的对象。
```

## Owner references in object specifications

Dependent objects have a `metadata.ownerReferences` field that references their owner object. A valid owner reference consists of the object name and a [UID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names) within the same [namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces) as the dependent object. Kubernetes sets the value of this field automatically for objects that are dependents of other objects like ReplicaSets, DaemonSets, Deployments, Jobs and CronJobs, and ReplicationControllers. You can also configure these relationships manually by changing the value of this field. However, you usually don't need to and can allow Kubernetes to automatically manage the relationships.

Dependent objects also have an `ownerReferences.blockOwnerDeletion` field that takes a boolean value and controls whether specific dependents can block garbage collection from deleting their owner object. Kubernetes automatically sets this field to `true` if a [controller](https://kubernetes.io/docs/concepts/architecture/controller/) (for example, the Deployment controller) sets the value of the `metadata.ownerReferences` field. You can also set the value of the `blockOwnerDeletion` field manually to control which dependents block garbage collection.

A Kubernetes admission controller controls user access to change this field for dependent resources, based on the delete permissions of the owner. This control prevents unauthorized users from delaying owner object deletion.

#### Note:

Cross-namespace owner references are disallowed by design. Namespaced dependents can specify cluster-scoped or namespaced owners. A namespaced owner **must** exist in the same namespace as the dependent. If it does not, the owner reference is treated as absent, and the dependent is subject to deletion once all owners are verified absent.

Cluster-scoped dependents can only specify cluster-scoped owners. In v1.20+, if a cluster-scoped dependent specifies a namespaced kind as an owner, it is treated as having an unresolvable owner reference, and is not able to be garbage collected.

In v1.20+, if the garbage collector detects an invalid cross-namespace `ownerReference`, or a cluster-scoped dependent with an `ownerReference` referencing a namespaced kind, a warning Event with a reason of `OwnerRefInvalidNamespace` and an `involvedObject` of the invalid dependent is reported. You can check for that kind of Event by running `kubectl get events -A --field-selector=reason=OwnerRefInvalidNamespace`.

```
## 对象规范中的所有者引用

依赖对象具有一个 `metadata.ownerReferences` 字段，用于引用其所有者对象。有效的所有者引用由对象名称和与依赖对象位于同一命名空间内的 [UID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names) 组成。Kubernetes 会自动为依赖其他对象（例如 ReplicaSet、DaemonSet、Deployment、Jobs、CronJobs 和 ReplicationController）的对象设置此字段的值。您也可以通过更改此字段的值来手动配置这些关系。但是，通常您不需要这样做，您可以让 Kubernetes 自动管理这些关系。

依赖对象还具有一个 `ownerReferences.blockOwnerDeletion` 字段，该字段接受一个布尔值，用于控制特定依赖对象是否可以阻止垃圾回收删除其所有者对象。如果某个[控制器](https://kubernetes.io/docs/concepts/architecture/controller/)（例如，Deployment 控制器）设置了 `metadata.ownerReferences` 字段的值，Kubernetes 会自动将此字段设置为 `true`。您也可以手动设置 `blockOwnerDeletion` 字段的值，以控制哪些依赖对象阻止垃圾回收。

Kubernetes 准入控制器根据所有者的删除权限，控制用户更改依赖资源此字段的权限。此控制可防止未经授权的用户延迟所有者对象的删除。

#### 注意：

跨命名空间的所有者引用在设计上是不允许的。命名空间内的依赖对象可以指定集群范围或命名空间内的所有者。命名空间内的所有者**必须**与依赖对象位于同一命名空间中。如果不存在，则所有者引用将被视为缺失，一旦所有所有者均被验证缺失，依赖项将被删除。

集群范围的依赖项只能指定集群范围的所有者。在 v1.20+ 版本中，如果集群范围的依赖项指定命名空间类型作为所有者，则该依赖项将被视为具有无法解析的所有者引用，并且无法被垃圾回收。

在 v1.20+ 版本中，如果垃圾回收器检测到无效的跨命名空间 `ownerReference`，或检测到集群范围的依赖项的 `ownerReference` 引用了命名空间类型，则会报告一个警告事件，其原因为 `OwnerRefInvalidNamespace`，并包含无效依赖项的 `involvedObject`。您可以通过运行 `kubectl get events -A --field-selector=reason=OwnerRefInvalidNamespace` 来检查此类事件。
```

## Ownership and finalizers

When you tell Kubernetes to delete a resource, the API server allows the managing controller to process any [finalizer rules](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/) for the resource. [Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/) prevent accidental deletion of resources your cluster may still need to function correctly. For example, if you try to delete a [PersistentVolume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) that is still in use by a Pod, the deletion does not happen immediately because the `PersistentVolume` has the `kubernetes.io/pv-protection` finalizer on it. Instead, the [volume](https://kubernetes.io/docs/concepts/storage/volumes/) remains in the `Terminating` status until Kubernetes clears the finalizer, which only happens after the `PersistentVolume` is no longer bound to a Pod.

Kubernetes also adds finalizers to an owner resource when you use either [foreground or orphan cascading deletion](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#cascading-deletion). In foreground deletion, it adds the `foreground` finalizer so that the controller must delete dependent resources that also have `ownerReferences.blockOwnerDeletion=true` before it deletes the owner. If you specify an orphan deletion policy, Kubernetes adds the `orphan` finalizer so that the controller ignores dependent resources after it deletes the owner object.

```
## 所有权和终结器

当您指示 Kubernetes 删除某个资源时，API 服务器会允许管理控制器处理该资源的任何 [终结器规则](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/)。[终结器](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/) 可防止意外删除集群可能仍需正常运行的资源。例如，如果您尝试删除仍在被 Pod 使用的 [持久卷](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)，则删除操作不会立即执行，因为该“持久卷”上已设置了“kubernetes.io/pv-protection”终结器。相反，[卷](https://kubernetes.io/docs/concepts/storage/volumes/) 会一直处于“Terminating”状态，直到 Kubernetes 清除终结器（这仅在“PersistentVolume”不再绑定到 Pod 后才会发生）。

当您使用[前台或孤立级联删除](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#cascading-deletion) 时，Kubernetes 也会向所有者资源添加终结器。在前台删除中，它会添加“前台”终结器，以便控制器在删除所有者之前必须删除同样具有“ownerReferences.blockOwnerDeletion”的依赖资源。如果您指定了孤立删除策略，Kubernetes 会添加“orphan”终结器，以便控制器在删除所有者对象后忽略依赖资源。
```

