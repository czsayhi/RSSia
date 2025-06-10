import Image from "next/image"
import Link from "next/link"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface VideoCardProps {
  item: {
    id: string
    title: string
    thumbnailUrl: string
    channelName: string
    channelAvatarUrl: string
    views: string
    publishedAt: string
    duration?: string
  }
}

export default function VideoCard({ item }: VideoCardProps) {
  return (
    <Link href={`/item/${item.id}`} className="group">
      <div className="flex flex-col gap-2">
        <div className="relative aspect-video rounded-xl overflow-hidden">
          <Image
            src={item.thumbnailUrl || "/placeholder.svg"}
            alt={item.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          {item.duration && (
            <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
              {item.duration}
            </span>
          )}
        </div>
        <div className="flex gap-3 items-start">
          <Avatar className="h-9 w-9 mt-0.5">
            <AvatarImage src={item.channelAvatarUrl || "/placeholder.svg"} alt={item.channelName} />
            <AvatarFallback>{item.channelName.charAt(0)}</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <h3 className="text-base font-medium leading-snug line-clamp-2 group-hover:text-primary transition-colors duration-200">
              {item.title}
            </h3>
            <p className="text-sm text-muted-foreground mt-1 group-hover:text-foreground/80 transition-colors duration-200">
              {item.channelName}
            </p>
            <div className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5 group-hover:text-foreground/70 transition-colors duration-200">
              <span>{item.views}</span>
              <span>•</span>
              <span>{item.publishedAt}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}
