## 主题：Kubernetes存储架构

### 1. 存储的三层抽象

Kubernetes将存储抽象为三层，解耦了存储提供者和使用者：

```
StorageClass (存储类)
    ↓ 动态创建
PersistentVolume (持久卷 - PV)
    ↓ 绑定
PersistentVolumeClaim (持久卷声明 - PVC)
    ↓ 挂载
Pod
```

**为什么需要三层**：
- **Pod**：我需要100GB存储
- **PVC**：申请100GB，不关心底层是什么（NFS/Ceph/云盘）
- **PV**：具体的存储资源（管理员创建或自动创建）
- **StorageClass**：如何自动创建PV的模板

### 2. PV（PersistentVolume）- 存储资源

**PV是集群级资源**，不属于任何命名空间：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local-01
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce  # RWO
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:  # Local PV必须指定节点
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - k8s-worker-1
```

**访问模式（AccessModes）**：

| 模式          | 缩写 | 含义       | 示例存储               |
| ------------- | ---- | ---------- | ---------------------- |
| ReadWriteOnce | RWO  | 单节点读写 | 本地盘、云盘           |
| ReadOnlyMany  | ROX  | 多节点只读 | NFS、对象存储          |
| ReadWriteMany | RWX  | 多节点读写 | NFS、GlusterFS、CephFS |

**回收策略（ReclaimPolicy）**：

```
Retain（保留）：
  PVC删除 → PV变为Released状态 → 数据保留 → 需要手动清理

Delete（删除）：
  PVC删除 → PV自动删除 → 底层存储也删除

Recycle（已废弃）：
  PVC删除 → 执行 rm -rf /volume/* → PV变为Available
```

### 3. PVC（PersistentVolumeClaim）- 存储申请

**PVC是命名空间级资源**，Pod通过PVC使用存储：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: default
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-storage
```

**绑定过程**：
```
1. 用户创建PVC，申请5Gi RWO存储
2. K8s查找匹配的PV：
   - 容量 >= 5Gi
   - accessModes包含RWO
   - storageClassName相同
3. 找到PV后绑定（1:1绑定）
4. PVC状态：Pending → Bound
```

**如果没有匹配的PV**：
```
静态配置：PVC一直Pending，等待管理员创建PV
动态配置：StorageClass自动创建PV
```

### 4. StorageClass - 动态配置

**StorageClass定义如何自动创建PV**：

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/no-provisioner  # 本地卷不支持动态配置
volumeBindingMode: WaitForFirstConsumer    # 延迟绑定
allowVolumeExpansion: true                 # 允许扩容
```

**云环境的动态配置示例**（阿里云）：

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: alicloud-disk-ssd
provisioner: diskplugin.csi.alibabacloud.com
parameters:
  type: cloud_ssd
  regionId: cn-hangzhou
  zoneId: cn-hangzhou-b
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

**动态配置流程**：
```
1. 用户创建PVC，指定storageClassName: alicloud-disk-ssd
2. StorageClass的provisioner被触发
3. Provisioner调用云厂商API创建云盘
4. 创建对应的PV对象
5. PV与PVC自动绑定
6. Pod挂载PVC
```

### 5. CSI（Container Storage Interface）

**CSI是存储插件的标准接口**：

```
以前：每种存储都要写K8s插件（in-tree）
现在：存储厂商实现CSI接口（out-of-tree）

CSI定义三组RPC：
1. Identity Service：插件信息
2. Controller Service：创建/删除/挂载卷
3. Node Service：节点级操作
```

**CSI插件架构**：
```
Controller Plugin (Deployment)
  - 集中管理：创建/删除卷
  - 调用云厂商API
  - 一般1-3个副本

Node Plugin (DaemonSet)
  - 每个节点一个
  - 负责卷的挂载/卸载
  - 格式化文件系统
```

### 6. Volume生命周期

**完整流程**：

```
阶段1: Provision（配置）
  - 创建底层存储
  - 创建PV对象

阶段2: Bind（绑定）
  - PVC与PV绑定
  - 1:1关系

阶段3: Use（使用）
  - Pod通过PVC挂载
  - AttachDetachController：将卷attach到节点
  - VolumeManager：将卷mount到Pod

阶段4: Release（释放）
  - PVC删除
  - PV状态变为Released

阶段5: Reclaim（回收）
  - 根据reclaimPolicy处理
  - Retain/Delete/Recycle
```

**实际操作示例**：

```yaml
# 1. 创建PV（手动）
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /mnt/data

---
# 2. 创建PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
# 3. Pod使用PVC
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-pvc
```

**查看状态**：
```bash
kubectl get pv
# NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM
# my-pv   5Gi        RWO            Retain           Bound    default/my-pvc

kubectl get pvc
# NAME     STATUS   VOLUME   CAPACITY   ACCESS MODES
# my-pvc   Bound    my-pv    5Gi        RWO
```

### 7. StatefulSet与存储

**StatefulSet使用VolumeClaimTemplates**：

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:  # 自动为每个Pod创建PVC
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

**自动创建PVC**：
```
mysql-0 → data-mysql-0 (PVC) → pv-001
mysql-1 → data-mysql-1 (PVC) → pv-002
mysql-2 → data-mysql-2 (PVC) → pv-003

每个Pod有独立的持久化存储
即使Pod重建，仍然挂载相同的PVC
```

### 8. 存储类型对比

| 类型             | 生命周期 | 数据持久化    | 适用场景             |
| ---------------- | -------- | ------------- | -------------------- |
| emptyDir         | Pod级别  | Pod删除即丢失 | 临时数据、缓存       |
| hostPath         | 节点级别 | 节点上保留    | 测试、访问节点文件   |
| PV/PVC           | 独立     | 独立于Pod     | 生产数据库、文件存储 |
| ConfigMap/Secret | 独立     | 配置数据      | 配置文件、密钥       |

### 9. 关键概念总结

**存储抽象的价值**：
```
开发者：我要100GB空间
  ↓ (创建PVC)
K8s：自动找到或创建存储
  ↓ (绑定PV)
底层：可能是NFS、Ceph、云盘...

开发者无需关心底层实现
迁移环境时只需换StorageClass
```

**为什么WordPress会丢数据**：
```
用的是emptyDir：
  Pod创建 → 临时目录
  Pod删除 → 目录销毁
  
应该用PVC：
  Pod创建 → 绑定已有PV
  Pod删除 → PV保留
  Pod重建 → 挂载相同PV，数据恢复
```

---

现在想学习：
1. **调度机制** - Scheduler如何选择节点、亲和性算法
2. **RBAC安全** - 权限控制、ServiceAccount
3. **还是继续存储话题** - 具体存储方案对比（NFS/Ceph/云存储）

或者今天学习到这里，消化一下这些理论知识？