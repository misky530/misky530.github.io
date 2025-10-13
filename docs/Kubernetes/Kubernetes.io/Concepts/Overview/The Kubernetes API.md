# The Kubernetes API

The Kubernetes API lets you query and manipulate the state of objects in Kubernetes. The core of Kubernetes' control plane is the API server and the HTTP API that it exposes. Users, the different parts of your cluster, and external components all communicate with one another through the API server.

The core of Kubernetes' [control plane](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) is the [API server](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver). The API server exposes an HTTP API that lets end users, different parts of your cluster, and external components communicate with one another.

The Kubernetes API lets you query and manipulate the state of API objects in Kubernetes (for example: Pods, Namespaces, ConfigMaps, and Events).

Most operations can be performed through the [kubectl](https://kubernetes.io/docs/reference/kubectl/) command-line interface or other command-line tools, such as [kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/), which in turn use the API. However, you can also access the API directly using REST calls. Kubernetes provides a set of [client libraries](https://kubernetes.io/docs/reference/using-api/client-libraries/) for those looking to write applications using the Kubernetes API.

Each Kubernetes cluster publishes the specification of the APIs that the cluster serves. There are two mechanisms that Kubernetes uses to publish these API specifications; both are useful to enable automatic interoperability. For example, the `kubectl` tool fetches and caches the API specification for enabling command-line completion and other features. The two supported mechanisms are as follows:

- [The Discovery API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#discovery-api) provides information about the Kubernetes APIs: API names, resources, versions, and supported operations. This is a Kubernetes specific term as it is a separate API from the Kubernetes OpenAPI. It is intended to be a brief summary of the available resources and it does not detail specific schema for the resources. For reference about resource schemas, please refer to the OpenAPI document.
- The [Kubernetes OpenAPI Document](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#openapi-interface-definition) provides (full) [OpenAPI v2.0 and 3.0 schemas](https://www.openapis.org/) for all Kubernetes API endpoints. The OpenAPI v3 is the preferred method for accessing OpenAPI as it provides a more comprehensive and accurate view of the API. It includes all the available API paths, as well as all resources consumed and produced for every operations on every endpoints. It also includes any extensibility components that a cluster supports. The data is a complete specification and is significantly larger than that from the Discovery API.

```
# Kubernetes API

Kubernetes API 允许您查询和操作 Kubernetes 中对象的状态。Kubernetes 控制平面的核心是 API 服务器及其公开的 HTTP API。用户、集群的不同部分以及外部组件都通过 API 服务器相互通信。

Kubernetes [控制平面](https://kubernetes.io/docs/reference/glossary/?all=true#term-control-plane) 的核心是 [API 服务器](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver)。API 服务器公开 HTTP API，允许最终用户、集群的不同部分以及外部组件相互通信。

Kubernetes API 允许您查询和操作 Kubernetes 中 API 对象的状态（例如：Pod、命名空间、ConfigMap 和事件）。

大多数操作可以通过 [kubectl](https://kubernetes.io/docs/reference/kubectl/) 命令行界面或其他命令行工具（例如 [kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/））执行，这些工具会使用 API。但是，您也可以使用 REST 调用直接访问 API。Kubernetes 为希望使用 Kubernetes API 编写应用程序的用户提供了一组 [客户端库](https://kubernetes.io/docs/reference/using-api/client-libraries/)。

每个 Kubernetes 集群都会发布其所服务的 API 规范。Kubernetes 使用两种机制来发布这些 API 规范；这两种机制都有助于实现自动互操作性。例如，`kubectl` 工具会获取并缓存 API 规范，以启用命令行补全和其他功能。支持的两种机制如下：

- [Discovery API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#discovery-api) 提供有关 Kubernetes API 的信息：API 名称、资源、版本和支持的操作。这是一个 Kubernetes 特有的术语，因为它与 Kubernetes OpenAPI 是不同的 API。它旨在简要概述可用的资源，并未详细说明资源的具体架构。有关资源架构的参考信息，请参阅 OpenAPI 文档。
- [Kubernetes OpenAPI 文档](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#openapi-interface-definition) 为所有 Kubernetes API 端点提供了（完整的）[OpenAPI v2.0 和 3.0 架构](https://www.openapis.org/)。OpenAPI v3 是访问 OpenAPI 的首选方法，因为它提供了更全面、更准确的 API 视图。它包含所有可用的 API 路径，以及每个端点上每个操作消耗和生成的所有资源。它还包含集群支持的所有可扩展组件。这些数据是一份完整的规范，并且比 Discovery API 中的数据要大得多。
```

## Discovery API

Kubernetes publishes a list of all group versions and resources supported via the Discovery API. This includes the following for each resource:

- Name
- Cluster or namespaced scope
- Endpoint URL and supported verbs
- Alternative names
- Group, version, kind

The API is available in both aggregated and unaggregated form. The aggregated discovery serves two endpoints, while the unaggregated discovery serves a separate endpoint for each group version.

```
## 发现 API

Kubernetes 发布了通过发现 API 支持的所有组版本和资源的列表。其中包含每个资源的以下内容：

- 名称
- 集群或命名空间范围
- 端点 URL 和支持的动词
- 备用名称
- 组、版本、类型

该 API 提供聚合和非聚合两种形式。聚合发现服务于两个端点，而非聚合发现为每个组版本服务一个单独的端点。
```

### Aggregated discovery

**FEATURE STATE:** `Kubernetes v1.30 [stable]` (enabled by default: true)

Kubernetes offers stable support for *aggregated discovery*, publishing all resources supported by a cluster through two endpoints (`/api` and `/apis`). Requesting this endpoint drastically reduces the number of requests sent to fetch the discovery data from the cluster. You can access the data by requesting the respective endpoints with an `Accept` header indicating the aggregated discovery resource: `Accept: application/json;v=v2;g=apidiscovery.k8s.io;as=APIGroupDiscoveryList`.

Without indicating the resource type using the `Accept` header, the default response for the `/api` and `/apis` endpoint is an unaggregated discovery document.

The [discovery document](https://github.com/kubernetes/kubernetes/blob/release-1.34/api/discovery/aggregated_v2.json) for the built-in resources can be found in the Kubernetes GitHub repository. This Github document can be used as a reference of the base set of the available resources if a Kubernetes cluster is not available to query.

The endpoint also supports ETag and protobuf encoding.

### Unaggregated discovery

Without discovery aggregation, discovery is published in levels, with the root endpoints publishing discovery information for downstream documents.

A list of all group versions supported by a cluster is published at the `/api` and `/apis` endpoints. Example:

```
### 聚合发现

**功能状态**：`Kubernetes v1.30 [stable]`（默认启用：true）

Kubernetes 为*聚合发现*提供稳定支持，通过两个端点（`/api` 和 `/apis`）发布集群支持的所有资源。请求此端点可显著减少从集群获取发现数据的请求数量。您可以通过使用 `Accept` 标头请求相应的端点来访问数据，该标头指示聚合发现资源：`Accept: application/json;v=v2;g=apidiscovery.k8s.io;as=APIGroupDiscoveryList`。

如果未使用 `Accept` 标头指示资源类型，则 `/api` 和 `/apis` 端点的默认响应为未聚合的发现文档。

内置资源的 [发现文档](https://github.com/kubernetes/kubernetes/blob/release-1.34/api/discovery/aggregated_v2.json) 可在 Kubernetes GitHub 仓库中找到。如果 Kubernetes 集群无法查询，可以参考此 Github 文档，了解可用资源的基本集合。

该端点还支持 ETag 和 protobuf 编码。

### 非聚合发现

若未聚合发现，则发现信息将按级别发布，根端点将发布下游文档的发现信息。

集群支持的所有组版本列表将在 `/api` 和 `/apis` 端点上发布。示例：
```



```
{
  "kind": "APIGroupList",
  "apiVersion": "v1",
  "groups": [
    {
      "name": "apiregistration.k8s.io",
      "versions": [
        {
          "groupVersion": "apiregistration.k8s.io/v1",
          "version": "v1"
        }
      ],
      "preferredVersion": {
        "groupVersion": "apiregistration.k8s.io/v1",
        "version": "v1"
      }
    },
    {
      "name": "apps",
      "versions": [
        {
          "groupVersion": "apps/v1",
          "version": "v1"
        }
      ],
      "preferredVersion": {
        "groupVersion": "apps/v1",
        "version": "v1"
      }
    },
    ...
}
```

Additional requests are needed to obtain the discovery document for each group version at `/apis/<group>/<version>` (for example: `/apis/rbac.authorization.k8s.io/v1alpha1`), which advertises the list of resources served under a particular group version. These endpoints are used by kubectl to fetch the list of resources supported by a cluster.

## OpenAPI interface definition

For details about the OpenAPI specifications, see the [OpenAPI documentation](https://www.openapis.org/).

Kubernetes serves both OpenAPI v2.0 and OpenAPI v3.0. OpenAPI v3 is the preferred method of accessing the OpenAPI because it offers a more comprehensive (lossless) representation of Kubernetes resources. Due to limitations of OpenAPI version 2, certain fields are dropped from the published OpenAPI including but not limited to `default`, `nullable`, `oneOf`.

### OpenAPI V2

The Kubernetes API server serves an aggregated OpenAPI v2 spec via the `/openapi/v2` endpoint. You can request the response format using request headers as follows:

```
## OpenAPI 接口定义

有关 OpenAPI 规范的详细信息，请参阅 [OpenAPI 文档](https://www.openapis.org/)。

Kubernetes 同时提供 OpenAPI v2.0 和 OpenAPI v3.0 版本。OpenAPI v3 是访问 OpenAPI 的首选方法，因为它能够更全面（无损）地呈现 Kubernetes 资源。由于 OpenAPI v2 版本的限制，已发布的 OpenAPI 中删除了某些字段，包括但不限于 `default`、`nullable` 和 `oneOf`。

### OpenAPI V2

Kubernetes API 服务器通过 `/openapi/v2` 端点提供聚合的 OpenAPI v2 规范。您可以使用以下请求标头请求响应格式：
```



| Header             | Possible values                                              | Notes                                          |
| ------------------ | ------------------------------------------------------------ | ---------------------------------------------- |
| `Accept-Encoding`  | `gzip`                                                       | *not supplying this header is also acceptable* |
| `Accept`           | `application/com.github.proto-openapi.spec.v2@v1.0+protobuf` | *mainly for intra-cluster use*                 |
| `application/json` | *default*                                                    |                                                |
| `*`                | *serves* `application/json`                                  |                                                |

#### Warning:

The validation rules published as part of OpenAPI schemas may not be complete, and usually aren't. Additional validation occurs within the API server. If you want precise and complete verification, a `kubectl apply --dry-run=server` runs all the applicable validation (and also activates admission-time checks).

### OpenAPI V3

**FEATURE STATE:** `Kubernetes v1.27 [stable]` (enabled by default: true)

Kubernetes supports publishing a description of its APIs as OpenAPI v3.

A discovery endpoint `/openapi/v3` is provided to see a list of all group/versions available. This endpoint only returns JSON. These group/versions are provided in the following format:

```yaml
{
    "paths": {
        ...,
        "api/v1": {
            "serverRelativeURL": "/openapi/v3/api/v1?hash=CC0E9BFD992D8C59AEC98A1E2336F899E8318D3CF4C68944C3DEC640AF5AB52D864AC50DAA8D145B3494F75FA3CFF939FCBDDA431DAD3CA79738B297795818CF"
        },
        "apis/admissionregistration.k8s.io/v1": {
            "serverRelativeURL": "/openapi/v3/apis/admissionregistration.k8s.io/v1?hash=E19CC93A116982CE5422FC42B590A8AFAD92CDE9AE4D59B5CAAD568F083AD07946E6CB5817531680BCE6E215C16973CD39003B0425F3477CFD854E89A9DB6597"
        },
        ....
    }
}
```

The relative URLs are pointing to immutable OpenAPI descriptions, in order to improve client-side caching. The proper HTTP caching headers are also set by the API server for that purpose (`Expires` to 1 year in the future, and `Cache-Control` to `immutable`). When an obsolete URL is used, the API server returns a redirect to the newest URL.

The Kubernetes API server publishes an OpenAPI v3 spec per Kubernetes group version at the `/openapi/v3/apis/<group>/<version>?hash=<hash>` endpoint.

Refer to the table below for accepted request headers.

| Header             | Possible values                                              | Notes                                          |
| ------------------ | ------------------------------------------------------------ | ---------------------------------------------- |
| `Accept-Encoding`  | `gzip`                                                       | *not supplying this header is also acceptable* |
| `Accept`           | `application/com.github.proto-openapi.spec.v3@v1.0+protobuf` | *mainly for intra-cluster use*                 |
| `application/json` | *default*                                                    |                                                |
| `*`                | *serves* `application/json`                                  |                                                |

A Golang implementation to fetch the OpenAPI V3 is provided in the package [`k8s.io/client-go/openapi3`](https://pkg.go.dev/k8s.io/client-go/openapi3).

Kubernetes 1.34 publishes OpenAPI v2.0 and v3.0; there are no plans to support 3.1 in the near future.

### Protobuf serialization

Kubernetes implements an alternative Protobuf based serialization format that is primarily intended for intra-cluster communication. For more information about this format, see the [Kubernetes Protobuf serialization](https://git.k8s.io/design-proposals-archive/api-machinery/protobuf.md) design proposal and the Interface Definition Language (IDL) files for each schema located in the Go packages that define the API objects.

## Persistence

Kubernetes stores the serialized state of objects by writing them into [etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/).

## API groups and versioning

To make it easier to eliminate fields or restructure resource representations, Kubernetes supports multiple API versions, each at a different API path, such as `/api/v1` or `/apis/rbac.authorization.k8s.io/v1alpha1`.

Versioning is done at the API level rather than at the resource or field level to ensure that the API presents a clear, consistent view of system resources and behavior, and to enable controlling access to end-of-life and/or experimental APIs.

To make it easier to evolve and to extend its API, Kubernetes implements [API groups](https://kubernetes.io/docs/reference/using-api/#api-groups) that can be [enabled or disabled](https://kubernetes.io/docs/reference/using-api/#enabling-or-disabling).

API resources are distinguished by their API group, resource type, namespace (for namespaced resources), and name. The API server handles the conversion between API versions transparently: all the different versions are actually representations of the same persisted data. The API server may serve the same underlying data through multiple API versions.

For example, suppose there are two API versions, `v1` and `v1beta1`, for the same resource. If you originally created an object using the `v1beta1` version of its API, you can later read, update, or delete that object using either the `v1beta1` or the `v1` API version, until the `v1beta1` version is deprecated and removed. At that point you can continue accessing and modifying the object using the `v1` API.

### API changes

Any system that is successful needs to grow and change as new use cases emerge or existing ones change. Therefore, Kubernetes has designed the Kubernetes API to continuously change and grow. The Kubernetes project aims to *not* break compatibility with existing clients, and to maintain that compatibility for a length of time so that other projects have an opportunity to adapt.

In general, new API resources and new resource fields can be added often and frequently. Elimination of resources or fields requires following the [API deprecation policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/).

Kubernetes makes a strong commitment to maintain compatibility for official Kubernetes APIs once they reach general availability (GA), typically at API version `v1`. Additionally, Kubernetes maintains compatibility with data persisted via *beta* API versions of official Kubernetes APIs, and ensures that data can be converted and accessed via GA API versions when the feature goes stable.

If you adopt a beta API version, you will need to transition to a subsequent beta or stable API version once the API graduates. The best time to do this is while the beta API is in its deprecation period, since objects are simultaneously accessible via both API versions. Once the beta API completes its deprecation period and is no longer served, the replacement API version must be used.

#### Note:

Although Kubernetes also aims to maintain compatibility for *alpha* APIs versions, in some circumstances this is not possible. If you use any alpha API versions, check the release notes for Kubernetes when upgrading your cluster, in case the API did change in incompatible ways that require deleting all existing alpha objects prior to upgrade.

Refer to [API versions reference](https://kubernetes.io/docs/reference/using-api/#api-versioning) for more details on the API version level definitions.

## API Extension

The Kubernetes API can be extended in one of two ways:

1. [Custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) let you declaratively define how the API server should provide your chosen resource API.
2. You can also extend the Kubernetes API by implementing an [aggregation layer](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/).

```
k8s.io/client-go/openapi3 包中提供了一个用于获取 OpenAPI V3 的 Golang 实现。

Kubernetes 1.34 发布了 OpenAPI v2.0 和 v3.0；近期没有计划支持 3.1 版本。

### Protobuf 序列化

Kubernetes 实现了一种基于 Protobuf 的替代序列化格式，主要用于集群内通信。有关此格式的更多信息，请参阅 Kubernetes Protobuf 序列化设计方案以及定义 API 对象的 Go 包中每个 Schema 的接口定义语言 (IDL) 文件。

## 持久性

Kubernetes 通过将对象的序列化状态写入 [etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) 来存储它们。

## API 组和版本控制

为了更轻松地删除字段或重构资源表示，Kubernetes 支持多个 API 版本，每个版本都有不同的 API 路径，例如“/api/v1”或“/apis/rbac.authorization.k8s.io/v1alpha1”。

版本控制在 API 级别而不是资源或字段级别进行，以确保 API 呈现清晰、一致的系统资源和行为视图，并支持控制对已终止和/或实验性 API 的访问。

为了更轻松地演进和扩展其 API，Kubernetes 实现了 [API 组](https://kubernetes.io/docs/reference/using-api/#api-groups)，这些组可以 [启用或禁用](https://kubernetes.io/docs/reference/using-api/#enabling-or-disabling)。

API 资源通过其 API 组、资源类型、命名空间（对于命名空间资源）和名称进行区分。API 服务器透明地处理 API 版本之间的转换：所有不同版本实际上都是相同持久化数据的表示。API 服务器可以通过多个 API 版本提供相同的底层数据。

例如，假设同一资源有两个 API 版本，分别为 `v1` 和 `v1beta1`。如果您最初使用 `v1beta1` 版本的 API 创建了一个对象，那么之后您可以使用 `v1beta1` 或 `v1` API 版本读取、更新或删除该对象，直到 `v1beta1` 版本被弃用并移除。届时，您可以继续使用 `v1` API 访问和修改该对象。

### API 变更

任何成功的系统都需要随着新用例的出现或现有用例的变化而发展和变化。因此，Kubernetes 将 Kubernetes API 设计为持续变化和发展。Kubernetes 项目的目标是*不*破坏与现有客户端的兼容性，并在一段时间内保持这种兼容性，以便其他项目有机会适应。

通常，可以频繁地添加新的 API 资源和新的资源字段。删除资源或字段需要遵循 [API 弃用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)。

Kubernetes 承诺在官方 Kubernetes API 正式发布 (GA)（通常为 API 版本“v1”）后保持兼容性。此外，Kubernetes 还与官方 Kubernetes API 的 *beta* API 版本保持数据兼容性，并确保在功能稳定后可以通过 GA API 版本转换和访问数据。

如果您采用 Beta API 版本，则需要在 API 正式发布后过渡到后续的 Beta 或稳定 API 版本。最佳过渡时间是 Beta API 处于弃用期时，因为对象可以通过两个 API 版本同时访问。一旦 Beta API 完成弃用期并不再提供服务，就必须使用替代 API 版本。

#### 注意：

尽管 Kubernetes 也致力于保持与 *alpha* API 版本的兼容性，但在某些情况下这是不可能的。如果您使用任何 alpha API 版本，请在升级集群时查看 Kubernetes 的发行说明，以防 API 发生不兼容的更改，导致需要在升级前删除所有现有的 alpha 对象。

有关 API 版本级别定义的更多详细信息，请参阅 [API 版本参考](https://kubernetes.io/docs/reference/using-api/#api-versioning)。

## API 扩展

Kubernetes API 可以通过以下两种方式扩展：

1. [自定义资源](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) 允许您以声明方式定义 API 服务器应如何提供您选择的资源 API。
2. 您还可以通过实现 [聚合层](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/) 来扩展 Kubernetes API。
```

