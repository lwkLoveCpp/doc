Go 中的 `time.Sleep(d)` 用于让当前 goroutine 暂停执行指定的时间 `d`，其底层实现依赖 Go 运行时（runtime）的定时器管理机制和协程调度器，核心逻辑是**将 goroutine 挂起，等待超时后自动唤醒**。以下是具体实现细节：

### 1. 核心依赖：`runtimeTimer` 与全局定时器堆

`time.Sleep` 的底层依赖 `runtime` 包中的 `runtimeTimer` 结构体（定时器对象）和全局维护的**最小堆（min-heap）**：

- **`runtimeTimer`**：每个 `Sleep` 会关联一个 `runtimeTimer`，记录超时时间、唤醒回调等信息。
- **全局定时器堆**：所有活跃的 `runtimeTimer` 会按**到期时间**排序，堆顶是最早到期的定时器，由运行时的 `timerproc` 协程负责管理。

### 2. 执行流程：从挂起到唤醒

当调用 `time.Sleep(d)` 时，底层流程如下：

#### （1）初始化或复用 `runtimeTimer`

- 每个 goroutine（`G` 对象）会缓存一个 `runtimeTimer`（`g.timer`），首次调用 `Sleep` 时创建，后续调用直接复用（减少内存分配）。
- 重置 `runtimeTimer` 的 `when` 字段（到期时间 = 当前时间 + `d`），并设置回调函数为 `sleepWake`（唤醒当前 goroutine 的逻辑）。

#### （2）将定时器加入全局堆

- 运行时将该 `runtimeTimer` 插入全局定时器堆（按 `when` 排序），确保 `timerproc` 能快速找到最早到期的任务。

#### （3）挂起当前 goroutine

- 调用 `gopark` 函数将当前 goroutine 状态从**运行中（running）** 转为**阻塞中（waiting）**，并让出 CPU 资源。
- 调度器会切换到其他就绪的 goroutine 执行，此时 `Sleep` 所在的 goroutine 不再占用 CPU。

#### （4）超时唤醒

- 全局定时器管理协程 `timerproc` 会定期检查堆顶的 `runtimeTimer`：
    - 当堆顶定时器到期（`when ≤ 当前时间`）时，`timerproc` 会从堆中取出该定时器，并执行其回调函数 `sleepWake`。
    - `sleepWake` 调用 `goready` 函数，将被挂起的 goroutine 状态从**阻塞中**转为**就绪（runnable）**，重新加入调度队列。
- 当调度器再次调度该 goroutine 时，它会从 `Sleep` 调用处继续执行。

### 3. 关键细节：高效的定时器管理

- **避免系统调用滥用**：`timerproc` 并非轮询检查堆，而是通过**阻塞等待最早期望时间**（结合系统调用如 `epoll_wait` 或 `Sleep`）减少无效唤醒，仅在有定时器到期或新定时器插入时被唤醒。
- **轻量级挂起 / 唤醒**：`gopark` 和 `goready` 是用户态操作（无需内核态切换），仅修改 goroutine 状态和调度队列，因此 `Sleep` 的开销远低于操作系统线程的 `sleep`（后者涉及内核调度）。
- **与其他定时器复用机制**：`time.Sleep` 的 `runtimeTimer` 与 `time.Timer`、`time.Ticker` 共享同一套全局定时器堆，确保资源高效利用。