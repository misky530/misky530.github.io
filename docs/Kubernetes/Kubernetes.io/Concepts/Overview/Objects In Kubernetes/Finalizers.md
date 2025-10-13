# Finalizers

Finalizers are namespaced keys that tell Kubernetes to wait until specific conditions are met before it fully deletes [resources](https://kubernetes.io/docs/reference/using-api/api-concepts/#standard-api-terminology) that are marked for deletion. Finalizers alert [controllers](https://kubernetes.io/docs/concepts/architecture/controller/) to clean up resources the deleted object owned.

When you tell Kubernetes to delete an object that has finalizers specified for it, the Kubernetes API marks the object for deletion by populating `.metadata.deletionTimestamp`, and returns a `202` status code (HTTP "Accepted"). The target object remains in a terminating state while the control plane, or other components, take the actions defined by the finalizers. After these actions are complete, the controller removes the relevant finalizers from the target object. When the `metadata.finalizers` field is empty, Kubernetes considers the deletion complete and deletes the object.

You can use finalizers to control [garbage collection](https://kubernetes.io/docs/concepts/architecture/garbage-collection/) of resources. For example, you can define a finalizer to clean up related [API resources](https://kubernetes.io/docs/reference/using-api/api-concepts/#standard-api-terminology) or infrastructure before the controller deletes the object being finalized.

You can use finalizers to control [garbage collection](https://kubernetes.io/docs/concepts/architecture/garbage-collection/) of [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) by alerting [controllers](https://kubernetes.io/docs/concepts/architecture/controller/) to perform specific cleanup tasks before deleting the target resource.

Finalizers don't usually specify the code to execute. Instead, they are typically lists of keys on a specific resource similar to annotations. Kubernetes specifies some finalizers automatically, but you can also specify your own.

```
# 终结器

终结器是命名空间中的键，用于指示 Kubernetes 等待特定条件满足后再完全删除标记为待删除的[资源](https://kubernetes.io/docs/reference/using-api/api-concepts/#standard-api-terminology)。终结器会通知[控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 清理已删除对象所拥有的资源。

当您指示 Kubernetes 删除已指定终结器的对象时，Kubernetes API 会通过填充 `.metadata.deletionTimestamp` 将该对象标记为待删除，并返回 `202` 状态码（HTTP“已接受”）。在控制平面或其他组件执行终结器定义的操作时，目标对象将保持终止状态。这些操作完成后，控制器将从目标对象中移除相关的终结器。当 `metadata.finalizers` 字段为空时，Kubernetes 认为删除操作已完成并删除该对象。

您可以使用 finalizer 来控制资源的垃圾回收。例如，您可以定义一个 finalizer，在控制器删除正在 finalized 的对象之前清理相关的 API 资源或基础设施。

您可以使用终结器来控制[对象](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects)的[垃圾收集](https://kubernetes.io/docs/concepts/architecture/garbage-collection/)，方法是在删除目标资源之前提醒[控制器](https://kubernetes.io/docs/concepts/architecture/controller/)执行特定的清理任务。

终结器通常不指定要执行的代码。相反，它们通常是特定资源上的键列表，类似于注解。Kubernetes 会自动指定一些终结器，但您也可以指定自己的终结器。
```

## How finalizers work

When you create a resource using a manifest file, you can specify finalizers in the `metadata.finalizers` field. When you attempt to delete the resource, the API server handling the delete request notices the values in the `finalizers` field and does the following:

- Modifies the object to add a `metadata.deletionTimestamp` field with the time you started the deletion.
- Prevents the object from being removed until all items are removed from its `metadata.finalizers` field
- Returns a `202` status code (HTTP "Accepted")

The controller managing that finalizer notices the update to the object setting the `metadata.deletionTimestamp`, indicating deletion of the object has been requested. The controller then attempts to satisfy the requirements of the finalizers specified for that resource. Each time a finalizer condition is satisfied, the controller removes that key from the resource's `finalizers` field. When the `finalizers` field is emptied, an object with a `deletionTimestamp` field set is automatically deleted. You can also use finalizers to prevent deletion of unmanaged resources.

A common example of a finalizer is `kubernetes.io/pv-protection`, which prevents accidental deletion of `PersistentVolume` objects. When a `PersistentVolume` object is in use by a Pod, Kubernetes adds the `pv-protection` finalizer. If you try to delete the `PersistentVolume`, it enters a `Terminating` status, but the controller can't delete it because the finalizer exists. When the Pod stops using the `PersistentVolume`, Kubernetes clears the `pv-protection` finalizer, and the controller deletes the volume.

#### Note:

- When you `DELETE` an object, Kubernetes adds the deletion timestamp for that object and then immediately starts to restrict changes to the `.metadata.finalizers` field for the object that is now pending deletion. You can remove existing finalizers (deleting an entry from the `finalizers` list) but you cannot add a new finalizer. You also cannot modify the `deletionTimestamp` for an object once it is set.
- After the deletion is requested, you can not resurrect this object. The only way is to delete it and make a new similar object.

#### Note:

Custom finalizer names **must** be publicly qualified finalizer names, such as `example.com/finalizer-name`. Kubernetes enforces this format; the API server rejects writes to objects where the change does not use qualified finalizer names for any custom finalizer.

```
## 终结器工作原理

使用清单文件创建资源时，您可以在 `metadata.finalizers` 字段中指定终结器。当您尝试删除资源时，处理删除请求的 API 服务器会注意到 `finalizers` 字段中的值，并执行以下操作：

- 修改对象，添加 `metadata.deletionTimestamp` 字段，其中包含您开始删除的时间。
- 阻止删除对象，直到其 `metadata.finalizers` 字段中的所有项都删除完毕。
- 返回 `202` 状态码（HTTP“已接受”）

管理该终结器的控制器会注意到对象 `metadata.deletionTimestamp` 设置的更新，这表示已请求删除该对象。然后，控制器会尝试满足为该资源指定的终结器的要求。每次满足终结器条件时，控制器都会从资源的 `finalizers` 字段中删除该键。当 `finalizers` 字段清空时，设置了 `deletionTimestamp` 字段的对象会被自动删除。您还可以使用 finalizer 来防止删除非托管资源。

finalizer 的一个常见示例是 `kubernetes.io/pv-protection`，它可以防止意外删除 `PersistentVolume` 对象。当 Pod 正在使用 `PersistentVolume` 对象时，Kubernetes 会添加 `pv-protection` finalizer。如果您尝试删除 `PersistentVolume`，它会进入 `Terminating` 状态，但由于 finalizer 已存在，控制器无法删除它。当 Pod 停止使用 `PersistentVolume` 时，Kubernetes 会清除 `pv-protection` finalizer，然后控制器会删除该卷。

#### 注意：

- 当您 `DELETE` 一个对象时，Kubernetes 会为该对象添加删除时间戳，然后立即开始限制对该待删除对象的 `.metadata.finalizers` 字段的更改。您可以移除现有的终结器（从 `finalizers` 列表中删除一个条目），但无法添加新的终结器。一旦设置了 `deletionTimestamp`，您也无法修改该对象的 `deletionTimestamp`。
- 请求删除后，您将无法恢复此对象。唯一的方法是删除它并创建一个新的类似对象。

#### 注意：

自定义终结器名称**必须**是公共限定的终结器名称，例如 `example.com/finalizer-name`。Kubernetes 强制执行此格式；API 服务器会拒绝对任何自定义终结器未使用限定终结器名称的对象进行写入。
```

## Owner references, labels, and finalizers

Like [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels), [owner references](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/) describe the relationships between objects in Kubernetes, but are used for a different purpose. When a [controller](https://kubernetes.io/docs/concepts/architecture/controller/) manages objects like Pods, it uses labels to track changes to groups of related objects. For example, when a [Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) creates one or more Pods, the Job controller applies labels to those pods and tracks changes to any Pods in the cluster with the same label.

The Job controller also adds *owner references* to those Pods, pointing at the Job that created the Pods. If you delete the Job while these Pods are running, Kubernetes uses the owner references (not labels) to determine which Pods in the cluster need cleanup.

Kubernetes also processes finalizers when it identifies owner references on a resource targeted for deletion.

In some situations, finalizers can block the deletion of dependent objects, which can cause the targeted owner object to remain for longer than expected without being fully deleted. In these situations, you should check finalizers and owner references on the target owner and dependent objects to troubleshoot the cause.

#### Note:

In cases where objects are stuck in a deleting state, avoid manually removing finalizers to allow deletion to continue. Finalizers are usually added to resources for a reason, so forcefully removing them can lead to issues in your cluster. This should only be done when the purpose of the finalizer is understood and is accomplished in another way (for example, manually cleaning up some dependent object).

```
## 所有者引用、标签和终结器

与 [标签](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels) 类似，[所有者引用](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/) 描述了 Kubernetes 中对象之间的关系，但用途不同。当 [控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 管理 Pod 等对象时，它会使用标签来跟踪相关对象组的变更。例如，当 [作业](https://kubernetes.io/docs/concepts/workloads/controllers/job/) 创建一个或多个 Pod 时，作业控制器会将标签应用于这些 Pod，并跟踪集群中具有相同标签的任何 Pod 的变更。

作业控制器还会向这些 Pod 添加 *所有者引用*，指向创建这些 Pod 的作业。如果您在这些 Pod 运行时删除作业，Kubernetes 会使用所有者引用（而非标签）来确定集群中哪些 Pod 需要清理。

Kubernetes 在识别待删除资源上的所有者引用时，也会处理终结器 (Finalizer)。

在某些情况下，终结器可能会阻止依赖对象的删除，这会导致目标所有者对象保留的时间比预期的要长，而无法完全删除。在这种情况下，您应该检查目标所有者和依赖对象上的终结器和所有者引用，以排查原因。

#### 注意：

如果对象卡在删除状态，请避免手动移除终结器以允许删除操作继续进行。终结器通常是出于某种原因添加到资源中的，因此强制移除它们可能会导致集群出现问题。只有在理解终结器的用途并以其他方式实现（例如，手动清理某些依赖对象）的情况下，才应执行此操作。
```

