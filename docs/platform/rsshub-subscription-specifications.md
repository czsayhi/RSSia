# RSSHub订阅源规范文档

## 📝 文档说明
本规范基于RSSHub官方文档整理，定义了RSS智能订阅器支持的各个平台订阅源的标准配置。

---

## 🐦 微博 (Weibo)

### ⚠️ 重要提醒
微博会针对请求的来源地区返回不同的结果。部分视频因未知原因仅限中国大陆境内访问。

### 📋 通用参数配置
对于微博内容，在 routeParams 参数中以 query string 格式指定选项，可以控制输出的样式：

| 键 | 含义 | 接受的值 | 默认值 |
|---|---|---|---|
| readable | 是否开启细节排版可读性优化 | 0/1/true/false | false |
| authorNameBold | 是否加粗作者名字 | 0/1/true/false | false |
| showAuthorInTitle | 是否在标题处显示作者 | 0/1/true/false | false（/weibo/keyword/中为 true） |
| showAuthorInDesc | 是否在正文处显示作者 | 0/1/true/false | false（/weibo/keyword/中为 true） |
| showAuthorAvatarInDesc | 是否在正文处显示作者头像 | 0/1/true/false | false |
| showEmojiForRetweet | 显示 "🔁" 取代 "转发" 两个字 | 0/1/true/false | false |
| showRetweetTextInTitle | 在标题出显示转发评论 | 0/1/true/false | true |
| addLinkForPics | 为图片添加可点击的链接 | 0/1/true/false | false |
| showTimestampInDescription | 在正文处显示被转发微博的时间戳 | 0/1/true/false | false |
| widthOfPics | 微博配图宽（生效取决于阅读器） | 不指定/数字 | 不指定 |
| heightOfPics | 微博配图高（生效取决于阅读器） | 不指定/数字 | 不指定 |
| sizeOfAuthorAvatar | 作者头像大小 | 数字 | 48 |
| displayVideo | 是否直接显示微博视频和 Live Photo | 0/1/true/false | true |
| displayArticle | 是否直接显示微博文章 | 0/1/true/false | false |
| displayComments | 是否直接显示热门评论 | 0/1/true/false | false |
| showEmojiInDescription | 是否展示正文中的微博表情 | 0/1/true/false | true |
| showLinkIconInDescription | 是否展示正文中的链接图标 | 0/1/true/false | true |
| preferMobileLink | 是否使用移动版链接 | 0/1/true/false | false |
| showRetweeted | 是否显示转发的微博 | 0/1/true/false | true |
| showBloggerIcons | 是否显示评论中博主的标志 | 0/1/true/false | false |

### 1. 博主订阅
- **热度**: 🔥 42051
- **状态**: 🟢 Passed Test 🚨 Strict Anti-crawling ⚙️ Config Required 🔍 Support Radar
- **路由**: `/weibo/user/:uid/:routeParams?`
- **示例**: `https://rsshub.app/weibo/user/1195230310`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| uid | 是 | 用户 id，博主主页打开控制台执行 `$CONFIG.oid` 获取 |
| routeParams | 否 | 额外参数，特别地，当 routeParams=1 时开启微博视频显示 |

#### 部署配置
- `WEIBO_COOKIES` (可选)

#### ⚠️ 注意事项
部分博主仅登录可见，未提供 Cookie 的情况下不支持订阅，可以通过打开 `https://m.weibo.cn/u/:uid` 验证

### 2. 关键词搜索
- **热度**: 🔥 1218
- **状态**: 🟢 Passed Test
- **路由**: `/weibo/keyword/:keyword/:routeParams?`
- **示例**: `https://rsshub.app/weibo/keyword/RSSHub`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| keyword | 是 | 你想订阅的微博关键词 |
| routeParams | 否 | 额外参数，请参阅通用参数配置表格 |

---

## 🟡 即刻 (Jike)

### 1. 圈子订阅
- **热度**: 🔥 19311
- **状态**: 🟢 Passed Test 🔍 Support Radar
- **路由**: `/jike/topic/:id/:showUid?`
- **示例**: `https://rsshub.app/jike/topic/556688fae4b00c57d9dd46ee`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| id | 是 | 圈子 id，可在即刻 web 端圈子页或 APP 分享出来的圈子页 URL 中找到 |
| showUid | 否 | 是否在内容中显示用户信息，设置为 1 则开启 |

### 2. 用户动态
- **热度**: 🔥 7795
- **状态**: 🟢 Passed Test 🔍 Support Radar
- **路由**: `/jike/user/:id`
- **示例**: `https://rsshub.app/jike/user/3EE02BC9-C5B3-4209-8750-4ED1EE0F67BB`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| id | 是 | 用户 id，可在即刻分享出来的单条动态页点击用户头像进入个人主页，然后在个人主页的 URL 中找到，或者在单条动态页使用 RSSHub Radar 插件 |

---

## 📺 哔哩哔哩 (Bilibili)

### 1. UP 主投稿
- **热度**: 🔥 177522
- **状态**: 🟢 Passed Test 🔍 Support Radar
- **路由**: `/bilibili/user/video/:uid/:embed?`
- **示例**: `https://rsshub.app/bilibili/user/video/2267573`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| uid | 是 | 用户 id，可在 UP 主主页中找到 |
| embed | 否 | 默认为开启内嵌视频，任意值为关闭 |

### 2. UP 主动态
- **热度**: 🔥 19161
- **状态**: 🟢 Passed Test ⚙️ Config Required 🔍 Support Radar
- **路由**: `/bilibili/user/dynamic/:uid/:routeParams?`
- **示例**: `https://rsshub.app/bilibili/user/dynamic/2267573`

#### 参数说明
| 参数 | 必需 | 说明 |
|---|---|---|
| uid | 是 | 用户 id，可在 UP 主主页中找到 |
| routeParams | 否 | 见下方路由参数配置 |

#### 路由参数配置
| 键 | 含义 | 接受的值 | 默认值 |
|---|---|---|---|
| showEmoji | 显示或隐藏表情图片 | 0/1/true/false | false |
| embed | 默认开启内嵌视频 | 0/1/true/false | true |
| useAvid | 视频链接使用 AV 号 (默认为 BV 号) | 0/1/true/false | false |
| directLink | 使用内容直链 | 0/1/true/false | false |
| hideGoods | 隐藏带货动态 | 0/1/true/false | false |
| offset | 偏移状态 | string | "" |

#### 用例
`/bilibili/user/dynamic/2267573/showEmoji=1&embed=0&useAvid=1`

#### 部署配置
- `BILIBILI_COOKIE_*` (可选) - 如果没有此配置，那么必须开启 puppeteer 支持

---

## 📊 平台支持总览

| 平台 | 中文名 | 支持的订阅类型 | 总路由数 |
|---|---|---|---|
| weibo | 微博 | 用户订阅、关键词搜索 | 2 |
| jike | 即刻 | 用户动态、圈子订阅 | 2 |
| bilibili | 哔哩哔哩 | UP主投稿、UP主动态 | 2 |

---

## 🔄 更新记录
- 2025-06-10: 基于RSSHub官方文档创建初始规范
- 整理了微博、即刻、哔哩哔哩三个平台的订阅源规范 