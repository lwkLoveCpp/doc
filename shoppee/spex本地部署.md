# [spex本地开发环境搭建](https://confluence.shopee.io/pages/viewpage.action?pageId=102440248)

[Skip to end of metadata](https://confluence.shopee.io/pages/viewpage.action?pageId=102440248#page-metadata-end)

- 由 [mingqin.tan@shopee.com](https://confluence.shopee.io/display/~mingqin.tan@shopee.com)创建, 最终由 [Lingyun Chen](https://confluence.shopee.io/display/~lingyun.chen@shopee.com)修改于 [2021-04-20](https://confluence.shopee.io/pages/diffpagesbyversion.action?pageId=102440248&selectedPageVersions=7&selectedPageVersions=8)

[Go to start of metadata](https://confluence.shopee.io/pages/viewpage.action?pageId=102440248#page-metadata-start)

Spex([Sea Platform Exchange](https://confluence.shopee.io/display/SPDEV/Sea+Platform+Architecture+Overview))是 Sea 的微服务管理平台，理念类似于  [istio](https://istio.io/). 通过一个代理 spex proxy，劫持所有进出该服务的流量，服务之间通过 spex proxy 进行通信。可以通过 config center 给 spex proxy 下发流量控制配置，来管理该服务的流量。

开发过程中，我们会依赖其它的 spex 服务的接口，spex 服务只能通过 spex proxy 代理去访问。因此在使用 dev machine 开发时，需要本机可以访问到 spex proxy.

目前并没有提供让 dev machine 使用的 spex proxy, 但我们可以将 test/live 环境的 spex 的 socket 通过 ssh map 到我们的 dev machine 上来。以下汇总一下 ssh mapping 的教程.

## 安装 socat

```bash
## For mac
brew install socat

## For Ubuntu
apt install socat

## For Arch
pacman -S socat
```

## 映射 spex socket

创建 spex 文件夹, 由于 macOS catalina 禁止用户在 / 目录下创建文件，因此我们需要换一个监听地址，比如 ~/run/spex/spex.sock

|   |
|---|
|`mkdir` `-p ~``/run/spex`<br><br>`chmod` `777 ~``/run/spex`|

启动

|                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------- |
| `socat -d -d -d UNIX-LISTEN:$HOME``/run/spex/spex``.sock,reuseaddr,fork TCP:agent-tcp.spex.``test``.shopee.io:9299` |
|                                                                                                                     |

## 让 spex agent 感知到 spex socket 地址

- 为了让 golang 程序感知到新的 socket 的地址，需要设置 `SP_UNIX_SOCKET` 环境变量, 值为我们新的 spex socket 监听地址,  `~/run/spex/spex.[sock](http://sock/run/spex/spex.sock)`  
    - VSCode 设置 debug launch.json 里的 env; 如果需要在 unit test 的时候也使用 spex，需要在 workspace 的 settings.json 里配置 `go.testEnvVars`
        
        |   |
        |---|
        |`# launch.json`<br><br>`{`<br><br>  `"version"``:` `"0.2.0"``,`<br><br>  `"configurations"``: [`<br><br>    `{`<br><br>      `"name"``:` `"Launch"``,`<br><br>      `"type"``:` `"go"``,`<br><br>      `"request"``:` `"launch"``,`<br><br>      `"mode"``:` `"auto"``,`<br><br>      `"program"``:` `"${workspaceFolder}/cmd/main.go"``,`<br><br>      `"cwd"``:` `"${workspaceFolder}"``,`<br><br>      `"env"``: {`<br><br>        `"env"``:` `"test"``,`<br><br>        `"SP_UNIX_SOCKET"``:` `"/home/ccccly/run/spex/spex.sock"``,`<br><br>      `},`<br><br>    `}`<br><br>  `]`<br><br>`}`<br><br>`# settings.json`<br><br>`{`<br><br>  `"go.testEnvVars"``: {`<br><br>    `"env"``:` `"test"``,`<br><br>    `"SP_UNIX_SOCKET"``:` `"/home/ccccly/run/spex/spex.sock"``,`<br><br>  `}`<br><br>`}`|
        
    - Goland 编辑 build configuration 和 test configuration 的 template, 如图, 注意 Goland 只能支持 absolute path, 需要把 /Users/lingyun 换成自己的 $HOME 目录  
        ![](https://confluence.shopee.io/download/attachments/102440248/Screen%20Shot%202019-12-09%20at%2011.12.07.png?version=1&modificationDate=1575861347000&api=v2)

## Reference