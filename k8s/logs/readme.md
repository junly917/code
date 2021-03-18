## 使用Fluent-bit收集k8s内的Pod日志

### 流程

```
k8s(pod) <-- fluent-bit --> Elasticsearch <-- kibana
```

### 版本信息

```
k8s: 1.16.4
fluent-bit:1.7.2
ES: 7.5.1
kibana: 7.5.1
```

部署方式：

```
fluent-bit使用daemonset在所有的节点部署, 收集/var/log/container/下面的所有日志
fluent-cm 为收集日志的配置规则(包含INPUT/filter/output)
es部署在k8s外面，使用endpoints来访问集群
kibana使用Pod的形式进行部署
```

部署过程

```
kubectl apply -f .
```

