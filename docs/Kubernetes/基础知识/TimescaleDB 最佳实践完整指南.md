## **TimescaleDB 最佳实践完整指南**

### **一、TimescaleDB 核心概念**

#### **1. Hypertable(超表) - 时序数据的核心**

```sql
-- 创建普通表
CREATE TABLE iot_sensor_data (
    time        TIMESTAMPTZ NOT NULL,
    device_id   TEXT NOT NULL,
    temperature DOUBLE PRECISION,
    humidity    DOUBLE PRECISION,
    pressure    DOUBLE PRECISION
);

-- 转换为 Hypertable(自动分区)
SELECT create_hypertable('iot_sensor_data', 'time', 
    chunk_time_interval => INTERVAL '1 day'  -- 每天一个分区
);

-- 添加索引优化查询
CREATE INDEX ON iot_sensor_data (device_id, time DESC);
CREATE INDEX ON iot_sensor_data (time DESC, device_id);
```

**Hypertable 自动做的事:**

- 按时间自动分区(Chunk)
- 每个 Chunk 是独立的 PostgreSQL 表
- 查询时自动路由到相关 Chunk
- 老数据可以单独压缩、归档、删除

------

#### **2. Continuous Aggregates(连续聚合) - 性能关键**

**问题场景**: 你有 3000+ 设备,每 10 秒上报一次数据,查询"过去 7 天每小时平均温度"需要扫描 6000 万行!

**解决方案**: 预计算并增量更新

```sql
-- 创建连续聚合视图:每小时统计
CREATE MATERIALIZED VIEW sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    device_id,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    MIN(temperature) AS min_temp,
    COUNT(*) AS sample_count
FROM iot_sensor_data
GROUP BY bucket, device_id
WITH NO DATA;  -- 不立即填充数据

-- 设置自动刷新策略(每 30 分钟更新一次)
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
    start_offset => INTERVAL '3 hours',   -- 从 3 小时前开始
    end_offset => INTERVAL '1 hour',      -- 到 1 小时前结束
    schedule_interval => INTERVAL '30 minutes'  -- 每 30 分钟执行
);

-- 查询时直接用聚合视图(快 100 倍+)
SELECT bucket, device_id, avg_temp
FROM sensor_data_hourly
WHERE bucket >= NOW() - INTERVAL '7 days'
  AND device_id = 'device_001'
ORDER BY bucket DESC;
```

**建议创建的聚合层级:**

- **1 分钟聚合**: 保留 7 天,用于近期详细分析
- **1 小时聚合**: 保留 90 天,用于趋势分析
- **1 天聚合**: 保留 1 年,用于长期报表

------

### **二、数据保留与分层策略(重要!)**

你目前"保留 3 个月,无分层策略",这不够优化。正确做法:

#### **分层保留策略设计:**

| 数据层级     | 时间范围  | 原始数据   | 压缩方式        | 查询频率 | 存储成本 |
| ------------ | --------- | ---------- | --------------- | -------- | -------- |
| **热数据**   | 最近 7 天 | ✅ 保留     | 无压缩          | 高频     | 高       |
| **温数据**   | 8-30 天   | ✅ 保留     | 原生压缩(2-20x) | 中频     | 中       |
| **冷数据**   | 31-90 天  | ⚠️ 降采样   | 原生压缩 + 聚合 | 低频     | 低       |
| **归档数据** | >90 天    | ❌ 删除原始 | 仅保留聚合视图  | 极少     | 极低     |

------

#### **实施步骤:**

**Step 1: 启用原生压缩(温数据层)**

```sql
-- 对超过 7 天的 Chunk 自动压缩
ALTER TABLE iot_sensor_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id',  -- 按设备分段压缩
    timescaledb.compress_orderby = 'time DESC'     -- 按时间排序
);

-- 添加压缩策略
SELECT add_compression_policy('iot_sensor_data', 
    INTERVAL '7 days'  -- 7 天前的数据自动压缩
);

-- 查看压缩效果
SELECT 
    chunk_name,
    pg_size_pretty(before_compression_total_bytes) AS before,
    pg_size_pretty(after_compression_total_bytes) AS after,
    ROUND(before_compression_total_bytes::numeric / after_compression_total_bytes::numeric, 2) AS ratio
FROM chunk_compression_stats('iot_sensor_data')
ORDER BY chunk_name DESC
LIMIT 10;

-- 典型压缩比: 5-20 倍
```

**压缩后的限制:**

- ✅ 可以 SELECT 查询
- ❌ 不能 UPDATE/DELETE
- ❌ 不能添加新列

------

**Step 2: 数据降采样(冷数据层)**

**原理**: 原始数据 10 秒一条太密集,30 天后降为 1 分钟一条

```sql
-- 创建降采样任务(将 10s 数据聚合为 1min)
CREATE MATERIALIZED VIEW sensor_data_1min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', time) AS bucket,
    device_id,
    AVG(temperature) AS temperature,
    AVG(humidity) AS humidity,
    AVG(pressure) AS pressure
FROM iot_sensor_data
GROUP BY bucket, device_id;

-- 自动刷新
SELECT add_continuous_aggregate_policy('sensor_data_1min',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 hour'
);
```

------

**Step 3: 自动删除过期数据(归档层)**

```sql
-- 删除 90 天前的原始数据
SELECT add_retention_policy('iot_sensor_data', 
    INTERVAL '90 days'
);

-- 但保留聚合视图(占用空间小)
-- sensor_data_1min 可以保留 1 年
-- sensor_data_hourly 可以保留 3 年
-- sensor_data_daily 可以保留永久
```

------

**Step 4: 完整的分层架构示意**

```
时间线:
|------ 7天 ------|------ 23天 ------|------ 60天 ------|--- 永久 ---|
     热数据            温数据              冷数据            归档数据

存储内容:
原始(10s)         原始(10s压缩)      1min降采样        1hour聚合
未压缩            压缩(10x)          压缩(5x)          压缩(3x)
100 GB           230 GB (压缩前2.3TB)  60 GB (压缩前300GB)  50 GB

查询延迟:
< 100ms          < 500ms            < 1s              < 100ms

存储成本(相对):
10                5                  2                 1
```

**总存储成本降低**: 从 2.59 TB → 440 GB,**节省 83%!**

------

### **三、查询性能优化进阶**

你提到使用了 `time_bucket`,很好!继续深化:

#### **1. time_bucket 最佳实践**

```sql
-- ✅ 正确:直接使用 time_bucket
SELECT 
    time_bucket('5 minutes', time) AS bucket,
    device_id,
    AVG(temperature) AS avg_temp
FROM iot_sensor_data
WHERE time > NOW() - INTERVAL '1 hour'
  AND device_id IN ('device_001', 'device_002')
GROUP BY bucket, device_id
ORDER BY bucket DESC;

-- ❌ 错误:先 GROUP BY time 再聚合(慢)
SELECT 
    DATE_TRUNC('minute', time) AS bucket,
    ...
```

**time_bucket 的优势:**

- 与 Chunk 分区对齐,减少扫描
- 自动利用索引
- 支持连续聚合

------

#### **2. 并行查询(Parallel Query)**

```sql
-- 启用并行查询(默认可能关闭)
ALTER TABLE iot_sensor_data SET (parallel_workers = 4);

-- 复杂聚合查询自动并行化
SET max_parallel_workers_per_gather = 4;

EXPLAIN ANALYZE
SELECT 
    time_bucket('1 hour', time) AS bucket,
    COUNT(DISTINCT device_id) AS device_count,
    AVG(temperature) AS avg_temp
FROM iot_sensor_data
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY bucket;

-- 查看执行计划,确认使用了 Parallel Seq Scan
```

------

#### **3. 分区裁剪(Partition Pruning)**

```sql
-- ✅ 正确:时间范围查询自动裁剪无关 Chunk
SELECT * FROM iot_sensor_data
WHERE time >= '2025-10-01' AND time < '2025-10-02';
-- 只扫描 2025-10-01 的 Chunk

-- ❌ 错误:不指定时间范围,全表扫描
SELECT * FROM iot_sensor_data
WHERE device_id = 'device_001'
ORDER BY time DESC
LIMIT 100;
-- 扫描所有 Chunk!

-- ✅ 修正:加上时间范围
SELECT * FROM iot_sensor_data
WHERE device_id = 'device_001'
  AND time > NOW() - INTERVAL '7 days'  -- 关键!
ORDER BY time DESC
LIMIT 100;
```

------

#### **4. 索引策略**

```sql
-- 主要查询模式 1: 按设备查询最近数据
CREATE INDEX idx_device_time ON iot_sensor_data (device_id, time DESC);

-- 主要查询模式 2: 按时间范围 + 设备聚合
CREATE INDEX idx_time_device ON iot_sensor_data (time DESC, device_id);

-- 主要查询模式 3: 特定指标范围查询
CREATE INDEX idx_temp_time ON iot_sensor_data (temperature, time DESC)
WHERE temperature > 100;  -- 部分索引,节省空间

-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'iot_sensor_data'
ORDER BY idx_scan DESC;
```

------

### **四、K8s 内部署 TimescaleDB 最佳实践**

#### **1. StatefulSet 部署配置**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: timescaledb
  namespace: database
spec:
  serviceName: timescaledb
  replicas: 1  # 生产环境可用主从复制
  selector:
    matchLabels:
      app: timescaledb
  template:
    metadata:
      labels:
        app: timescaledb
    spec:
      # 反亲和性:不与其他数据库部署在同一节点
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["mysql", "redis", "kafka"]
            topologyKey: kubernetes.io/hostname
      
      containers:
      - name: timescaledb
        image: timescale/timescaledb:latest-pg15
        
        # 资源配置(根据你的数据量调整)
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
        
        # 环境变量
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: timescaledb-secret
              key: password
        - name: POSTGRES_DB
          value: "iot_metrics"
        # 性能调优参数
        - name: TIMESCALEDB_TELEMETRY
          value: "off"
        - name: TS_TUNE_MEMORY
          value: "12GB"  # 75% of memory
        - name: TS_TUNE_NUM_CPUS
          value: "4"
        
        # 持久化存储
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
          subPath: postgres  # 避免权限问题
        
        # 自定义配置
        - name: config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
        
        # 就绪探针
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        
        # 存活探针
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 60
          periodSeconds: 30
      
      volumes:
      - name: config
        configMap:
          name: timescaledb-config
  
  # 持久化卷声明
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: ssd-storage  # 使用 SSD!
      resources:
        requests:
          storage: 500Gi  # 根据你的 TB 级数据调整
```

------

#### **2. 性能调优配置(ConfigMap)**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: timescaledb-config
data:
  postgresql.conf: |
    # 内存配置(假设 16GB 总内存)
    shared_buffers = 4GB              # 25% 内存
    effective_cache_size = 12GB       # 75% 内存
    maintenance_work_mem = 2GB        # 用于 VACUUM, CREATE INDEX
    work_mem = 64MB                   # 每个查询操作的内存
    
    # TimescaleDB 特定
    timescaledb.max_background_workers = 8
    max_worker_processes = 16
    max_parallel_workers_per_gather = 4
    max_parallel_workers = 8
    
    # WAL 配置(提升写入性能)
    wal_buffers = 16MB
    min_wal_size = 1GB
    max_wal_size = 4GB
    checkpoint_completion_target = 0.9
    
    # 连接数
    max_connections = 200
    
    # 日志
    log_min_duration_statement = 1000  # 记录 >1s 的慢查询
    log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
    
    # 自动 VACUUM
    autovacuum = on
    autovacuum_max_workers = 4
    autovacuum_naptime = 30s
```

------

#### **3. 备份策略**

```bash
# 方案 1: pg_dump 逻辑备份(小数据量)
kubectl exec -n database timescaledb-0 -- \
  pg_dump -U postgres -Fc iot_metrics > backup_$(date +%Y%m%d).dump

# 方案 2: 物理备份(推荐,TB 级数据)
# 使用 pgBackRest 或 WAL-G

# 部署 pgBackRest Sidecar
apiVersion: v1
kind: Pod
metadata:
  name: timescaledb-backup
spec:
  containers:
  - name: pgbackrest
    image: pgbackrest/pgbackrest:latest
    command:
    - pgbackrest
    - backup
    - --type=full
    - --repo1-path=/backup
    - --repo1-retention-full=7  # 保留 7 个全量备份
    volumeMounts:
    - name: backup
      mountPath: /backup
    - name: data
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: backup
    persistentVolumeClaim:
      claimName: backup-pvc
```

------

### **五、监控 TimescaleDB 的关键指标**

#### **Prometheus Exporter 部署**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: postgres-exporter
        image: prometheuscommunity/postgres-exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          value: "postgresql://postgres:password@timescaledb:5432/iot_metrics?sslmode=disable"
        ports:
        - containerPort: 9187
```

#### **关键监控指标**

```promql
# 1. 数据库大小增长
pg_database_size_bytes{datname="iot_metrics"}

# 2. 连接数
pg_stat_database_numbackends{datname="iot_metrics"}

# 3. 事务速率
rate(pg_stat_database_xact_commit{datname="iot_metrics"}[5m])

# 4. 缓存命中率(应该 >95%)
sum(pg_stat_database_blks_hit{datname="iot_metrics"}) / 
(sum(pg_stat_database_blks_hit{datname="iot_metrics"}) + 
 sum(pg_stat_database_blks_read{datname="iot_metrics"}))

# 5. Hypertable 统计
timescaledb_hypertable_num_chunks
timescaledb_hypertable_uncompressed_size_bytes
timescaledb_hypertable_compressed_size_bytes

# 6. 慢查询数量
pg_stat_statements_calls{query=~".*FROM iot_sensor_data.*"}
```

#### **Grafana 告警规则**

```yaml
# 数据库大小超过 80%
- alert: TimescaleDBDiskFull
  expr: |
    (pg_database_size_bytes / 
     (node_filesystem_size_bytes{mountpoint="/var/lib/postgresql/data"})) > 0.8
  for: 10m
  labels:
    severity: P1

# 缓存命中率低
- alert: LowCacheHitRate
  expr: |
    (sum(pg_stat_database_blks_hit) / 
     (sum(pg_stat_database_blks_hit) + sum(pg_stat_database_blks_read))) < 0.9
  for: 30m
  labels:
    severity: P2

# 连接数过高
- alert: HighDatabaseConnections
  expr: pg_stat_database_numbackends > 180
  for: 5m
  labels:
    severity: P2
```

------

### **六、存储成本优化总结**

你提到使用了 ILM 策略,这里是完整的优化矩阵:

| 优化手段       | 实施难度 | 成本节省     | 性能影响        |
| -------------- | -------- | ------------ | --------------- |
| **原生压缩**   | ⭐ 简单   | 80-95%       | 查询慢 10-30%   |
| **连续聚合**   | ⭐⭐ 中等  | 50-70%       | 查询快 10-100倍 |
| **数据降采样** | ⭐⭐⭐ 复杂 | 90%          | 精度略降        |
| **分层保留**   | ⭐⭐ 中等  | 60-80%       | 无影响          |
| **自动删除**   | ⭐ 简单   | 取决于保留期 | 无影响          |

**推荐组合拳:**

1. 7 天内原始数据(未压缩)

2. 7-30 天原始数据(压缩 10x)

3. 30-90 天降采样(压缩 5x)

4. > 90 天仅聚合视图

5. **总成本降低 80%+**

------

## **面试标准答案模板**

> **"我们使用 TimescaleDB 管理 TB 级时序数据,通过分层保留策略优化成本:**
>
> **1. 数据分层**:
>
> - 热数据(7天): 原始未压缩,查询 <100ms
> - 温数据(8-30天): 原生压缩(10x),查询 <500ms
> - 冷数据(31-90天): 降采样+压缩,查询 <1s
> - 归档(>90天): 仅保留聚合视图,永久保存
>
> **2. 性能优化**:
>
> - 使用 time_bucket 和连续聚合,查询速度提升 100 倍
> - 创建多级聚合视图(1分钟/1小时/1天)
> - 索引策略匹配主要查询模式
> - 并行查询处理大数据量聚合
>
> **3. 成本优化**: 通过压缩和降采样,存储成本从 2.5 TB 降至 400 GB,**节省 84%**
>
> **4. 运维保障**: K8s StatefulSet 部署,SSD 存储,物理备份,Prometheus 监控关键指标(DB 大小、缓存命中率、慢查询)"

------

