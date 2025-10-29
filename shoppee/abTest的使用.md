（1）先检查权限，如果权限申请成功，将不止有All Scenes，还会有你申请过的组
![[截屏2025-09-01 18.44.13.png]]
（2）选择对应的scene，也可以选择自己创建。进入对应scene后先创建Layer
![[截屏2025-09-01 18.47.42.png]]
（3）写个合适的名字即可。
![[截屏2025-09-01 18.48.41.png]]
（4）创建完后再创建experiment![[截屏2025-09-01 18.51.24.png]]
(5)实验是需要依托于对应layer的，你可以选择刚刚创建的layer

![[截屏2025-09-01 18.51.52.png]]
（6）实验创建好后还需要设置分组，你可以给不同的组设置流量比例。分组中的参数的意思是你通过spex访问abTest平台，平台会选择其中一个组的参数返回给你，你可以通过参数判断返回的是哪个组。
![[截屏2025-09-01 19.05.57.png]]至此，layer和layer上面的实验都创建好了。
相关概念平台上的文档有，这里不做介绍。
（5）可以点击红线处查看layerID，该页面的ID是实验ID。layerID是访问平台的重要参数。
![[截屏2025-09-01 18.55.48.png]]![[截屏2025-09-01 18.56.43.png]]
（6）如下是通过spex访问平台的示例代码，使用到的参数是scene，layerID，userID（与你创建experiment时填写的参数有关）。
```go
func GetExperimentWithBindLayer(ctx context.Context, userID int64, scene string,  
    layerIDs []int64) (map[int64]*experimentManageProto.ExpHitResult, error) {  
    req := &experimentManageProto.GetABResultWithBindLayerRequest{  
       Uid:      userID,  
       Scene:    scene,  
       LayerIds: layerIDs,  
    }  
    resp := &experimentManageProto.GetABResultWithBindLayerResponse{}  
    sCtx, cancel := timeout.SetSpexTimeout(ctx, CmdGetExperimentWithBindLayer)  
    defer cancel()  
    err := spex.DefaultSPEXClient.RPCRequest(sCtx, CmdGetExperimentWithBindLayer, req, resp)  
    if err != nil {  
       logkit.WithCtx(ctx).Error("get experiment err", zap.Error(err))  
       return nil, err  
    }  
  
    return resp.GetExpHitResults(), nil  
}
```