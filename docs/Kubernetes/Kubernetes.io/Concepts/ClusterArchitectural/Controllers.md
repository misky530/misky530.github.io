# Controllers

In robotics and automation, a *control loop* is a non-terminating loop that regulates the state of a system.

Here is one example of a control loop: a thermostat in a room.

When you set the temperature, that's telling the thermostat about your *desired state*. The actual room temperature is the *current state*. The thermostat acts to bring the current state closer to the desired state, by turning equipment on or off.

In Kubernetes, controllers are control loops that watch the state of your [cluster](https://kubernetes.io/docs/reference/glossary/?all=true#term-cluster), then make or request changes where needed. Each controller tries to move the current cluster state closer to the desired state.

```
# 控制器

在机器人和自动化领域，*控制循环*是一种调节系统状态的永不终止的循环。

以下是控制循环的一个例子：房间里的恒温器。

当你设置温度时，实际上是在告诉恒温器你的*期望状态*。实际的室温是*当前状态*。恒温器通过打开或关闭设备，使当前状态更接近期望状态。

在 Kubernetes 中，控制器是控制循环，它监视[集群](https://kubernetes.io/docs/reference/glossary/?all=true#term-cluster) 的状态，然后在需要时进行更改或请求更改。每个控制器都会尝试使当前集群状态更接近期望状态。
```

## Controller pattern

A controller tracks at least one Kubernetes resource type. These [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) have a spec field that represents the desired state. The controller(s) for that resource are responsible for making the current state come closer to that desired state.

The controller might carry the action out itself; more commonly, in Kubernetes, a controller will send messages to the [API server](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver) that have useful side effects. You'll see examples of this below.

### Control via API server

The [Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) controller is an example of a Kubernetes built-in controller. Built-in controllers manage state by interacting with the cluster API server.

Job is a Kubernetes resource that runs a [Pod](https://kubernetes.io/docs/concepts/workloads/pods/), or perhaps several Pods, to carry out a task and then stop.

(Once [scheduled](https://kubernetes.io/docs/concepts/scheduling-eviction/), Pod objects become part of the desired state for a kubelet).

When the Job controller sees a new task it makes sure that, somewhere in your cluster, the kubelets on a set of Nodes are running the right number of Pods to get the work done. The Job controller does not run any Pods or containers itself. Instead, the Job controller tells the API server to create or remove Pods. Other components in the [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) act on the new information (there are new Pods to schedule and run), and eventually the work is done.

After you create a new Job, the desired state is for that Job to be completed. The Job controller makes the current state for that Job be nearer to your desired state: creating Pods that do the work you wanted for that Job, so that the Job is closer to completion.

Controllers also update the objects that configure them. For example: once the work is done for a Job, the Job controller updates that Job object to mark it `Finished`.

(This is a bit like how some thermostats turn a light off to indicate that your room is now at the temperature you set).

```
## 控制器模式

控制器跟踪至少一种 Kubernetes 资源类型。这些[对象](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) 具有表示期望状态的 spec 字段。该资源的控制器负责使当前状态更接近期望状态。

控制器可能会自行执行操作；更常见的是，在 Kubernetes 中，控制器会向 [API 服务器](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver) 发送具有有用副作用的消息。您将在下方看到相关示例。

### 通过 API 服务器控制

[Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) 控制器是 Kubernetes 内置控制器的一个示例。内置控制器通过与集群 API 服务器交互来管理状态。

Job 是一种 Kubernetes 资源，它运行一个 [Pod](https://kubernetes.io/docs/concepts/workloads/pods/) 或多个 Pod 来执行任务，然后停止。

（一旦 [调度](https://kubernetes.io/docs/concepts/scheduling-eviction/)，Pod 对象就成为 kubelet 所需状态的一部分）。

当 Job 控制器发现新任务时，它会确保集群中某个节点上的 kubelet 运行着正确数量的 Pod 来完成工作。Job 控制器本身并不运行任何 Pod 或容器。相反，它会通知 API 服务器创建或移除 Pod。 [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 中的其他组件会根据新信息采取行动（有新的 Pod 需要调度和运行），最终完成工作。

创建新作业后，期望状态是该作业完成。作业控制器会将该作业的当前状态更接近您的期望状态：创建 Pod 来执行您期望的作业工作，从而使作业更接近完成状态。

控制器还会更新配置它们的对象。例如：作业工作完成后，作业控制器会更新该作业对象，将其标记为“完成”。

（这有点像某些恒温器会关闭灯，以指示您的房间温度已达到您设定的温度）。
```

### Direct control

In contrast with Job, some controllers need to make changes to things outside of your cluster.

For example, if you use a control loop to make sure there are enough [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/) in your cluster, then that controller needs something outside the current cluster to set up new Nodes when needed.

Controllers that interact with external state find their desired state from the API server, then communicate directly with an external system to bring the current state closer in line.

(There actually is a [controller](https://github.com/kubernetes/autoscaler/) that horizontally scales the nodes in your cluster.)

The important point here is that the controller makes some changes to bring about your desired state, and then reports the current state back to your cluster's API server. Other control loops can observe that reported data and take their own actions.

In the thermostat example, if the room is very cold then a different controller might also turn on a frost protection heater. With Kubernetes clusters, the control plane indirectly works with IP address management tools, storage services, cloud provider APIs, and other services by [extending Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/) to implement that.

## Desired versus current state

Kubernetes takes a cloud-native view of systems, and is able to handle constant change.

Your cluster could be changing at any point as work happens and control loops automatically fix failures. This means that, potentially, your cluster never reaches a stable state.

As long as the controllers for your cluster are running and able to make useful changes, it doesn't matter if the overall state is stable or not.

## Design

As a tenet of its design, Kubernetes uses lots of controllers that each manage a particular aspect of cluster state. Most commonly, a particular control loop (controller) uses one kind of resource as its desired state, and has a different kind of resource that it manages to make that desired state happen. For example, a controller for Jobs tracks Job objects (to discover new work) and Pod objects (to run the Jobs, and then to see when the work is finished). In this case something else creates the Jobs, whereas the Job controller creates Pods.

It's useful to have simple controllers rather than one, monolithic set of control loops that are interlinked. Controllers can fail, so Kubernetes is designed to allow for that.

#### Note:

There can be several controllers that create or update the same kind of object. Behind the scenes, Kubernetes controllers make sure that they only pay attention to the resources linked to their controlling resource.

For example, you can have Deployments and Jobs; these both create Pods. The Job controller does not delete the Pods that your Deployment created, because there is information ([labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels)) the controllers can use to tell those Pods apart.

## Ways of running controllers

Kubernetes comes with a set of built-in controllers that run inside the [kube-controller-manager](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/). These built-in controllers provide important core behaviors.

The Deployment controller and Job controller are examples of controllers that come as part of Kubernetes itself ("built-in" controllers). Kubernetes lets you run a resilient control plane, so that if any of the built-in controllers were to fail, another part of the control plane will take over the work.

You can find controllers that run outside the control plane, to extend Kubernetes. Or, if you want, you can write a new controller yourself. You can run your own controller as a set of Pods, or externally to Kubernetes. What fits best will depend on what that particular controller does.

```
### 直接控制

与 Job 不同，某些控制器需要对集群外部的内容进行更改。

例如，如果您使用控制循环来确保集群中有足够的 [节点](https://kubernetes.io/docs/concepts/architecture/nodes/)，那么该控制器需要当前集群外部的某些内容来在需要时设置新的节点。

与外部状态交互的控制器从 API 服务器获取其期望状态，然后直接与外部系统通信，使当前状态更接近期望状态。

（实际上，有一个 [控制器](https://github.com/kubernetes/autoscaler/) 可以水平扩展集群中的节点。）

这里需要注意的是，控制器会进行一些更改以实现期望状态，然后将当前状态报告给集群的 API 服务器。其他控制循环可以观察报告的数据并采取相应的措施。

以恒温器为例，如果房间非常冷，那么另一个控制器也可能会打开防冻加热器。在 Kubernetes 集群中，控制平面通过[扩展 Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/) 间接地与 IP 地址管理工具、存储服务、云提供商 API 和其他服务协作来实现这一点。

## 期望状态与当前状态

Kubernetes 采用云原生视角来看待系统，并且能够应对持续的变化。

随着工作的进行，您的集群可能会随时发生变化，控制循环会自动修复故障。这意味着，您的集群可能永远不会达到稳定状态。

只要集群的控制器正在运行并能够进行有用的更改，整体状态是否稳定就无关紧要。

## 设计

作为其设计的原则，Kubernetes 使用了许多控制器，每个控制器管理集群状态的特定方面。最常见的情况是，特定的控制循环（控制器）使用一种资源作为其期望状态，并管理另一种资源来实现该期望状态。例如，Job 控制器会跟踪 Job 对象（用于发现新任务）和 Pod 对象（用于运行 Job，并查看任务何时完成）。在这种情况下，Job 由其他组件创建，而 Job 控制器则创建 Pod。

使用简单的控制器比使用一组相互关联的、庞大的控制循环更为有效。控制器可能会失败，因此 Kubernetes 的设计考虑到了这一点。

#### 注意：

可以有多个控制器创建或更新同一种对象。在后台，Kubernetes 控制器会确保它们只关注与其控制资源关联的资源。

例如，您可以拥有 Deployment 和 Job；它们都会创建 Pod。 Job 控制器不会删除 Deployment 创建的 Pod，因为控制器可以使用标签 ([labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels)) 来区分这些 Pod。

## 运行控制器的方式

Kubernetes 内置了一组在 kube-controller-manager 中运行的内置控制器。这些内置控制器提供了重要的核心行为。

Deployment 控制器和 Job 控制器是 Kubernetes 本身自带的控制器（“内置”控制器）的示例。Kubernetes 允许您运行一个弹性控制平面，这样，如果任何内置控制器发生故障，控制平面的其他部分将接管工作。

您可以找到在控制平面之外运行的控制器来扩展 Kubernetes。或者，如果您愿意，也可以自己编写一个新的控制器。您可以将自己的控制器作为一组 Pod 运行，也可以将其运行在 Kubernetes 外部。哪种方式最合适取决于该控制器的具体功能。
```

