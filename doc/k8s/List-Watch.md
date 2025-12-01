你想了解 Nginx Ingress Controller 如何通过 K8s 的 List-Watch 机制实现对资源的实时监控，这是它能动态适配后端变化的核心原理。下面我会从机制原理、具体实现和代码层面详细拆解。

### 一、K8s List-Watch 机制基础

K8s 的 List-Watch 是客户端与 API Server 之间的**长连接异步通信机制**，用于实时感知资源变化：

1. **List**：客户端首先发送一次 `List` 请求，获取资源的全量数据（如所有 Ingress、Service、Endpoints）；
2. **Watch**：接着建立长连接，发送 `Watch` 请求，API Server 会通过这个连接**推送**后续资源的增量变化（创建、更新、删除）；
3. **重连机制**：如果连接断开，客户端会通过**资源版本号（resourceVersion）** 重新发起 Watch，避免全量拉取。

![[截屏2025-11-27 19.20.08.png]]
### 二、Nginx Ingress Controller 的监控实现

Nginx Ingress Controller 基于 K8s 官方的 `client-go` 库实现 List-Watch，主要监控以下核心资源：

#### 1. 监控的资源类型

- **Ingress 资源**：监听所有 Namespace 的 Ingress 规则变化（路由规则、TLS 配置等）；
- **Service/Endpoints**：监听与 Ingress 关联的 Service 和对应的 Endpoints（后端 Pod IP 变化）；
- **Secret**：监听 TLS 证书对应的 Secret 变化（自动更新 HTTPS 配置）；
- **ConfigMap**：监听控制器自身的配置 ConfigMap（如 Nginx 模板、限流规则）。

#### 2. 具体实现步骤（代码层面）

Ingress Controller 启动时会初始化多个 `Informer`（基于 List-Watch 的封装）：

```go
// 简化的核心代码逻辑
func main() {
    // 1. 创建 K8s 客户端
    clientset, _ := kubernetes.NewForConfig(config)
    
    // 2. 初始化 Ingress Informer（监听 Ingress 资源）
    ingressInformer := informers.NewIngressInformer(
        clientset,
        metav1.NamespaceAll, // 监听所有 Namespace
        time.Minute*30,      // 重新同步间隔
        cache.Indexers{},
    )
    
    // 3. 注册事件处理函数
    ingressInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc:    onIngressAdd,    // 新增 Ingress 时触发
        UpdateFunc: onIngressUpdate, // 更新 Ingress 时触发
        DeleteFunc: onIngressDelete, // 删除 Ingress 时触发
    })
    
    // 4. 启动 Informer（后台 goroutine 运行 List-Watch）
    stopCh := make(chan struct{})
    defer close(stopCh)
    go ingressInformer.Run(stopCh)
    
    // 同理，初始化 Service/Endpoints/Secret Informer...
}

// Ingress 新增事件处理函数
func onIngressAdd(obj interface{}) {
    ingress := obj.(*v1.Ingress)
    log.Printf("Ingress %s/%s 已新增", ingress.Namespace, ingress.Name)
    // 触发 Nginx 配置重新生成
    generateNginxConfig()
}
```

#### 3. 事件处理流程

当监控的资源发生变化时，Controller 会执行以下操作：

1. **接收事件**：Informer 通过 Watch 连接收到 API Server 推送的事件（如 Ingress 创建、Endpoints 更新）；
2. **更新本地缓存**：将变化同步到本地缓存（Store），避免每次查询都访问 API Server；
3. **生成新配置**：调用配置生成器，结合所有资源的最新状态生成新的 Nginx 配置文件（`nginx.conf`）；
4. **热加载配置**：通过 `nginx -s reload` 或 `kill -HUP` 信号热加载配置，无需重启 Nginx 进程。

### 三、关键组件与技术细节

#### 1. Informer 与 Workqueue

- **Informer**：封装了 List-Watch 逻辑，提供事件回调接口，内部维护本地缓存；
- **Workqueue**：事件处理的异步队列，避免并发冲突（如多个资源同时变化时，串行处理配置生成）。

#### 2. 资源版本号（resourceVersion）

Watch 请求会携带上一次的 `resourceVersion`，API Server 仅返回该版本之后的变化，减少数据传输：

```http
GET /apis/networking.k8s.io/v1/ingresses?watch=true&resourceVersion=12345
```

#### 3. 容错机制

- **重连**：Watch 连接断开时，Informer 会自动重试，并使用最新的 `resourceVersion` 恢复监听；
- **全量同步**：定期执行 List 请求全量同步资源，避免增量更新导致的缓存不一致；
- **限流与退避**：API Server 对 Watch 请求有限流，Informer 会通过指数退避策略重试。

### 四、监控过程示例（以 Endpoints 变化为例）

1. **Pod 扩缩容**：用户执行 `kubectl scale deployment backend --replicas=3`，新增 1 个 Pod；
2. **Endpoints 更新**：K8s 自动更新 `backend` Service 对应的 Endpoints，添加新 Pod 的 IP；
3. **事件推送**：API Server 通过 Watch 连接将 Endpoints 更新事件推送给 Ingress Controller；
4. **配置更新**：Controller 感知到 Endpoints 变化，重新生成 Nginx upstream 配置，添加新的后端 IP；
5. **热加载**：执行 `nginx -s reload`，新配置生效，请求可转发到新 Pod。

### 总结

- **核心机制**：Nginx Ingress Controller 通过 `client-go` 的 Informer 实现 List-Watch，先全量拉取资源，再监听增量变化；
- **监控对象**：主要监听 Ingress、Service、Endpoints、Secret 等资源，确保路由规则和后端节点实时同步；
- **处理流程**：资源变化 → 事件回调 → 更新缓存 → 生成新配置 → 热加载 Nginx，实现无感知动态更新。

这种机制让 Ingress Controller 能实时感知 K8s 集群的动态变化，无需人工干预即可适配后端服务的扩缩容、重启等操作。