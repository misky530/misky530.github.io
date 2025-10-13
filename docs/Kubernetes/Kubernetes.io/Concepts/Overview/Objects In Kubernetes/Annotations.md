# Annotations

You can use Kubernetes annotations to attach arbitrary non-identifying metadata to [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects). Clients such as tools and libraries can retrieve this metadata.

## Attaching metadata to objects

You can use either labels or annotations to attach metadata to Kubernetes objects. Labels can be used to select objects and to find collections of objects that satisfy certain conditions. In contrast, annotations are not used to identify and select objects. The metadata in an annotation can be small or large, structured or unstructured, and can include characters not permitted by labels. It is possible to use labels as well as annotations in the metadata of the same object.

```
您可以使用 Kubernetes 注解将任意非标识性元数据附加到[对象](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects)。客户端（例如工具和库）可以检索这些元数据。

## 将元数据附加到对象

您可以使用标签或注解将元数据附加到 Kubernetes 对象。标签可用于选择对象以及查找满足特定条件的对象集合。相反，注解不用于识别和选择对象。注解中的元数据可以长可短，可以结构化或非结构化，并且可以包含标签不允许的字符。在同一对象的元数据中，可以同时使用标签和注解。
```

Annotations, like labels, are key/value maps:

```json
"metadata": {
  "annotations": {
    "key1" : "value1",
    "key2" : "value2"
  }
}
```

#### Note:

The keys and the values in the map must be strings. In other words, you cannot use numeric, boolean, list or other types for either the keys or the values.

Here are some examples of information that could be recorded in annotations:

- Fields managed by a declarative configuration layer. Attaching these fields as annotations distinguishes them from default values set by clients or servers, and from auto-generated fields and fields set by auto-sizing or auto-scaling systems.
- Build, release, or image information like timestamps, release IDs, git branch, PR numbers, image hashes, and registry address.
- Pointers to logging, monitoring, analytics, or audit repositories.
- Client library or tool information that can be used for debugging purposes: for example, name, version, and build information.
- User or tool/system provenance information, such as URLs of related objects from other ecosystem components.
- Lightweight rollout tool metadata: for example, config or checkpoints.
- Phone or pager numbers of persons responsible, or directory entries that specify where that information can be found, such as a team web site.
- Directives from the end-user to the implementations to modify behavior or engage non-standard features.

Instead of using annotations, you could store this type of information in an external database or directory, but that would make it much harder to produce shared client libraries and tools for deployment, management, introspection, and the like.

```
#### 注意：

映射中的键和值必须是字符串。换句话说，您不能使用数字、布尔值、列表或其他类型作为键或值。

以下是一些可以在注解中记录的信息示例：

- 由声明式配置层管理的字段。将这些字段附加为注解可以将它们与客户端或服务器设置的默认值以及自动生成的字段以及自动调整大小或自动伸缩系统设置的字段区分开来。
- 构建、发布或镜像信息，例如时间戳、发布 ID、git 分支、PR 编号、镜像哈希值和注册表地址。
- 指向日志记录、监控、分析或审计存储库的指针。
- 可用于调试目的的客户端库或工具信息：例如名称、版本和构建信息。
- 用户或工具/系统来源信息，例如来自其他生态系统组件的相关对象的 URL。
- 轻量级部署工具元数据：例如配置或检查点。
- 负责人的电话号码或传呼机号码，或指定该信息所在位置的目录条目，例如团队网站。
- 最终用户向实现发出的指令，用于修改行为或启用非标准功能。

除了使用注解之外，您还可以将此类信息存储在外部数据库或目录中，但这会使生成用于部署、管理、自省等的共享客户端库和工具变得更加困难。
```

## Syntax and character set

*Annotations* are key/value pairs. Valid annotation keys have two segments: an optional prefix and name, separated by a slash (`/`). The name segment is required and must be 63 characters or less, beginning and ending with an alphanumeric character (`[a-z0-9A-Z]`) with dashes (`-`), underscores (`_`), dots (`.`), and alphanumerics between. The prefix is optional. If specified, the prefix must be a DNS subdomain: a series of DNS labels separated by dots (`.`), not longer than 253 characters in total, followed by a slash (`/`).

If the prefix is omitted, the annotation Key is presumed to be private to the user. Automated system components (e.g. `kube-scheduler`, `kube-controller-manager`, `kube-apiserver`, `kubectl`, or other third-party automation) which add annotations to end-user objects must specify a prefix.

The `kubernetes.io/` and `k8s.io/` prefixes are reserved for Kubernetes core components.

For example, here's a manifest for a Pod that has the annotation `imageregistry: https://hub.docker.com/` :

```
*注释* 是键/值对。有效的注释键包含两部分：可选的前缀和名称，以斜杠 (`/`) 分隔。名称部分是必需的，且长度不得超过 63 个字符，以字母数字字符 (`[a-z0-9A-Z]`) 开头和结尾，中间可以包含短划线 (`-`)、下划线 (`_`)、点 (`.`) 以及字母数字字符。前缀是可选的。如果指定，前缀必须是 DNS 子域名：一系列以点 (`.`) 分隔的 DNS 标签，总长度不超过 253 个字符，后跟斜杠 (`/`)。

如果省略前缀，则假定注释键对用户是私有的。向最终用户对象添加注解的自动化系统组件（例如 `kube-scheduler`、`kube-controller-manager`、`kube-apiserver`、`kubectl` 或其他第三方自动化组件）必须指定前缀。

`kubernetes.io/` 和 `k8s.io/` 前缀是为 Kubernetes 核心组件保留的。

例如，以下是包含注解 `imageregistry: https://hub.docker.com/` 的 Pod 的清单：
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: annotations-demo
  annotations:
    imageregistry: "https://hub.docker.com/"
spec:
  containers:
  - name: nginx
    image: nginx:1.14.2
    ports:
    - containerPort: 80
```

## 