Go 语言标准库提供了多种锁机制，用于解决并发编程中的资源竞争问题，核心围绕 `sync` 包展开。这些锁机制设计简洁且高效，适配不同的并发场景，以下是主要锁类型及使用方式：

### 1. 互斥锁（`sync.Mutex`）

`sync.Mutex` 是最基础的互斥锁，保证同一时间只有一个 goroutine 能获取锁并进入临界区，其他 goroutine 会阻塞等待。

#### 核心方法：

- `Lock()`：获取锁，若锁已被占用则阻塞。
- `Unlock()`：释放锁，唤醒等待的 goroutine。

#### 示例：

go

运行

```go
package main

import (
	"fmt"
	"sync"
)

var (
	counter int
	mu      sync.Mutex // 互斥锁
	wg      sync.WaitGroup
)

func increment() {
	defer wg.Done()
	mu.Lock()         // 加锁
	counter++         // 临界区操作
	mu.Unlock()       // 解锁
}

func main() {
	wg.Add(1000)
	for i := 0; i < 1000; i++ {
		go increment()
	}
	wg.Wait()
	fmt.Println("counter:", counter) // 输出 1000（无竞争）
}
```

#### 特点：

- 非公平锁（不保证等待顺序，可能导致饥饿）。
- 适用于锁持有时间短、竞争不激烈的场景。
- 必须保证 `Lock()` 和 `Unlock()` 成对出现，通常用 `defer` 确保释放。

### 2. 读写互斥锁（`sync.RWMutex`）

`sync.RWMutex` 是读写分离的互斥锁，允许多个读操作并发执行，但写操作与读 / 写操作互斥，适合 “读多写少” 场景。

#### 核心方法：

- **读锁**：`RLock()`（获取读锁）、`RUnlock()`（释放读锁）。
- **写锁**：`Lock()`（获取写锁）、`Unlock()`（释放写锁）。

#### 示例：

go

运行

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

var (
	data  string
	rwmu  sync.RWMutex // 读写锁
	wg    sync.WaitGroup
)

// 读操作：可以并发执行
func read(i int) {
	defer wg.Done()
	rwmu.RLock()
	fmt.Printf("reader %d: %s\n", i, data)
	time.Sleep(100 * time.Millisecond) // 模拟读耗时
	rwmu.RUnlock()
}

// 写操作：独占执行
func write() {
	defer wg.Done()
	rwmu.Lock()
	data = "updated"
	time.Sleep(500 * time.Millisecond) // 模拟写耗时
	rwmu.Unlock()
}

func main() {
	data = "initial"
	// 启动5个读goroutine
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go read(i)
	}
	// 启动1个写goroutine
	wg.Add(1)
	go write()
	// 再启动5个读goroutine
	for i := 5; i < 10; i++ {
		wg.Add(1)
		go read(i)
	}
	wg.Wait()
}
```

#### 特点：

- 读锁之间不互斥，可并发获取（提高读效率）。
- 写锁与所有读锁、写锁互斥（保证写操作的原子性）。
- 适合缓存、配置等读多写少的场景。

### 3. 自旋锁（无标准实现，需手动实现）

Go 标准库没有内置自旋锁，但可通过 `sync/atomic` 包的原子操作手动实现，适用于锁持有时间极短的场景。

#### 实现示例：

go

运行

```go
package main

import (
	"sync"
	"sync/atomic"
)

// 自旋锁实现
type SpinLock struct {
	locked uint32 // 0: 未锁定，1: 已锁定
}

// 获取锁（自旋等待）
func (sl *SpinLock) Lock() {
	for !atomic.CompareAndSwapUint32(&sl.locked, 0, 1) {
		// 空循环自旋，直到获取锁
	}
}

// 释放锁
func (sl *SpinLock) Unlock() {
	atomic.StoreUint32(&sl.locked, 0)
}

// 使用示例
var (
	spinLock SpinLock
	count    int
	wg       sync.WaitGroup
)

func add() {
	defer wg.Done()
	spinLock.Lock()
	count++
	spinLock.Unlock()
}

func main() {
	wg.Add(1000)
	for i := 0; i < 1000; i++ {
		go add()
	}
	wg.Wait()
	println(count) // 输出 1000
}
```

#### 特点：

- 不阻塞 goroutine，而是循环重试（自旋），适合锁持有时间极短（纳秒级）的场景。
- 避免了 goroutine 切换开销，但长时间自旋会浪费 CPU，需谨慎使用。

### 4. 其他同步工具（辅助锁机制）

- **`sync.WaitGroup`**：用于等待一组 goroutine 完成，配合锁使用可协调并发流程（如示例中的 `wg.Add`/`wg.Done`/`wg.Wait`）。
- **`sync.Cond`**：条件变量，用于 goroutine 间的通知机制（类似 C++ 的 `std::condition_variable`），需与互斥锁配合使用。
- **`sync.Once`**：保证代码块只执行一次（如初始化操作），内部通过原子操作和互斥锁实现。

### 总结

Go 语言的锁机制以 `sync.Mutex`（互斥）和 `sync.RWMutex`（读写分离）为核心，覆盖了大多数并发场景：

  

- 简单互斥需求用 `sync.Mutex`；
- 读多写少场景用 `sync.RWMutex`；
- 极短临界区且高并发时可考虑手动实现自旋锁。

  

使用时需注意：

  

- 锁的粒度要小（减少竞争）；
- 避免嵌套锁（防止死锁）；
- 优先使用高层同步工具（如 `channel`），锁作为底层补充。