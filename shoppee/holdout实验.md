#### holdout实验的整体结构
![[截屏2025-09-18 19.03.07.png]]
vetical layer,feature layer和priority layer的流量是互斥的。
#### 提供的api
详细文档可看https://confluence.shopee.io/pages/viewpage.action?pageId=1957185333
使用示例：
```go
func GetABResult(ctx context.Context, scene string, region string, userID, shopID int64, layerIDs []int64) (  
    *abhit.ServiceExpHit, error) {  
    params := abparam.NewExpParamBuilder().SceneKey(scene).  
       UserID(userID).  
       Region(region).ShopID(shopID).  
       Build()  
    hits, err := abapi.GetAbClient().GetABResultWithBindLayer(ctx, params)  
    if err != nil {  
       logkit.WithCtx(ctx).Error("GetABResultWithBindLayer err", zap.Error(err))  
       return nil, err  
    }  
  
    return hits, nil  
}

```
GetABResultWithBindLayer该接口的返回值有三种情况，（1）返回该scene的vertical layer的实验参数（2）返回priority layer的实验参数（3）返回该scene的所有feature layer。由于它会返回所有feature layer，所以我们需要手动处理，筛选出我们正在做的实验对应的layer，然后根据该layer存储的值可以确定分组。
##### GetABResultWithBindLayer返回值详解
```go
type ServiceExpHit struct {  
    Hit []*BackExpHit `json:"hit"`  
}
type BackExpHit struct {  
    GroupID   int64  `json:"exp_group_id"`  
    LayerID   int64  `json:"layer_id"`  
    GroupName string `json:"exp_group_name"`  
    Parameter string `json:"parameter"`  
    LayerKey  string `json:"layer_key"`  
    LayerName string `json:"layer_name"`  
    ExpID     int64  `json:"exp_id"`  
    ExpName   string `json:"exp_name"`  
    //ExpKey    string `json:"experiment_key"`  
    //c++ add    HitGrayExp      bool              `json:"hit_gray_exp"`  
    ParameterMap    map[string]string `json:"parameter_map"`  
    ParameterTabMap map[string]string `json:"parameter_tab_map"`  
    // 0: parameter, 1: parameter tab  
    ParameterType int32 `json:"parameter_type"`  
    SceneVersion  int64 `json:"scene_version"`  
}
```
其返回值为ServiceExpHit，该结构体里面存储的是layer数组，一个BackExpHit代表一个layer。当我们有多个feature layer时，如果实验平台命中的是feature layer，ServiceExpHit里面就会存储多个BackExpHit。我们可以通过layerID分辨是哪个实验。
paramter里面就是存储的对应实验的某个group里的参数，如图所示。
![[截屏2025-09-18 19.29.47.png]]我们可以将其反序列化成结构体。通过参数可以得知命中了实验的哪个分组。

#### 总结
流程总结
![[holdout.drawio.png]]