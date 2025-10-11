# Kubernetes Object Management

The `kubectl` command-line tool supports several different ways to create and manage Kubernetes [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects). This document provides an overview of the different approaches. Read the [Kubectl book](https://kubectl.docs.kubernetes.io/) for details of managing objects by Kubectl.

```
kubectl 命令行工具支持多种方式创建和管理Kubernetes对象.此文档提供了一个不同方式使用的总览.参考kubectl book来详细管理kubectl对象
```



## Management techniques

#### Warning:

A Kubernetes object should be managed using only one technique. Mixing and matching techniques for the same object results in undefined behavior.

| Management technique             | Operates on          | Recommended environment | Supported writers | Learning curve |
| -------------------------------- | -------------------- | ----------------------- | ----------------- | -------------- |
| Imperative commands              | Live objects         | Development projects    | 1+                | Lowest         |
| Imperative object configuration  | Individual files     | Production projects     | 1                 | Moderate       |
| Declarative object configuration | Directories of files | Production projects     | 1+                | Highest        |

```
一个Kubernetes对象的应该使用单一管理技术.对同一对象混合和使用多种技术的结果是未定义的行为
```



## Imperative commands

When using imperative commands, a user operates directly on live objects in a cluster. The user provides operations to the `kubectl` command as arguments or flags.

This is the recommended way to get started or to run a one-off task in a cluster. Because this technique operates directly on live objects, it provides no history of previous configurations.

```
当使用命令式命令时,用户直接操作集群中活动的对象.用户提供kubectl命令的操作参数
这是集群中一个开始操作或者运行一次任务的建议.由于该操作直接作用于活动对象,因此不会保留先前配置的历史记录.
```

### Examples

Run an instance of the nginx container by creating a Deployment object:

```sh
kubectl create deployment nginx --image nginx
```

### Trade-offs

Advantages compared to object configuration:

- Commands are expressed as a single action word.
- Commands require only a single step to make changes to the cluster.

Disadvantages compared to object configuration:

- Commands do not integrate with change review processes.
- Commands do not provide an audit trail associated with changes.
- Commands do not provide a source of records except for what is live.
- Commands do not provide a template for creating new objects.

```
权衡
对象配置的优势:
- 命令是以单个动作词表达形式
- 命令仅需一步即可修改集群
对象配置的劣势:
- 命令无法与变更审核流程集成
- 命令不提供对变更的审核追踪
- 除实时状态外,命令不提供记录来源
- 命令没有提供一个模板来创建新的对象

```



## Imperative object configuration

In imperative object configuration, the kubectl command specifies the operation (create, replace, etc.), optional flags and at least one file name. The file specified must contain a full definition of the object in YAML or JSON format.

See the [API reference](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.34/) for more details on object definitions.

#### Warning:

The imperative `replace` command replaces the existing spec with the newly provided one, dropping all changes to the object missing from the configuration file. This approach should not be used with resource types whose specs are updated independently of the configuration file. Services of type `LoadBalancer`, for example, have their `externalIPs` field updated independently from the configuration by the cluster.

```
命令式对象配置
在命令式对象配置中,kubectl命令提供的操作(create,replace, etc.), 可靠的flags至少是一个文件名. 这文件必须提供一个对象的完整定义并且使用YAML或者JSON格式.

Warning:
命令replace 将会使用新提供的spec替换掉现有的sepc. 会放弃所有的配置在配置文件中没有定义部分.此文件不能用于资源类型(它们的spec在独立的配置文件中).比如 servce中的loadBalancer, 比如,这里有 externalIps文件 是独立更新于集群中的配置文件.
```



### Examples

Create the objects defined in a configuration file:

```sh
kubectl create -f nginx.yaml
```

Delete the objects defined in two configuration files:

```sh
kubectl delete -f nginx.yaml -f redis.yaml
```

Update the objects defined in a configuration file by overwriting the live configuration:

```sh
kubectl replace -f nginx.yaml
```

### Trade-offs

Advantages compared to imperative commands:

- Object configuration can be stored in a source control system such as Git.
- Object configuration can integrate with processes such as reviewing changes before push and audit trails.
- Object configuration provides a template for creating new objects.

Disadvantages compared to imperative commands:

- Object configuration requires basic understanding of the object schema.
- Object configuration requires the additional step of writing a YAML file.

Advantages compared to declarative object configuration:

- Imperative object configuration behavior is simpler and easier to understand.
- As of Kubernetes version 1.5, imperative object configuration is more mature.

Disadvantages compared to declarative object configuration:

- Imperative object configuration works best on files, not directories.
- Updates to live objects must be reflected in configuration files, or they will be lost during the next replacement.

```
优势比较使用命令
- 对象配置可以存储在源代码管理中,比如git
- 对象配置可以集成在流程中,比如审核流程,在推送和审计追踪前
- 对象配置提供了模板来进行创建新对象
劣势比较使用命令
- 对象配置需要对对象的结构有基础了解
- 对象配置需要额外的步骤来编写YAML file
优势比较于声明式对象配置
- 对象配置的行为比较简单和易于明白
- 在Kubernetes1.5, 对象配置更成熟
劣势比较于声明式对象配置
- 对象配置工作最好是文件 ,不是文件 夹
- 更新活动对象必须依赖于配置文件 , 或者他们将丢于接下来的替换
```

## Declarative object configuration

When using declarative object configuration, a user operates on object configuration files stored locally, however the user does not define the operations to be taken on the files. Create, update, and delete operations are automatically detected per-object by `kubectl`. This enables working on directories, where different operations might be needed for different objects.

#### Note:

Declarative object configuration retains changes made by other writers, even if the changes are not merged back to the object configuration file. This is possible by using the `patch` API operation to write only observed differences, instead of using the `replace` API operation to replace the entire object configuration.

```
使用声明式对象配置时，用户操作的是本地存储的对象配置文件，但无需定义对文件执行的具体操作。`kubectl`会自动检测每个对象的创建、更新和删除操作。这使得在目录中操作成为可能——不同对象可能需要不同的操作。

注意：

声明式对象配置会保留其他写入者所做的更改，即使这些更改尚未合并回对象配置文件。这是通过使用`patch` API操作仅写入检测到的差异实现的，而非使用`replace` API操作替换整个对象配置。
```



### Examples

Process all object configuration files in the `configs` directory, and create or patch the live objects. You can first `diff` to see what changes are going to be made, and then apply:

```sh
kubectl diff -f configs/
kubectl apply -f configs/
```

Recursively process directories:

```sh
kubectl diff -R -f configs/
kubectl apply -R -f configs/
```

### Trade-offs

Advantages compared to imperative object configuration:

- Changes made directly to live objects are retained, even if they are not merged back into the configuration files.
- Declarative object configuration has better support for operating on directories and automatically detecting operation types (create, patch, delete) per-object.

Disadvantages compared to imperative object configuration:

- Declarative object configuration is harder to debug and understand results when they are unexpected.
- Partial updates using diffs create complex merge and patch operations

```
### 权衡取舍

相较于命令式对象配置的优势：

- 即使未合并回配置文件，对运行中对象的直接修改仍会被保留。
- 声明式对象配置更支持目录操作，并能自动检测每个对象的操作类型（创建、修补、删除）。

相较于命令式对象配置的劣势：

- 声明式配置在出现异常结果时更难调试和理解。
- 基于差异的局部更新会产生复杂的合并和修补操作。
```

