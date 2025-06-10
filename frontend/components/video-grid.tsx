import VideoCard from "./video-card"

const placeholderItems = Array(12)
  .fill(null)
  .map((_, i) => ({
    id: `item-${i}`,
    title:
      i % 3 === 0 ? "这是一个非常非常长的文章标题，用来测试多行显示效果和省略号是否正常工作" : `RSS 文章标题 ${i + 1}`,
    thumbnailUrl: `/placeholder.svg?width=400&height=225&query=abstract+${i}`,
    channelName: `订阅源 ${String.fromCharCode(65 + (i % 5))}`,
    channelAvatarUrl: `/placeholder.svg?width=36&height=36&query=avatar+${String.fromCharCode(65 + (i % 5))}`,
    views: `${Math.floor(Math.random() * 100)}K 次阅读`,
    publishedAt: `${Math.floor(Math.random() * 12) + 1} 个月前`,
    duration: i % 4 === 0 ? "12:34" : undefined,
  }))

export default function VideoGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-8">
      {placeholderItems.map((item) => (
        <VideoCard key={item.id} item={item} />
      ))}
    </div>
  )
}
