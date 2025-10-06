## **Prometheus + Grafana 监控最佳实践**

### **一、监控指标体系(四个黄金信号)**

Google SRE 提出的监控理论 - **四个黄金信号**(Four Golden Signals):

#### **1. 延迟 (Latency)** - 请求响应时间

```promql
# API 响应时间 P99
histogram_quantile(0.99, 
  rate(http_request_duration_seconds_bucket[5m])
)

# MQTT 消息处理延迟
rate(mqtt_message_processing_duration_sum[5m]) / 
rate(mqtt_message_processing_duration_count[5m])
```

#### **2. 流量 (Traffic)** - 系统负载

```promql
# API QPS
rate(http_requests_total[1m])

# Kafka 消息生产速率
rate(kafka_producer_records_sent_total[1m])

# MQTT 连接数
mqtt_connected_clients
```

#### **3. 错误 (Errors)** - 失败率

```promql
# HTTP 5xx 错误率
rate(http_requests_total{status=~"5.."}[5m]) / 
rate(http_requests_total[5m])

# Kafka 消费失败率
rate(kafka_consumer_failed_messages_total[5m])
```

#### **4. 饱和度 (Saturation)** - 资源使用率

```promql
# CPU 使用率
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 磁盘使用率
(node_filesystem_size_bytes - node_filesystem_free_bytes) / 
node_filesystem_size_bytes * 100
```

------

### **二、你的 IOT 场景应该监控的完整指标**

#### **基础设施层 (Infrastructure)**

| 类别     | 指标                       | Exporter            | 用途           |
| -------- | -------------------------- | ------------------- | -------------- |
| **节点** | CPU/内存/磁盘/网络         | node-exporter       | 资源瓶颈预警   |
| **K8s**  | Pod 状态/重启次数/资源配额 | kube-state-metrics  | 容器健康度     |
| **存储** | IOPS/延迟/容量             | 具体存储的 exporter | 性能和容量规划 |

**关键告警示例:**

```yaml
# CPU 使用率超过 80% 持续 5 分钟
- alert: HighCPUUsage
  expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: P2
  annotations:
    summary: "节点 {{ $labels.instance }} CPU 使用率过高"
    value: "{{ $value | humanizePercentage }}"
```

------

#### **中间件层 (Middleware)**

| 组件           | 关键指标                   | 告警阈值示例   |
| -------------- | -------------------------- | -------------- |
| **EMQX**       | 连接数、消息速率、队列长度 | 队列 > 10000   |
| **Kafka**      | Lag、ISR、磁盘使用         | Lag > 100000   |
| **Redis**      | 内存使用、命中率、慢查询   | 慢查询 > 1s    |
| **MySQL**      | 连接数、慢查询、复制延迟   | 复制延迟 > 10s |
| **时序数据库** | 写入速率、查询延迟、存储   | 磁盘 > 85%     |

**Kafka 监控示例:**

```promql
# Consumer Lag 告警
kafka_consumergroup_lag{group="iot-message-group"} > 50000

# Under-Replicated Partitions(副本不足)
kafka_cluster_partition_underreplicated > 0
```

------

#### **应用层 (Application)**

**你的 IOT 系统应该暴露的业务指标:**

```python
# Python 示例:使用 prometheus_client 库
from prometheus_client import Counter, Histogram, Gauge

# 1. 消息处理计数器
message_processed = Counter(
    'iot_messages_processed_total',
    'Total messages processed',
    ['device_type', 'status']  # 标签:设备类型、处理状态
)

# 2. 消息处理延迟直方图
message_latency = Histogram(
    'iot_message_processing_duration_seconds',
    'Message processing latency',
    buckets=[0.1, 0.5, 1, 2, 5, 10]  # 延迟分桶
)

# 3. 在线设备数
online_devices = Gauge(
    'iot_devices_online',
    'Number of online devices',
    ['device_type']
)

# 业务代码中使用
message_processed.labels(device_type='sensor', status='success').inc()
with message_latency.time():
    process_message(msg)
online_devices.labels(device_type='gateway').set(3000)
```

**关键业务告警:**

```yaml
# 消息处理成功率低于 95%
- alert: MessageProcessingFailureHigh
  expr: |
    (
      rate(iot_messages_processed_total{status="success"}[5m]) /
      rate(iot_messages_processed_total[5m])
    ) < 0.95
  for: 10m
  labels:
    severity: P1
  annotations:
    summary: "消息处理成功率过低"
    description: "当前成功率: {{ $value | humanizePercentage }}"

# 消息处理延迟 P99 超过 5 秒
- alert: MessageProcessingLatencyHigh
  expr: |
    histogram_quantile(0.99,
      rate(iot_message_processing_duration_seconds_bucket[5m])
    ) > 5
  for: 5m
  labels:
    severity: P2
```

------

### **三、告警分级标准 (P0-P3)**

#### **分级原则:**

- **影响范围**: 影响多少用户/设备?
- **业务影响**: 核心功能是否不可用?
- **响应时间**: 需要多快处理?

#### **详细分级标准表:**

| 级别   | 严重程度 | 典型场景                                               | 响应时间    | 通知方式             | 值班要求            |
| ------ | -------- | ------------------------------------------------------ | ----------- | -------------------- | ------------------- |
| **P0** | 🔴 致命   | • 整个系统不可用<br>• 数据丢失风险<br>• 影响 >50% 用户 | **5 分钟**  | 电话 + 短信 + IM     | 立即处理,升级到总监 |
| **P1** | 🟠 紧急   | • 核心功能受损<br>• 影响 20-50% 用户<br>• 性能严重下降 | **15 分钟** | 短信 + IM(钉钉/企微) | 30 分钟内响应       |
| **P2** | 🟡 重要   | • 非核心功能异常<br>• 资源使用率高<br>• 影响 <20% 用户 | **1 小时**  | IM 群消息            | 工作时间内处理      |
| **P3** | 🟢 提示   | • 预警性信息<br>• 趋势异常<br>• 建议优化               | **1 天**    | 仅记录到工单系统     | 周会讨论            |

------

#### **你的 IOT 系统告警分级示例:**

**P0 级告警(致命):**

```yaml
# K8s 集群 API Server 不可用
- alert: KubernetesAPIServerDown
  expr: up{job="kubernetes-apiservers"} == 0
  for: 1m
  labels:
    severity: P0
  annotations:
    summary: "🔴 K8s API Server 宕机"
    runbook: "https://wiki.company.com/runbook/k8s-api-down"

# EMQX 集群全部节点宕机
- alert: EMQXClusterDown
  expr: up{job="emqx"} == 0
  for: 2m
  labels:
    severity: P0
  annotations:
    summary: "🔴 EMQX 集群完全不可用,所有设备离线"

# Kafka 所有 Broker 宕机
- alert: KafkaClusterDown
  expr: count(up{job="kafka"} == 1) == 0
  for: 1m
  labels:
    severity: P0
```

**P1 级告警(紧急):**

```yaml
# 消息积压严重
- alert: KafkaConsumerLagCritical
  expr: kafka_consumergroup_lag > 200000
  for: 10m
  labels:
    severity: P1
  annotations:
    summary: "🟠 消息严重积压,可能导致数据延迟"
    current_lag: "{{ $value }}"

# Pod 频繁重启
- alert: PodCrashLooping
  expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.1
  for: 5m
  labels:
    severity: P1
  annotations:
    summary: "🟠 Pod {{ $labels.pod }} 频繁重启"

# 在线设备数骤降
- alert: OnlineDevicesDropped
  expr: |
    (
      iot_devices_online - iot_devices_online offset 10m
    ) / iot_devices_online offset 10m < -0.3
  for: 5m
  labels:
    severity: P1
  annotations:
    summary: "🟠 在线设备数下降 30%"
```

**P2 级告警(重要):**

```yaml
# 资源使用率高
- alert: HighMemoryUsage
  expr: |
    (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
  for: 10m
  labels:
    severity: P2
  annotations:
    summary: "🟡 节点 {{ $labels.instance }} 内存使用率超过 85%"

# 磁盘空间不足
- alert: DiskSpaceRunningOut
  expr: |
    (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 15
  for: 30m
  labels:
    severity: P2
  annotations:
    summary: "🟡 磁盘空间不足 15%,预计 {{ $value | humanizeDuration }} 后耗尽"
```

**P3 级告警(提示):**

```yaml
# 证书即将过期
- alert: CertificateExpiringSoon
  expr: |
    (
      probe_ssl_earliest_cert_expiry - time()
    ) / 86400 < 30
  for: 1h
  labels:
    severity: P3
  annotations:
    summary: "🟢 SSL 证书将在 30 天内过期"

# 慢查询增多
- alert: SlowQueriesIncreasing
  expr: rate(mysql_global_status_slow_queries[10m]) > 5
  for: 1h
  labels:
    severity: P3
```

------

### **四、告警噪音(Alert Fatigue)问题**

#### **什么是告警噪音?**

- **大量无效告警**: 每天收到 100+ 条告警,但 90% 都不需要处理
- **频繁抖动**: 同一个问题反复触发/恢复
- **误报**: 阈值设置不合理导致的假警报

#### **后果:**

- 运维人员麻木,**真正的严重问题被忽略**
- "狼来了"效应,影响响应速度

------

#### **减少告警噪音的 8 大策略:**

**1. 合理设置阈值和持续时间**

```yaml
# ❌ 错误:太敏感
- alert: HighCPU
  expr: cpu_usage > 70
  for: 10s  # 只持续 10 秒就告警

# ✅ 正确:有缓冲
- alert: HighCPU
  expr: cpu_usage > 85
  for: 5m   # 持续 5 分钟才告警
```

**2. 使用 `avg_over_time` 平滑抖动**

```yaml
# 使用 5 分钟平均值,避免瞬时波动
- alert: HighMemory
  expr: avg_over_time(memory_usage[5m]) > 90
  for: 10m
```

**3. 告警抑制(Inhibition)**

```yaml
# AlertManager 配置:当 P0 告警触发时,抑制 P1/P2 告警
inhibit_rules:
- source_match:
    severity: 'P0'
  target_match_re:
    severity: 'P1|P2'
  equal: ['instance']  # 相同实例的低级别告警被抑制
```

**4. 告警分组(Grouping)**

```yaml
# 将同类告警合并成一条通知
route:
  group_by: ['alertname', 'cluster']
  group_wait: 30s        # 等待 30 秒收集更多告警
  group_interval: 5m     # 每 5 分钟发送一次分组告警
  repeat_interval: 4h    # 重复告警间隔 4 小时
```

**5. 静默时间窗口(Silences)**

```bash
# 变更窗口期间静默告警
amtool silence add \
  alertname=HighCPU \
  instance=node-1 \
  --start="2025-10-07T02:00:00+08:00" \
  --end="2025-10-07T06:00:00+08:00" \
  --comment="计划内维护"
```

**6. 业务时间路由**

```yaml
# 非工作时间只发送 P0/P1 告警
routes:
- match:
    severity: P0|P1
  receiver: oncall-phone
- match:
    severity: P2|P3
  receiver: slack
  active_time_intervals:
    - business_hours  # 仅工作时间发送
```

**7. 基于变化率而非绝对值**

```yaml
# ❌ 绝对值告警:流量从 100 QPS 涨到 150 QPS 就告警
- alert: HighTraffic
  expr: http_requests_rate > 150

# ✅ 变化率告警:流量突增 50% 才告警
- alert: TrafficSpike
  expr: |
    (
      http_requests_rate - http_requests_rate offset 10m
    ) / http_requests_rate offset 10m > 0.5
  for: 5m
```

**8. 定期审查和清理无效告警**

- 每月统计告警触发次数和处理率
- 删除从未导致真实问题的告警规则
- 调整经常误报的阈值

------

### **五、AlertManager 通知渠道配置示例**

```yaml
receivers:
# P0 级:电话 + 短信 + IM
- name: 'p0-oncall'
  webhook_configs:
  - url: 'https://phone-alert.company.com/api/call'  # 电话告警接口
    send_resolved: true
  - url: 'https://sms-gateway.company.com/api/send'  # 短信接口
  webhook_configs:
  - url: 'https://oapi.dingtalk.com/robot/send?access_token=xxx'  # 钉钉机器人
    send_resolved: true

# P1 级:短信 + IM
- name: 'p1-team'
  webhook_configs:
  - url: 'https://sms-gateway.company.com/api/send'
  wechat_configs:
  - corp_id: 'ww123456'
    agent_id: '1000001'
    api_secret: 'xxx'
    to_party: '运维组'

# P2 级:仅 IM
- name: 'p2-slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/xxx'
    channel: '#alerts-warning'
    title: '⚠️ P2 告警'

# P3 级:仅记录
- name: 'p3-log'
  webhook_configs:
  - url: 'http://alert-logger.svc.cluster.local/api/log'

# 路由规则
route:
  receiver: 'p2-slack'  # 默认接收器
  routes:
  - match:
      severity: P0
    receiver: p0-oncall
    continue: false
  - match:
      severity: P1
    receiver: p1-team
  - match:
      severity: P3
    receiver: p3-log
```

------

### **六、Grafana Dashboard 最佳实践**

#### **你应该创建的 Dashboard:**

1. **集群总览 Dashboard** (CEO 视角)
   - 在线设备数
   - 消息处理量(今天/本周/本月)
   - 系统可用性 SLA
   - 告警统计
2. **K8s 集群 Dashboard**
   - 节点资源使用率
   - Pod 状态分布
   - 网络流量
   - 存储使用情况
3. **应用性能 Dashboard** (APM)
   - API 响应时间 P50/P95/P99
   - 错误率
   - QPS
   - 数据库慢查询
4. **中间件 Dashboard**
   - EMQX 连接数和消息速率
   - Kafka Lag 趋势
   - Redis 命中率
   - MySQL 连接池
5. **告警历史 Dashboard**
   - 每日告警数量趋势
   - 告警分级占比
   - MTTR(平均修复时间)
   - 告警频发 Top 10

------

### **七、面试中如何回答监控问题(标准答案)**

> **"我们构建了基于 Prometheus + Grafana 的多层监控体系:**
>
> **1. 监控指标**: 覆盖基础设施(节点/K8s)、中间件(EMQX/Kafka/Redis)和应用层,关注 Google SRE 的四个黄金信号:延迟、流量、错误率、饱和度。
>
> **2. 告警分级**:
>
> - P0(致命):系统不可用,5 分钟响应,电话通知
> - P1(紧急):核心功能受损,15 分钟响应,短信通知
> - P2(重要):非核心异常,1 小时响应,IM 通知
> - P3(提示):预警信息,1 天响应,仅记录
>
> **3. 降噪措施**: 通过合理设置持续时间、告警抑制、分组、静默窗口等手段,将告警误报率控制在 5% 以下,确保每条告警都值得关注。
>
> **4. 可视化**: 创建了 5 类 Grafana Dashboard,从 CEO 视角到技术细节,支撑不同角色的监控需求。"

------

