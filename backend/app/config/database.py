def init_subscription_templates():
    """初始化订阅模板数据"""
    templates = [
        {
            'platform': 'bilibili',
            'content_type': 'video',
            'subscription_mode': 'precise',
            'name': 'B站UP主视频',
            'description': '订阅B站UP主的最新视频投稿',
            'url_template': 'https://rsshub.app/bilibili/user/video/{user_id}',
            'example_user_id': '2267573'
        },
        {
            'platform': 'bilibili',
            'content_type': 'dynamic',
            'subscription_mode': 'precise',
            'name': 'B站UP主动态',
            'description': '订阅B站UP主的最新动态',
            'url_template': 'https://rsshub.app/bilibili/user/dynamic/{user_id}',
            'example_user_id': '297572288'
        },
        {
            'platform': 'weibo',
            'content_type': 'post',
            'subscription_mode': 'precise',
            'name': '微博用户动态',
            'description': '订阅微博用户的最新动态',
            'url_template': 'https://rsshub.app/weibo/user/{user_id}',
            'example_user_id': '1195230310'
        },
        {
            'platform': 'weibo',
            'content_type': 'post',
            'subscription_mode': 'theme_aggregation',
            'name': '微博关键词搜索',
            'description': '订阅包含特定关键词的微博内容',
            'url_template': 'https://rsshub.app/weibo/search/{user_id}',
            'example_user_id': 'ai科技'
        }
    ]
    
    # ... existing code ... 