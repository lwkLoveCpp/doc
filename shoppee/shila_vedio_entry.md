```go
type ProactiveDistributionResponse struct {  
    state         protoimpl.MessageState  
    sizeCache     protoimpl.SizeCache  
    unknownFields protoimpl.UnknownFields  
  
    Header   *ResponseHeader                 `protobuf:"bytes,1,opt,name=header,proto3,oneof" json:"header,omitempty"`  
    Messages []*ProactiveDistributionMessage `protobuf:"bytes,2,rep,name=messages,proto3" json:"messages,omitempty"`  
}
type ProactiveDistributionMessage struct {  
    state         protoimpl.MessageState  
    sizeCache     protoimpl.SizeCache  
    unknownFields protoimpl.UnknownFields  
  
    MessageType        *string                     `protobuf:"bytes,2,opt,name=message_type,json=messageType,proto3,oneof" json:"message_type,omitempty"` // 101, 102, ...  
    Title              *string                     `protobuf:"bytes,3,opt,name=title,proto3,oneof" json:"title,omitempty"`  
    Message            *string                     `protobuf:"bytes,4,opt,name=message,proto3,oneof" json:"message,omitempty"`  
    FollowUpQuestion   []string                    `protobuf:"bytes,5,rep,name=follow_up_question,json=followUpQuestion,proto3" json:"follow_up_question,omitempty"`  
    ItemInfo           *KspItemInfo                `protobuf:"bytes,6,opt,name=item_info,json=itemInfo,proto3,oneof" json:"item_info,omitempty"`  
    ItemComparisonInfo *ItemComparisonCardResponse `protobuf:"bytes,7,opt,name=item_comparison_info,json=itemComparisonInfo,proto3,oneof" json:"item_comparison_info,omitempty"`  
}
type KspItemInfo struct {  
    state         protoimpl.MessageState  
    sizeCache     protoimpl.SizeCache  
    unknownFields protoimpl.UnknownFields  
  
    ItemId                 *int64   `protobuf:"varint,1,opt,name=item_id,json=itemId,proto3,oneof" json:"item_id,omitempty"`  
    Category               *string  `protobuf:"bytes,2,opt,name=category,proto3,oneof" json:"category,omitempty"`  
    ModelId                *int64   `protobuf:"varint,3,opt,name=model_id,json=modelId,proto3,oneof" json:"model_id,omitempty"`  
    Currency               *string  `protobuf:"bytes,4,opt,name=currency,proto3,oneof" json:"currency,omitempty"`  
    OriginalPrice          *int64   `protobuf:"varint,5,opt,name=original_price,json=originalPrice,proto3,oneof" json:"original_price,omitempty"`  
    DiscountPrice          *int64   `protobuf:"varint,6,opt,name=discount_price,json=discountPrice,proto3,oneof" json:"discount_price,omitempty"`  
    DiscountPercentage     *float32 `protobuf:"fixed32,7,opt,name=discount_percentage,json=discountPercentage,proto3,oneof" json:"discount_percentage,omitempty"`  
    PromotionType          *int64   `protobuf:"varint,8,opt,name=promotion_type,json=promotionType,proto3,oneof" json:"promotion_type,omitempty"`  
    DisplaySoldCount       *int64   `protobuf:"varint,9,opt,name=display_sold_count,json=displaySoldCount,proto3,oneof" json:"display_sold_count,omitempty"`  
    DisplaySoldCountText   *string  `protobuf:"bytes,10,opt,name=display_sold_count_text,json=displaySoldCountText,proto3,oneof" json:"display_sold_count_text,omitempty"`  
    Stock                  *int64   `protobuf:"varint,11,opt,name=stock,proto3,oneof" json:"stock,omitempty"`  
    KspId                  *int32   `protobuf:"varint,12,opt,name=ksp_id,json=kspId,proto3,oneof" json:"ksp_id,omitempty"`  
    Title                  *string  `protobuf:"bytes,13,opt,name=title,proto3,oneof" json:"title,omitempty"`  
    EndTime                *int64   `protobuf:"varint,14,opt,name=end_time,json=endTime,proto3,oneof" json:"end_time,omitempty"`  
    RatingStar             *float32 `protobuf:"fixed32,15,opt,name=rating_star,json=ratingStar,proto3,oneof" json:"rating_star,omitempty"`  
    PositiveRating         *float32 `protobuf:"fixed32,16,opt,name=positive_rating,json=positiveRating,proto3,oneof" json:"positive_rating,omitempty"`  
    PositiveRatingText     *string  `protobuf:"bytes,17,opt,name=positive_rating_text,json=positiveRatingText,proto3,oneof" json:"positive_rating_text,omitempty"`  
    UserPortrait           []string `protobuf:"bytes,18,rep,name=user_portrait,json=userPortrait,proto3" json:"user_portrait,omitempty"`  
    TagName                []string `protobuf:"bytes,19,rep,name=tag_name,json=tagName,proto3" json:"tag_name,omitempty"`  
    ItemName               *string  `protobuf:"bytes,20,opt,name=item_name,json=itemName,proto3,oneof" json:"item_name,omitempty"`  
    ModelName              *string  `protobuf:"bytes,21,opt,name=model_name,json=modelName,proto3,oneof" json:"model_name,omitempty"`  
    ModelImage             *string  `protobuf:"bytes,22,opt,name=model_image,json=modelImage,proto3,oneof" json:"model_image,omitempty"`  
    SavedPrice             *int64   `protobuf:"varint,23,opt,name=saved_price,json=savedPrice,proto3,oneof" json:"saved_price,omitempty"`  
    DiscountPercentageText *string  `protobuf:"bytes,24,opt,name=discount_percentage_text,json=discountPercentageText,proto3,oneof" json:"discount_percentage_text,omitempty"`  
    ShopId                 *int64   `protobuf:"varint,25,opt,name=shop_id,json=shopId,proto3,oneof" json:"shop_id,omitempty"`  
}
```

```go
type PopupResult struct {  
    FollowUpQuestions []*FollowupQuestions     `protobuf:"bytes,1,rep,name=follow_up_questions,json=followUpQuestions" json:"follow_up_questions,omitempty"`  
    NotiMultiItem     []*ItemRecommendItemInfo `protobuf:"bytes,2,rep,name=noti_multi_item,json=notiMultiItem" json:"noti_multi_item,omitempty"`  
    NotiSingleItem    *ItemRecommendItemInfo   `protobuf:"bytes,3,opt,name=noti_single_item,json=notiSingleItem" json:"noti_single_item,omitempty"`  
    MetaData          *PopupMetaData           `protobuf:"bytes,4,opt,name=meta_data,json=metaData" json:"meta_data,omitempty"`  
    CardRank          []int32                  `protobuf:"varint,5,rep,name=card_rank,json=cardRank" json:"card_rank,omitempty"`  
    ItemRename        *string                  `protobuf:"bytes,6,opt,name=item_rename,json=itemRename" json:"item_rename,omitempty"`  
    BulletPoints      []string                 `protobuf:"bytes,7,rep,name=bullet_points,json=bulletPoints" json:"bullet_points,omitempty"`  
    RequestId         *string                  `protobuf:"bytes,8,opt,name=request_id,json=requestId" json:"request_id,omitempty"`  
    DebugInfoList     *string                  `protobuf:"bytes,9,opt,name=debug_info_list,json=debugInfoList" json:"debug_info_list,omitempty"`  
    ItemShortName     *string                  `protobuf:"bytes,10,opt,name=item_short_name,json=itemShortName" json:"item_short_name,omitempty"`  
    ItemSourceType    *int32                   `protobuf:"varint,11,opt,name=item_source_type,json=itemSourceType" json:"item_source_type,omitempty"`  
    SpecificDate      *string                  `protobuf:"bytes,12,opt,name=specific_date,json=specificDate" json:"specific_date,omitempty"`  
    XXX_unrecognized  []byte                   `json:"-"`  
}
type PopupMetaData struct {  
    Prologue         *string `protobuf:"bytes,1,opt,name=prologue" json:"prologue,omitempty"`  
    FrontierMd       *string `protobuf:"bytes,2,opt,name=frontier_md,json=frontierMd" json:"frontier_md,omitempty"`  
    XXX_unrecognized []byte  `json:"-"`  
}
type ItemRecommendItemInfo struct {  
    ItemId           *int64  `protobuf:"varint,1,opt,name=item_id,json=itemId" json:"item_id,omitempty"`  
    ShopId           *int64  `protobuf:"varint,2,opt,name=shop_id,json=shopId" json:"shop_id,omitempty"`  
    ModelId          *int64  `protobuf:"varint,3,opt,name=model_id,json=modelId" json:"model_id,omitempty"`  
    ItemName         *string `protobuf:"bytes,4,opt,name=item_name,json=itemName" json:"item_name,omitempty"`  
    Bullet           *string `protobuf:"bytes,5,opt,name=bullet" json:"bullet,omitempty"`  
    XXX_unrecognized []byte  `json:"-"`  
}
```

```go
type GetGuideInfoResponse struct {  
    Code             *int32                     `protobuf:"varint,1,opt,name=code" json:"code,omitempty"`  
    Msg              *string                    `protobuf:"bytes,2,opt,name=msg" json:"msg,omitempty"`  
    Data             *GetGuideInfoResponse_Data `protobuf:"bytes,3,opt,name=data" json:"data,omitempty"`  
    XXX_unrecognized []byte                     `json:"-"`  
}
type GetGuideInfoResponse_Data struct {  
    IconQuestion     *string          `protobuf:"bytes,1,opt,name=icon_question,json=iconQuestion" json:"icon_question,omitempty"`  
    CommentQuestion  *string          `protobuf:"bytes,2,opt,name=comment_question,json=commentQuestion" json:"comment_question,omitempty"`  
    InstantDisplay   *bool            `protobuf:"varint,3,opt,name=instant_display,json=instantDisplay" json:"instant_display,omitempty"`  
    ToastPrologueExp *bool            `protobuf:"varint,4,opt,name=toast_prologue_exp,json=toastPrologueExp" json:"toast_prologue_exp,omitempty"`  
    AnimationText    []*SegmentedText `protobuf:"bytes,5,rep,name=animation_text,json=animationText" json:"animation_text,omitempty"`  
    XXX_unrecognized []byte           `json:"-"`  
}
type SegmentedText struct {  
    ShowType         *int32  `protobuf:"varint,1,opt,name=show_type,json=showType" json:"show_type,omitempty"`  
    Text             *string `protobuf:"bytes,2,opt,name=text" json:"text,omitempty"`  
    XXX_unrecognized []byte  `json:"-"`  
}
```