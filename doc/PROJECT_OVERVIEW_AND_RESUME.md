# IM Gateway Server：项目说明与简历素材

> 用途：介绍项目架构、主要链路、工程价值和可用于简历的真实表述。依据当前仓库代码以及 `im_gateway_dao v0.0.15` 中的 Redis 实现整理；**不是生产容量报告**。简历中的个人职责、业务规模和效果须按实际经历补充。

## 1. 项目是什么

`im_gateway_server` 是一个用 Go / tRPC-Go 实现的多渠道消息网关。它向上连接企微 AI Bot、微信 iLink、微证券（wzq）等消息平台，向下把统一格式的用户消息交给 Agent；Agent 返回的内容再由网关按平台协议回复给用户。此外，对外提供主动推送、绑定连通性检测和本实例连接查询能力。

项目解决的核心问题不是“开发一个聊天机器人”，而是：**多种平台协议不同，Agent 不应重复处理各平台的建连、鉴权、媒体解密、消息生命周期和故障恢复**。网关将渠道差异收敛在适配层，把 Agent 的调用方式收敛在后端接口中，并管理多实例下的 Bot 接收连接。

### 一张图看架构

```text
管理/业务系统 ──tRPC──> service（Push / CheckBind / GetConnections）
                              │
                              ▼
用户 ⇄ IM 平台 ⇄ channel ⇄ runtime ──HTTP POST + SSE──> 实体 Agent
             WS/长轮询           │  └──MCP HTTP────────> 知识库工具
                                ├──DAO RPC──> MySQL（Spec / Agent 定义）
                                └──Redis────> 实例注册、租约、事件广播、去重、主动推送
```

**两类“连接”要区分**：网关与企微/wzq 维护 WebSocket、与微信进行 HTTP 长轮询；网关与 HTTP Agent 则按每条入站消息发起一次 HTTP 请求，读取 SSE 流，**不是一条常驻的 Agent 长连接**。MCP 后端调用完成后一次性产出回答，不是逐 token 流式生成。

### 模块与责任

| 模块 | 主要职责 | 代码入口 |
| --- | --- | --- |
| `cmd/`、`config/` | 加载 tRPC/网关配置、初始化依赖和服务 | `cmd/main.go`、`config/config.go` |
| `channel/` | 定义 `GatewayChannel`、`InboundMessage`、`OutboundMessage` 和平台适配工厂 | `channel/channel.go`、`channel/defines.go`、`channel/factory.go` |
| `channel/wecom/`、`channel/wechat/`、`channel/wzq/` | 各平台建连/收发、消息转换、特有协议处理 | 各渠道目录 |
| `runtime/` | 消费绑定事件、抢租约与续租、分片对账、入站路由、出站投递 | `runtime/runtime.go`、`runtime/reconcile.go`、`runtime/inbound.go` |
| `agent/` | 按名称发现后端，接入 HTTP SSE / MCP，实现 Agent 配置周期刷新 | `agent/agent.go`、`agent/agent_manager.go`、`agent/http_backend.go`、`agent/mcp_backend.go` |
| `storage/` | 通过 DAO RPC 访问渠道绑定 `Spec`，转换 DAO/网关模型 | `storage/spec.go` |
| `service/`、`idl/` | 三个对外 tRPC 接口及协议 | `service/gateway_service.go`、`idl/im_gateway_server.proto` |

## 2. 核心数据模型与配置关系

- `GatewayBotId`：统一 Bot 键，形式为 `{channel_type}:{bot_id}`，串起绑定、租约、事件和出站投递。
- `GatewaySpec`：某个 Bot 的渠道类型、渠道凭证、状态与 `AgentID`；通过 DAO RPC 持久化（DAO 背后为 MySQL），**不是存储在 Redis 的 `gateway:spec:*`**。`Spec.AgentID` 对应 Agent 的 `Name`。
- `Agent`：名称、后端类型、目标地址、超时、路由元信息及可注入的 `call_metadata`；网关从 DAO 拉取，建立本地 backend 缓存。
- `InboundMessage`：统一承载用户文本/原始报文、附件、来源会话、平台消息 ID、渠道元数据；`OutboundMessage`：统一承载回复目标、消息形态、流式帧类型及回复关联 ID。
- Redis：用于**运行时数据**，包括实例注册、Bot 租约、绑定事件 Pub/Sub、入站去重和主动推送 Pub/Sub；不要与 DAO 中的 `Spec` 持久化混为一谈。

## 3. 核心链路：从绑定到回复

### 3.1 Bot 接管、抢租约与故障恢复

1. 管理侧写入/更新 `Spec` 后发布事件；网关实例通过 Redis Pub/Sub 订阅。事件为**广播**，每个实例在一个串行 `consumeLoop` 中处理事件。
2. 每个实例尝试对同一 `GatewayBotId` 调用 `Acquire`。底层使用 Redis `SET NX`；通常一个赢家获得租约并创建对应渠道，其他实例抢不到就跳过。赢家另外写租约索引供删除对账使用。
3. 赢家调用 `GatewayChannel.Start(Handler)`，并订阅该 Bot 的主动推送；Bot 生命周期内按 `max(1s, receiver_ttl/3)` 心跳续租。默认 `receiver_ttl=30s`，即约每 10s 续租。租约丢失或渠道终止时停止渠道、取消出站消费者、释放租约。
4. 每个网关实例约每 20s 注册实例心跳；60s 未更新的实例被清理。按存活实例序号划分固定 slot 区间，每个实例周期扫描自己负责的 `Spec`；发现 `Spec` 有而租约无时发布建连事件（默认扫描间隔 30s）。删除对账约每小时一次。

**关键并发口径**：单个网关实例的事件消费和 `Acquire` 是串行的；当有 \(N\) 个实例订阅同一事件时，单条事件最多引发 \(N\) 次并行的抢租约请求（通常 1 次成功，\(N-1\) 次失败）。扫描虽按 slot 分片，**事件消费尚未按 slot 过滤**，因此冷启动/故障恢复时存在约 \(N\) 倍 Redis `SET NX` 请求放大。这是架构权衡，不是“每台实例同时抢无限个 Bot”。

边界：`SET NX` 的单次抢占是原子的；但当前依赖里的续租为“读 token → 写回 TTL”，释放为“读 token → 删除”，**检查和修改未合为原子 CAS**。因此不能对外承诺任何时序下都绝对无双主。事件 Pub/Sub 丢消息时靠周期对账补偿，恢复时间受 TTL、对账间隔及下游建连耗时影响。

### 3.2 用户消息与 Agent 响应

```text
平台消息 → 渠道解析/解密 → InboundMessage
       → runtime 按 Bot 查询当前 Spec.AgentID
       → Redis 按平台消息 ID 去重
       → AgentBackend.StreamChat(ctx, inbound, emit)
       → 每个 emit(OutboundMessage) 交给原渠道 Send
       → 渠道按平台规则展示 delta、完成帧或错误
```

- 每条消息单独启动 goroutine，避免阻塞平台接收循环；Agent 请求按配置设置超时，默认 5 分钟。**当前没有统一入站并发闸门**。
- HTTP Agent 调用 `POST /v1/gateway/stream`，请求为统一 JSON；响应 `text/event-stream` 中每个 `data:` 是一条完整 `OutboundMessage` JSON，`completed` 帧用于结束流。按 `GatewayBotId:ChatID` 构造一致性哈希键，以减少同一会话被路由到不同 Agent 实例的概率。
- Agent 级 `call_metadata` 合入入站消息；`attachments` / `metadata` 归一化为空数组/对象，避免 `null` 与 Agent 的 JSON 校验不兼容。
- MCP 后端当前执行固定知识库 `initialize → tools/call`，将结果作为完整 `message` 和 `completed` 两帧返回；只转发查询文本，不具备 HTTP Agent 的完整入站消息与实时 SSE 流式能力。
- Redis 去重发生在调用 Agent **之前**。Agent 报错会尝试返回错误帧；若平台重投相同 ID，则去重仍可能拦住重试。Agent 的出站 `Send` 失败只记录日志，不做自动补发。

### 3.3 主动推送与连接观测

`Push` 是不依赖用户入站的单独路径：检查 Bot 租约；无租约时确认 `Spec` 是否存在并发布建连事件；随后将消息发布到 Bot 对应的 Redis Pub/Sub 出站频道，由持有渠道连接的实例订阅并 `Send`。`PushRsp.Code=0` 代表**发布调用成功**，不是平台确认收到。**当前出站 Pub/Sub 不持久化，尚无 ACK/失败重试；无订阅者时消息可能丢失。**

`CheckBind` 在不启动运行态长连接的前提下校验平台配置；`GetConnections` 返回**当前实例**的真实连接快照，可报告企微、wzq 的 WS 连接与最后活跃时间，**不将微信长轮询计作 WS 连接**。

## 4. 三个渠道的差异化设计

| 渠道 | 接入方式 | 特殊处理 | 可陈述的价值 |
| --- | --- | --- | --- |
| 企微 AI Bot（`wecom`） | WS 订阅、心跳与重连 | 回调解析；群聊/私聊策略；媒体下载解密；回复流累积；达到 **50 字节或 50ms** 批量刷新；平台请求与 ACK 关联 | 将平台实时交互和 Agent 高频增量帧解耦，减少逐 token 平台请求，并保留流式体验 |
| 微信 iLink（`wechat`） | HTTP 长轮询 | 游标维护、重试、会话失效后停用绑定；正文增量先累积再按渠道能力发文本，忽略不支持的思考/工具展示 | 在共享的消息模型下适配非 WebSocket 平台，无需 Agent 感知轮询协议 |
| 微证券（`wzq`） | 带 token 的 WS | 入站目前统一 `raw` 透传；出站支持 `raw` 原样透传及 `completed → done` 信令 | 在平台协议尚未完全统一时保留可用的低侵入接入能力；`done` 使平台清理会话处理中状态 |

通用模型里的 `image/file/voice/video` 是**协议表达能力**，不等于每个渠道都完整实现了所有类型的出站发送。描述业务覆盖时应按具体渠道验证。

## 5. 工程价值：问题、方案与能证明的收益

| 问题 | 项目中的方案 | 价值表述（不依赖虚构数据） | 证据 |
| --- | --- | --- | --- |
| 不同平台的建连/报文/消息类型互不兼容 | `GatewayChannel` 接口 + 工厂注册 + 统一双向消息模型 | 新增渠道主要在适配层实现，不要求 Agent 直接接入每个平台；三种平台复用路由主链路 | `channel/channel.go`、`channel/factory.go`、`channel/defines.go` |
| 多实例 Bot 接管与实例故障后的恢复 | Redis 抢租约、心跳续租、实例注册、slot 分片对账 | 避免正常情况下各实例为同一 Bot 重复持有连接；实例退出后通过租约过期与对账重新接管 | `runtime/runtime.go`、`runtime/reconcile.go` |
| Agent 形态和部署地址差异 | `AgentBackend` 抽象；HTTP SSE 与 MCP 后端；DAO 配置周期刷新 | 渠道层无需处理 Agent 协议；同一 Bot 的 Agent 绑定查询可按消息生效（后端列表约每分钟刷新） | `agent/agent.go`、`agent/agent_manager.go`、`runtime/inbound.go` |
| 大模型增量消息与平台接口能力不匹配 | 标准化 `content_type`（正文/思考/完成等）；企微批量刷流、微信缓冲、wzq 完成信令 | 一套 Agent 事件语义在不同平台上以适合各自协议的形式展示 | `channel/defines.go`、各渠道 `Send` 实现 |
| 平台媒体格式不适合直接供 Agent 使用 | 渠道内下载/解密，标准化附件格式 | Agent 更聚焦内容处理；不必重复集成企微媒体加密协议 | `channel/wecom/`、`channel/defines.go` |
| 线上多实例连接状态难以定位 | `GetConnections` 返回本实例连接地址、建立时间和最近活跃时间 | 为管理侧汇总实际 WS 连接状态提供数据基础 | `runtime/connection.go`、`service/gateway_service.go` |

以上是**代码支持的设计价值**，不等于已经量化的业务收益。简历若写“降低平台请求 X%”“恢复耗时缩短 X%”“承载 X 万 Bot”，需提供上线前后监控或压测记录。尤其不要将 Agent HTTP 压测误写成抢租约压测。

### 抢租约的容量该如何讲

- `N` 个实例时，单事件会广播到 `N` 个消费者，触发最多 `N` 次 `Acquire`；只有获取成功的实例建连。因此单次争抢的**全局峰值并发约为实例数**，而每实例该消费循环内的 `Acquire` 在途数为 1。
- 对账扫描按实例分摊 slot，但逐个 `Spec` 执行串行 `HasLease`；耗时近似受每实例扫描条目数与 Redis 往返时延影响。实例越多，扫描范围越小，却会放大事件争抢的 Redis 请求数。
- 默认 30s 租约、约 10s 续租；假设有 `M` 个存活 Bot，**仅续租**稳态约为 `M/10` 次心跳调用每秒，当前 DAO 每次心跳至少涉及一次读取和一次写入，折合至少约 `M/5` 次 Redis 命令/秒（不含其它请求）。
- 先前使用本地纯 Go Redis 模拟器观察过单 key 多实例抢占和事件广播；这**不能代表生产 Redis、真实建连速度或生产 Bot 容量**。本仓库保留的 `agent/concurrency_bench_test.go` 与 `channel/wecom/concurrency_bench_test.go` 也分别只覆盖本地 mock Agent 链路和 mock 企微 WS，**不覆盖完整租约系统/真实平台/生产 DAO**。

## 6. 当前限制与可落地的下一步

1. **租约原子性**：将续租和释放的 token 检查与修改合成 Lua CAS，并检查 `Acquire` 后索引 `ZADD` 的错误，降低租约交替期状态不一致风险；这属于**待优化项**，不能写成已实现。
2. **抢租约写放大**：当前广播后由所有实例抢占；可在实例侧增加按存活列表计算的 slot 过滤，或按 slot 定向路由事件，并设计实例上下线/分片变化时的回退机制。不能只声称“改为定向后仍与全员抢占等价”：接管时序与容错需重新验证。
3. **对账与实例心跳隔离**：`scanLoop` 同一个循环执行 20s 实例心跳及定时对账；大规模扫描阻塞会使心跳延后。可拆分任务、批量/并行 `HasLease`、增加超时与监控。
4. **主动推送可靠性**：当前 DAO 版本使用 Pub/Sub，即发即失；如需送达保证，应引入可持久化队列、消费 ACK、失败重试和幂等键，并明确“成功”语义。
5. **资源与异常处理**：入站 goroutine 数无统一上限；企微同一 `req_id` 的并发回复可能覆盖 `pending` 等待者，需考虑请求关联串行化、超时与连接关闭竞态；媒体临时文件的清理与敏感数据日志也应纳入治理。

这些是可讨论的技术债和优化方向，**不应以“已完成优化”写进简历**。具体问题的排查记录可回看 `TODO.md`，但该文件部分描述可能与当前实现不同，以代码和 DAO 依赖版本为准。

## 7. 简历写法：根据真实个人职责选择

> 下面是**项目事实支持的写法模板**，不自动代表你本人负责全部模块。根据本人参与的代码与成果删选，不能把团队成果或待优化项写成个人已完成。

### 简历项目概述（可精简到 1 行）

**多渠道智能体消息网关｜Go、tRPC-Go、Redis、MySQL（DAO RPC）、WebSocket、SSE、MCP**：面向企微 AI Bot、微信 iLink、微证券实现统一接入，承载 Bot 连接管理、用户消息到 Agent 的路由与多渠道回复，并提供主动推送及连接观测接口。

### 工作亮点候选（选择确实亲自完成的 2～4 条）

- **多渠道抽象**：设计/实现 `GatewayChannel` 适配接口与统一收发消息模型，将企微 WS、微信长轮询、微证券 WS 的协议差异收敛到渠道层，复用入站路由与 Agent 调用链路。
- **多实例连接管理**：基于 Redis `SET NX` 租约、周期续租与实例注册管理 Bot 接收连接；使用 slot 分片对账补偿建连事件丢失，并处理实例退出后的连接清理与重新接管。
- **Agent 流式接入**：对接 HTTP SSE Agent，将统一入站消息映射到 `/v1/gateway/stream`，逐帧解析增量、完成/错误事件，并按 Bot+会话一致性哈希路由 Agent 实例；通过渠道适配差异化渲染。
- **企微交互优化**：实现企微回复增量攒批（50 字节或 50ms 触发刷新）、媒体下载解密及平台 ACK 关联，减少对平台逐 token 请求，同时支持流式回复。
- **异构后端与可观测**：抽象 HTTP/MCP Agent backend，接入按 DAO 配置分钟级刷新；提供 `CheckBind` 和 `GetConnections` 接口，辅助绑定验证与多实例连接排障。

### 可量化信息：先收证据再填写

| 指标 | 可填内容（未测到的不要填） | 建议证据 |
| --- | --- | --- |
| 接入范围 | 3 种渠道；2 种 Agent backend；3 个对外 RPC | 当前仓库代码即可核验；这是**功能数量**而非业务效果 |
| 活跃连接与规模 | 生产 Bot 数、实例数、WS 连接数、峰值增长 | 实际部署/监控截图，区分微信长轮询与 WS |
| 故障恢复 | 宕机后租约过期与成功重建的 P50/P95 | 故障演练记录、日志与指标；不能用 TTL 直接充当实测时间 |
| 抢租约容量 | 不同实例数下的冲突率、Redis QPS、全量恢复时间 | 真 Redis + 真实 DAO/平台或可说明边界的集成压测 |
| 消息体验 | 首帧耗时、完成耗时、企微平台消息发送次数 | 灰度/线上数据、优化前后同口径对比 |
| 稳定性 | 发送失败率、去重率、丢事件后的对账修复量 | 线上报表或压测记录；勿写“可靠投递 100%” |

### 面试解释重点

1. **为什么用租约而不是让所有实例直接连 Bot？** 避免正常情况下重复接管；依赖 `SET NX` 抢占和 TTL 实现故障后的重新分配，事件广播只负责触发，周期对账兜底事件丢失。
2. **分片和抢租约是什么关系？** 分片仅限制每实例扫描的 `Spec` 区间；绑定事件仍广播给所有实例，因此单事件 Redis 争抢次数随实例数增长。这是下一步可优化的写放大点。
3. **SSE 与 WS 的角色？** WS 是网关与部分 IM 平台保持的渠道连接；SSE 是网关按消息调用 HTTP Agent 时读取的流式响应；微信使用 HTTP 长轮询，MCP 后端不是逐帧回答。
4. **主动推送保证了什么？** 当前 `Push` 成功只表示 Pub/Sub 发布成功，没有端到端 ACK；当时无订阅者可能丢消息，不能声称持久化/至少一次/Exactly-once。
5. **如果重做会优先优化什么？** 租约续租/释放的原子 CAS、对账扫描与实例心跳隔离、广播抢租约的写放大、主动推送可靠性与入站并发限制。

## 8. 事实核对与文档范围

- 当前实现以 `storage/spec.go` 为准，`Spec` 来自 DAO RPC；根目录 `README.md` 有“Spec 存 Redis”的旧口径，不可照搬。
- 当前对外接口以 `idl/im_gateway_server.proto` 为准，有 `Push`、`CheckBind`、`GetConnections` 三个。
- 当前出站语义以 `runtime/runtime.go` 和 `im_gateway_dao v0.0.15` 的 `repo/redis/outbound_message_queue.go` 为准，使用 Pub/Sub；旧文档对“队列”的描述并不意味着落盘或有 ACK。
- 本文仅描述**项目实现能力**，不推断个人所有权、生产部署范围、线上性能或最终业务收益。求职对外版本应按公司保密要求隐去内部服务名、目标地址、客户数据等信息。
