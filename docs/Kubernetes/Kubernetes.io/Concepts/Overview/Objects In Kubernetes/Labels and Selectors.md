# Labels and Selectors

*Labels* are key/value pairs that are attached to [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#kubernetes-objects) such as Pods. Labels are intended to be used to specify identifying attributes of objects that are meaningful and relevant to users, but do not directly imply semantics to the core system. Labels can be used to organize and to select subsets of objects. Labels can be attached to objects at creation time and subsequently added and modified at any time. Each object can have a set of key/value labels defined. Each Key must be unique for a given object.

```json
"metadata": {
  "labels": {
    "key1" : "value1",
    "key2" : "value2"
  }
}
```

Labels allow for efficient queries and watches and are ideal for use in UIs and CLIs. Non-identifying information should be recorded using [annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/).

```
labels是键值对的形式附加到对象中.比如Pods.Labels是依赖于提供一些有用对象的认证属性,一般都来自于用户, 但不会直接向核心系统传递语义.Labels可以用来组织和选择对象的集合.Labels可以在对象创建时附加,也可以在任何有需要的时候修改.每个对象都可以定义一组key/value的标签. 有给予对象标签时, 每个Key必须是唯一的.
```

## Motivation

Labels enable users to map their own organizational structures onto system objects in a loosely coupled fashion, without requiring clients to store these mappings.

Service deployments and batch processing pipelines are often multi-dimensional entities (e.g., multiple partitions or deployments, multiple release tracks, multiple tiers, multiple micro-services per tier). Management often requires cross-cutting operations, which breaks encapsulation of strictly hierarchical representations, especially rigid hierarchies determined by the infrastructure rather than by users.

Example labels:

- `"release" : "stable"`, `"release" : "canary"`
- `"environment" : "dev"`, `"environment" : "qa"`, `"environment" : "production"`
- `"tier" : "frontend"`, `"tier" : "backend"`, `"tier" : "cache"`
- `"partition" : "customerA"`, `"partition" : "customerB"`
- `"track" : "daily"`, `"track" : "weekly"`

These are examples of [commonly used labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/); you are free to develop your own conventions. Keep in mind that label Key must be unique for a given object.

```
动机
标签允许用户以一种松散的组合方式映射他们的组织架构在系统对象中,而不需要客户端来存储这些映射.
服务部署和批处理管道通常是多维实体（例如：多个分区或部署、多个发布通道、多层架构、每层多个微服务）。管理操作往往需要跨维度操作，这会打破严格分层表示的封装性，尤其当这种分层结构由基础设施而非用户决定时更为明显。
Example labels:

- `"release" : "stable"`, `"release" : "canary"`
- `"environment" : "dev"`, `"environment" : "qa"`, `"environment" : "production"`
- `"tier" : "frontend"`, `"tier" : "backend"`, `"tier" : "cache"`
- `"partition" : "customerA"`, `"partition" : "customerB"`
- `"track" : "daily"`, `"track" : "weekly"`
这是一些常用的有用的标签,你可以定义自己的转换,记住对象的标签key必须是唯一的

```



## Syntax and character set

*Labels* are key/value pairs. Valid label keys have two segments: an optional prefix and name, separated by a slash (`/`). The name segment is required and must be 63 characters or less, beginning and ending with an alphanumeric character (`[a-z0-9A-Z]`) with dashes (`-`), underscores (`_`), dots (`.`), and alphanumerics between. The prefix is optional. If specified, the prefix must be a DNS subdomain: a series of DNS labels separated by dots (`.`), not longer than 253 characters in total, followed by a slash (`/`).

If the prefix is omitted, the label Key is presumed to be private to the user. Automated system components (e.g. `kube-scheduler`, `kube-controller-manager`, `kube-apiserver`, `kubectl`, or other third-party automation) which add labels to end-user objects must specify a prefix.

The `kubernetes.io/` and `k8s.io/` prefixes are [reserved](https://kubernetes.io/docs/reference/labels-annotations-taints/) for Kubernetes core components.

Valid label value:

- must be 63 characters or less (can be empty),
- unless empty, must begin and end with an alphanumeric character (`[a-z0-9A-Z]`),
- could contain dashes (`-`), underscores (`_`), dots (`.`), and alphanumerics between.

For example, here's a manifest for a Pod that has two labels `environment: production` and `app: nginx`:

```
*标签*是键值对。有效的标签键由两部分组成：可选的前缀和名称，两者以斜杠（`/`）分隔。名称部分为必填项，长度不得超过63个字符，且必须以字母数字字符（`[a-z0-9A-Z]`）开头和结尾，中间可包含连字符（`-`）、下划线（`_`）、点号（`.`）及字母数字字符。前缀为可选项。若指定前缀，则必须为DNS子域：由点号（`.`）分隔的DNS标签序列，总长不超过253个字符，后接斜杠（`/`）。

若省略前缀，则标签键默认为用户私有。自动系统组件（如`kube-scheduler`、`kube-controller-manager`、`kube-apiserver`、`kubectl`或其他第三方自动化工具）向终端用户对象添加标签时必须指定前缀。

`kubernetes.io/` 和 `k8s.io/` 前缀为 Kubernetes 核心组件[保留](https://kubernetes.io/docs/reference/labels-annotations-taints/)。

有效标签值要求：

- 总长度不超过 63 个字符（可为空）
- 非空时首尾必须为字母数字字符（`[a-z0-9A-Z]`），
- 中间可包含连字符（`-`）、下划线（`_`）、点号（`.`）及字母数字字符。

例如，以下是具有两个标签 `environment: production` 和 `app: nginx` 的 Pod 配置文件：

通过DeepL.com（免费版）翻译
```



```yaml
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.14.2
    ports:
    - containerPort: 80
```

## Label selectors

Unlike [names and UIDs](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/), labels do not provide uniqueness. In general, we expect many objects to carry the same label(s).

Via a *label selector*, the client/user can identify a set of objects. The label selector is the core grouping primitive in Kubernetes.

The API currently supports two types of selectors: *equality-based* and *set-based*. A label selector can be made of multiple *requirements* which are comma-separated. In the case of multiple requirements, all must be satisfied so the comma separator acts as a logical *AND* (`&&`) operator.

The semantics of empty or non-specified selectors are dependent on the context, and API types that use selectors should document the validity and meaning of them.

#### Note:

For some API types, such as ReplicaSets, the label selectors of two instances must not overlap within a namespace, or the controller can see that as conflicting instructions and fail to determine how many replicas should be present.

#### Caution:

For both equality-based and set-based conditions there is no logical *OR* (`||`) operator. Ensure your filter statements are structured accordingly.

```
Label selectors
不同于名称和UID, 标签不需要唯一性, 通常我们期望多个对象有着同样的标签.
通过一个标签选择器,客户端和用户可以获取一组对象的集合. 在Kubernetes中标签选择器是核心的分组原语
API目前支持两种类型的选择器,基于等式和基于集合.一个标签选择器可以有多个需求,使用逗号分开. 在多需求中, 所有的标签必须全部满足,相当于逻辑比较符 &&
空或者未提供的选择器语义依赖于上下文. API类型在使用选择器时应该将验证和它们的意义文档化.

Note:
有一些API的类型,比如ReplicaSet, 在同一个namespace中两个实例的标签选择器不能重叠,控制器视为指令冲突,从而无法确实要产生的副本数量

Caution:
基于等式或者基于集合的条件中两者都不存在于逻辑 OR的条件. 确实你的筛选语句结构符合此要求.

```



### *Equality-based* requirement

*Equality-* or *inequality-based* requirements allow filtering by label keys and values. Matching objects must satisfy all of the specified label constraints, though they may have additional labels as well. Three kinds of operators are admitted `=`,`==`,`!=`. The first two represent *equality* (and are synonyms), while the latter represents *inequality*. For example:

```
environment = production
tier != frontend
```

The former selects all resources with key equal to `environment` and value equal to `production`. The latter selects all resources with key equal to `tier` and value distinct from `frontend`, and all resources with no labels with the `tier` key. One could filter for resources in `production` excluding `frontend` using the comma operator: `environment=production,tier!=frontend`

One usage scenario for equality-based label requirement is for Pods to specify node selection criteria. For example, the sample Pod below selects nodes where the `accelerator` label exists and is set to `nvidia-tesla-p100`.

````
*基于相等性*或*基于不等性*的要求允许通过标签键值进行过滤。匹配对象必须满足所有指定的标签约束，但也可附加其他标签。支持三种运算符：`=`、`==`、`!=`。前两者表示*相等性*（且为同义词），后者表示*不等性*。例如：

```
环境 = 生产环境
层级 != 前端
```

前者筛选所有键值为 `环境` 且值为 `生产环境` 的资源。后者筛选所有键值为 `层级` 但值不同于 `前端` 的资源，以及所有未携带 `层级` 键的资源。若需筛选`production`环境中排除`frontend`的资源，可使用逗号运算符：`environment=production,tier!=frontend`

基于等值的标签要求常用于Pod节点选择策略。例如下例Pod仅选择存在`accelerator`标签且值为`nvidia-tesla-p100`的节点：
````



```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cuda-test
spec:
  containers:
    - name: cuda-test
      image: "registry.k8s.io/cuda-vector-add:v0.1"
      resources:
        limits:
          nvidia.com/gpu: 1
  nodeSelector:
    accelerator: nvidia-tesla-p100
```

### *Set-based* requirement

*Set-based* label requirements allow filtering keys according to a set of values. Three kinds of operators are supported: `in`,`notin` and `exists` (only the key identifier). For example:

```
environment in (production, qa)
tier notin (frontend, backend)
partition
!partition
```

- The first example selects all resources with key equal to `environment` and value equal to `production` or `qa`.
- The second example selects all resources with key equal to `tier` and values other than `frontend` and `backend`, and all resources with no labels with the `tier` key.
- The third example selects all resources including a label with key `partition`; no values are checked.
- The fourth example selects all resources without a label with key `partition`; no values are checked.

Similarly the comma separator acts as an *AND* operator. So filtering resources with a `partition` key (no matter the value) and with `environment` different than `qa` can be achieved using `partition,environment notin (qa)`. The *set-based* label selector is a general form of equality since `environment=production` is equivalent to `environment in (production)`; similarly for `!=` and `notin`.

*Set-based* requirements can be mixed with *equality-based* requirements. For example: `partition in (customerA, customerB),environment!=qa`.

````
基于集合的标签要求允许根据一组值过滤键。支持三种运算符：`in`、`notin` 和 `exists`（仅限键标识符）。例如：

```
environment in (production, qa)
tier notin (frontend, backend)
partition
!partition
```

- 首例选择所有具有 `environment` 键且值为 `production` 或 `qa` 的资源。
- 次例选择所有具有 `tier` 键且值非 `frontend` 或 `backend` 的资源，以及所有未携带 `tier` 键标签的资源。
- 第三例选择所有包含 `partition` 键标签的资源；不检查具体值。
- 第四例选择所有不包含`partition`标签的资源；不检查具体值。

同样地，逗号分隔符充当*AND*运算符。因此，通过`partition,environment notin (qa)`可实现同时筛选包含`partition`标签（无论值为何）且`environment`不同于`qa`的资源。基于集合的标签选择器本质上是等值运算的通用形式，因为`environment=production`等同于`environment in (production)`；`!=`和`notin`运算符亦遵循此原理。

集合型条件可与等值型条件混合使用。例如：`partition in (customerA, customerB),environment!=qa`。

通过DeepL.com（免费版）翻译
````



## API

### LIST and WATCH filtering

For **list** and **watch** operations, you can specify label selectors to filter the sets of objects returned; you specify the filter using a query parameter. (To learn in detail about watches in Kubernetes, read [efficient detection of changes](https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes)). Both requirements are permitted (presented here as they would appear in a URL query string):

- *equality-based* requirements: `?labelSelector=environment%3Dproduction,tier%3Dfrontend`
- *set-based* requirements: `?labelSelector=environment+in+%28production%2Cqa%29%2Ctier+in+%28frontend%29`

Both label selector styles can be used to list or watch resources via a REST client. For example, targeting `apiserver` with `kubectl` and using *equality-based* one may write:

```shell
kubectl get pods -l environment=production,tier=frontend
```

or using *set-based* requirements:

```shell
kubectl get pods -l 'environment in (production),tier in (frontend)'
```

As already mentioned *set-based* requirements are more expressive. For instance, they can implement the *OR* operator on values:

```shell
kubectl get pods -l 'environment in (production, qa)'
```

or restricting negative matching via *notin* operator:

```shell
kubectl get pods -l 'environment,environment notin (frontend)'
```

### Set references in API objects

Some Kubernetes objects, such as [`services`](https://kubernetes.io/docs/concepts/services-networking/service/) and [`replicationcontrollers`](https://kubernetes.io/docs/concepts/workloads/controllers/replicationcontroller/), also use label selectors to specify sets of other resources, such as [pods](https://kubernetes.io/docs/concepts/workloads/pods/).

#### Service and ReplicationController

The set of pods that a `service` targets is defined with a label selector. Similarly, the population of pods that a `replicationcontroller` should manage is also defined with a label selector.

Label selectors for both objects are defined in `json` or `yaml` files using maps, and only *equality-based* requirement selectors are supported:

```json
"selector": {
    "component" : "redis",
}
```

or

```yaml
selector:
  component: redis
```

This selector (respectively in `json` or `yaml` format) is equivalent to `component=redis` or `component in (redis)`.

#### Resources that support set-based requirements

Newer resources, such as [`Job`](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [`Deployment`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), [`ReplicaSet`](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/), and [`DaemonSet`](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/), support *set-based* requirements as well.

```yaml
selector:
  matchLabels:
    component: redis
  matchExpressions:
    - { key: tier, operator: In, values: [cache] }
    - { key: environment, operator: NotIn, values: [dev] }
```

`matchLabels` is a map of `{key,value}` pairs. A single `{key,value}` in the `matchLabels` map is equivalent to an element of `matchExpressions`, whose `key` field is "key", the `operator` is "In", and the `values` array contains only "value". `matchExpressions` is a list of pod selector requirements. Valid operators include In, NotIn, Exists, and DoesNotExist. The values set must be non-empty in the case of In and NotIn. All of the requirements, from both `matchLabels` and `matchExpressions` are ANDed together -- they must all be satisfied in order to match.

#### Selecting sets of nodes

One use case for selecting over labels is to constrain the set of nodes onto which a pod can schedule. See the documentation on [node selection](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) for more information.

## Using labels effectively

You can apply a single label to any resources, but this is not always the best practice. There are many scenarios where multiple labels should be used to distinguish resource sets from one another.

For instance, different applications would use different values for the `app` label, but a multi-tier application, such as the [guestbook example](https://github.com/kubernetes/examples/tree/master/web/guestbook/), would additionally need to distinguish each tier. The frontend could carry the following labels:

```yaml
labels:
  app: guestbook
  tier: frontend
```

while the Redis master and replica would have different `tier` labels, and perhaps even an additional `role` label:

```yaml
labels:
  app: guestbook
  tier: backend
  role: master
```

and

```yaml
labels:
  app: guestbook
  tier: backend
  role: replica
```

The labels allow for slicing and dicing the resources along any dimension specified by a label:

```shell
kubectl apply -f examples/guestbook/all-in-one/guestbook-all-in-one.yaml
kubectl get pods -Lapp -Ltier -Lrole
NAME                           READY  STATUS    RESTARTS   AGE   APP         TIER       ROLE
guestbook-fe-4nlpb             1/1    Running   0          1m    guestbook   frontend   <none>
guestbook-fe-ght6d             1/1    Running   0          1m    guestbook   frontend   <none>
guestbook-fe-jpy62             1/1    Running   0          1m    guestbook   frontend   <none>
guestbook-redis-master-5pg3b   1/1    Running   0          1m    guestbook   backend    master
guestbook-redis-replica-2q2yf  1/1    Running   0          1m    guestbook   backend    replica
guestbook-redis-replica-qgazl  1/1    Running   0          1m    guestbook   backend    replica
my-nginx-divi2                 1/1    Running   0          29m   nginx       <none>     <none>
my-nginx-o0ef1                 1/1    Running   0          29m   nginx       <none>     <none>
kubectl get pods -lapp=guestbook,role=replica
NAME                           READY  STATUS   RESTARTS  AGE
guestbook-redis-replica-2q2yf  1/1    Running  0         3m
guestbook-redis-replica-qgazl  1/1    Running  0         3m
```

## Updating labels

Sometimes you may want to relabel existing pods and other resources before creating new resources. This can be done with `kubectl label`. For example, if you want to label all your NGINX Pods as frontend tier, run:

```shell
kubectl label pods -l app=nginx tier=fe
pod/my-nginx-2035384211-j5fhi labeled
pod/my-nginx-2035384211-u2c7e labeled
pod/my-nginx-2035384211-u3t6x labeled
```

This first filters all pods with the label "app=nginx", and then labels them with the "tier=fe". To see the pods you labeled, run:

```shell
kubectl get pods -l app=nginx -L tier
NAME                        READY     STATUS    RESTARTS   AGE       TIER
my-nginx-2035384211-j5fhi   1/1       Running   0          23m       fe
my-nginx-2035384211-u2c7e   1/1       Running   0          23m       fe
my-nginx-2035384211-u3t6x   1/1       Running   0          23m       fe
```

This outputs all "app=nginx" pods, with an additional label column of pods' tier (specified with `-L` or `--label-columns`).

For more information, please see [kubectl label](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands/#label).