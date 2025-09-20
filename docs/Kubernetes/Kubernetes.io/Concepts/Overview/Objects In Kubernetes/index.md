# Objects In Kubernetes

Kubernetes objects are persistent entities in the Kubernetes system. Kubernetes uses these entities to represent the state of your cluster. Learn about the Kubernetes object model and how to work with these objects.

This page explains how Kubernetes objects are represented in the Kubernetes API, and how you can express them in `.yaml` format.

```
Kubernetes对象是Kubernetes系统中的持久化实体。Kubernetes使用这些实例可以表现系统的状态。学习/了解Kubernetes对象以及如何使用这些对象。
此页解释了Kubernetes对象在Kubernetes API中的表现形式和你如何快速的用.yaml来表示它们.
```

## Understanding Kubernetes objects

*Kubernetes objects* are persistent entities in the Kubernetes system. Kubernetes uses these entities to represent the state of your cluster. Specifically, they can describe:

- What containerized applications are running (and on which nodes)
- The resources available to those applications
- The policies around how those applications behave, such as restart policies, upgrades, and fault-tolerance

A Kubernetes object is a "record of intent"--once you create the object, the Kubernetes system will constantly work to ensure that the object exists. By creating an object, you're effectively telling the Kubernetes system what you want your cluster's workload to look like; this is your cluster's *desired state*.

To work with Kubernetes objects—whether to create, modify, or delete them—you'll need to use the [Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/). When you use the `kubectl` command-line interface, for example, the CLI makes the necessary Kubernetes API calls for you. You can also use the Kubernetes API directly in your own programs using one of the [Client Libraries](https://kubernetes.io/docs/reference/using-api/client-libraries/).

```
了解Kubernetes对象
Kubernetes对象都是Kubernetes系统中持久化的实体.Kubernetes集群中使用这这些实体来表现系统的状态,特别的,他们可以描述为
- 哪些容器化的应用程序在运行(在哪个节点上)
- 这些应用程序的可用资源
- 关于这些应用程序如何运行的策略, 比如重启策略,更新策略和容错

一个Kubernetes对象是"意向记录" -- 一旦你创建一个对象, Kubernetes系统将不断工作来保证这个对象存在.通过创建对象, 你将有效的告诉Kubernetes你期望的集群状态是什么样子的,这就是集群的期望状态
```

### Object spec and status

Almost every Kubernetes object includes two nested object fields that govern the object's configuration: the object *`spec`* and the object *`status`*. For objects that have a `spec`, you have to set this when you create the object, providing a description of the characteristics you want the resource to have: its *desired state*.

The `status` describes the *current state* of the object, supplied and updated by the Kubernetes system and its components. The Kubernetes [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) continually and actively manages every object's actual state to match the desired state you supplied.

For example: in Kubernetes, a Deployment is an object that can represent an application running on your cluster. When you create the Deployment, you might set the Deployment `spec` to specify that you want three replicas of the application to be running. The Kubernetes system reads the Deployment spec and starts three instances of your desired application--updating the status to match your spec. If any of those instances should fail (a status change), the Kubernetes system responds to the difference between spec and status by making a correction--in this case, starting a replacement instance.

For more information on the object spec, status, and metadata, see the [Kubernetes API Conventions](https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md).

```
对象说明和状态
几乎所有Kubernetes对象都包含两个状态字段: 就是ojbect spec and objec status. 当对象具有spec属性时, 你必须在创建对象时设置,提供一个特征描述: 你期望的状态
状态字段描述了对象的当前状态, 由Kubernetes系统和它的组件更新和提供.Kubernetes控制平面持续主动的管理每个对象真实的状态以匹配你期望的状态
比如: 在Kubernetes里, Deployment是表示在集群中一个可以运行的状态. 当你创建这个部署, 你可以设置这个Deployment spc来指定应用程序有三个副本.Kubernetes系会读取Deployment规范并启动三个实例为以匹配你的规范.如果其中实例有任何失败的(一个状态变化),Kubernetes系统会通过进行更正来响应规范和状态之间的差异  --在这个示例中,将启动一个替代的实例.

```

### Describing a Kubernetes object

When you create an object in Kubernetes, you must provide the object spec that describes its desired state, as well as some basic information about the object (such as a name). When you use the Kubernetes API to create the object (either directly or via `kubectl`), that API request must include that information as JSON in the request body. Most often, you provide the information to `kubectl` in a file known as a *manifest*. By convention, manifests are YAML (you could also use JSON format). Tools such as `kubectl` convert the information from a manifest into JSON or another supported serialization format when making the API request over HTTP.

Here's an example manifest that shows the required fields and object spec for a Kubernetes Deployment:

[`application/deployment.yaml`](https://raw.githubusercontent.com/kubernetes/website/main/content/en/examples/application/deployment.yaml)![Copy application/deployment.yaml to clipboard](assets/copycode.svg+xml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  selector:
    matchLabels:
      app: nginx
  replicas: 2 # tells deployment to run 2 pods matching the template
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
```

One way to create a Deployment using a manifest file like the one above is to use the [`kubectl apply`](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#apply) command in the `kubectl` command-line interface, passing the `.yaml` file as an argument. Here's an example:

```shell
kubectl apply -f https://k8s.io/examples/application/deployment.yaml
```

The output is similar to this:

```
deployment.apps/nginx-deployment created
```

```
描述 一个Kubernetes 对象
当你创建一个Kubernetes对象,你必须提供描述其期望状态的规范,以及对象的一些基本信息,比如名称. 当你使用Kubernetes API来创建对象(或者直接使用kubectl),那API request必须在request body包含JSON请求体.通常,你会为kubectl提供 'manifest'的信息,通过转换后, mainfests就是一个YAML,你也可以使用JSON格式 . 诸如kubectl的工具会在通过HTTP请求API时,将清单中的信息转换为JSON或者其他支持序列化的格式.
```



### Required fields

In the manifest (YAML or JSON file) for the Kubernetes object you want to create, you'll need to set values for the following fields:

- `apiVersion` - Which version of the Kubernetes API you're using to create this object
- `kind` - What kind of object you want to create
- `metadata` - Data that helps uniquely identify the object, including a `name` string, `UID`, and optional `namespace`
- `spec` - What state you desire for the object

The precise format of the object `spec` is different for every Kubernetes object, and contains nested fields specific to that object. The [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/) can help you find the spec format for all of the objects you can create using Kubernetes.

For example, see the [`spec` field](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec) for the Pod API reference. For each Pod, the `.spec` field specifies the pod and its desired state (such as the container image name for each container within that pod). Another example of an object specification is the [`spec` field](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/stateful-set-v1/#StatefulSetSpec) for the StatefulSet API. For StatefulSet, the `.spec` field specifies the StatefulSet and its desired state. Within the `.spec` of a StatefulSet is a [template](https://kubernetes.io/docs/concepts/workloads/pods/#pod-templates) for Pod objects. That template describes Pods that the StatefulSet controller will create in order to satisfy the StatefulSet specification. Different kinds of objects can also have different `.status`; again, the API reference pages detail the structure of that `.status` field, and its content for each different type of object.

```
每个Kubernetes对象的精确spec都不同,并且包含于对象的特定嵌套字段
比如,pod的spec字段,在每个pod中,.sepc字段指定了pod和他的预期状态,(比如,container image name 在它的pod的每个容器中).另一个例子是StatefulSet. 它的.spec字段指定了StatefulSet和他的预期状态.StafefulSet的.sepc之内包含一个Pod object,模板描述了StatefulSet控制器会为满足StatefulSet规范而创建Pod.不同类型的对象可以有不同的.staus.同样,API引用的详情页中详细介绍.status字段,以及不同类型对象的内容
```

#### Note:

See [Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/) for additional information on writing YAML configuration files.

## Server side field validation

Starting with Kubernetes v1.25, the API server offers server side [field validation](https://kubernetes.io/docs/reference/using-api/api-concepts/#field-validation) that detects unrecognized or duplicate fields in an object. It provides all the functionality of `kubectl --validate` on the server side.

The `kubectl` tool uses the `--validate` flag to set the level of field validation. It accepts the values `ignore`, `warn`, and `strict` while also accepting the values `true` (equivalent to `strict`) and `false` (equivalent to `ignore`). The default validation setting for `kubectl` is `--validate=true`.

- `Strict`

  Strict field validation, errors on validation failure

- `Warn`

  Field validation is performed, but errors are exposed as warnings rather than failing the request

- `Ignore`

  No server side field validation is performed

When `kubectl` cannot connect to an API server that supports field validation it will fall back to using client-side validation. Kubernetes 1.27 and later versions always offer field validation; older Kubernetes releases might not. If your cluster is older than v1.27, check the documentation for your version of Kubernetes.

```
从Kubernetes v1.25开始, api sever提供服务端字段验证用于检测未识别的重复的字段在对象中.它提供了kubectl --validate在服务端中
```



## 