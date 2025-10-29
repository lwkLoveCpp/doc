
### mac安装
```bash、
brew install protobuf
brew install protoc-gen-go
brew install protoc-gen-o-grpc
```
生成代码
```go
protoc --go_out=. service.proto
```
### 问题记录
##### 问题1
protoc-gen-go: unable to determine Go import path for "service.proto"

Please specify either:
        • a "go_package" option in the .proto source file, or
        • a "M" argument on the command line.

See https://protobuf.dev/reference/go/go-generated#package for more information.
###### 解决办法
在proto文件里加入
option go_package = "./;pb";
###### 解释
option go_package = "./proto;pb";
;前面的参数指定生成的go文件的位置
;后的参数指定go文件的包名。
##### 问题2
proto和protoc版本兼容问题

在 Go Protobuf 库中，`ProtoMessage` 接口（通过 `ProtoReflect()` 方法实现）的引入是从 **v1.20.0** 版本开始的。这是一个重要的版本分界线，标志着从旧版 API 向新版反射系统的过渡。

###### **版本关键节点**

###### **1. 旧版 API（v1.19.x 及之前）**

- 使用 `github.com/golang/protobuf` 包
- 核心接口是 `proto.Message`，仅需实现空方法 `ProtoMessage()`
- 示例：
    
    go
    
    ```go
    import "github.com/golang/protobuf/proto"
    
    type MyMessage struct {
        // 字段定义
    }
    
    // 实现 proto.Message 接口（空方法）
    func (m *MyMessage) ProtoMessage() {}
    ```
    
      
    

###### **2. 过渡版本（v1.20.0 - v1.28.x）**

- 引入新包 `google.golang.org/protobuf`
- 新增 `protoreflect.ProtoMessage` 接口，要求实现 `ProtoReflect()` 方法
- 生成的代码同时兼容新旧接口，但推荐使用新接口
- 示例：
    
    go
    
    ```go
    import "google.golang.org/protobuf/proto"
    import "google.golang.org/protobuf/reflect/protoreflect"
    
    func (m *MyMessage) ProtoReflect() protoreflect.Message {
        // 返回反射对象
    }
    ```
    
      
    

###### **3. 完全迁移（v1.29.x 及之后）**

- 全面采用新反射系统，旧版 API 不再维护
- 生成的代码仅实现 `protoreflect.ProtoMessage` 接口
- `protoc-gen-go` 插件版本需 >= v1.29.0
    
    - 旧版（v1.19.x）：生成的 `.pb.go` 文件包含 `ProtoMessage()` 方法
    - 新版（v1.29.x）：生成的 `.pb.go` 文件包含 `ProtoReflect()` 方法，且无 `ProtoMessage()` 方法
新版本的proto需要与新版本的protoc相对应，新版本的proto在调用marshal时要求message有ProtoReflect，这是旧版本生成代码时没有的方法。
降低proto版本的方式：引用时使用“"github.com/golang/protobuf/proto"
新版本使用"google.golang.org/protobuf/proto"
