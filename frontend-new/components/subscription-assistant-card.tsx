"use client"

import type React from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { X, Send, User, ChevronDown, ChevronUp } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import Image from "next/image"

interface Message {
  id: string
  content: React.ReactNode
  sender: "ai" | "user"
  timestamp: string
  isCollapsible?: boolean
}

function SummaryMessage({ content }: { content: React.ReactNode }) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div>
      <div
        className={cn(
          "overflow-hidden transition-all duration-300 text-sm",
          isExpanded ? "max-h-none" : "max-h-[100px]",
        )}
      >
        <div className={cn(!isExpanded && "line-clamp-5")}>{content}</div>
      </div>
      <Button
        variant="link"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-0 h-auto text-xs mt-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
      >
        {isExpanded ? "收起摘要" : "展开摘要"}
        {isExpanded ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />}
      </Button>
    </div>
  )
}

// 注意：这里的初始消息是mock数据，实际应该由后端提供
const initialMessages: Message[] = [
  {
    id: "1",
    content: (
      <>
        <p className="font-semibold text-base mb-2">🚀 这是今天的订阅摘要：</p>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>TechCrunch: AI领域又有新突破，某公司发布了通用人工智能模型，引发业界广泛关注。</li>
          <li>The Verge: 最新款智能手机测评出炉，相机性能大幅提升，但续航能力有所下降。</li>
          <li>Bloomberg: 全球股市波动，分析师建议谨慎投资，特别是在新兴科技板块。</li>
          <li>Wired: 隐私保护成为年度热议话题，新的数据法规即将生效。</li>
          <li>Gizmodo: 可折叠设备市场持续增长，多家厂商预告新品。</li>
        </ul>
      </>
    ),
    sender: "ai",
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    isCollapsible: true,
  },
]

export default function SubscriptionAssistantCard({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [inputValue, setInputValue] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && messages.length > initialMessages.length) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isOpen])

  const handleSendMessage = () => {
    if (inputValue.trim() === "") return
    const newUserMessage: Message = {
      id: String(Date.now()),
      content: inputValue,
      sender: "user",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }
    setMessages((prev) => [...prev, newUserMessage])
    setInputValue("")

    // 模拟AI回复
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          content: `关于"${newUserMessage.content}"，这是我的模拟回复。我正在处理您的请求...`,
          sender: "ai",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ])
    }, 1000)
  }

  if (!isOpen) return null

  return (
    <div
      className={cn(
        "fixed top-4 right-4 bottom-4 z-50",
        "w-[calc(100%-2rem)] max-w-sm md:max-w-md",
        "flex flex-col bg-card text-card-foreground shadow-2xl rounded-lg border dark:border-neutral-800 overflow-hidden",
      )}
    >
      <div className="flex items-center justify-between p-4 border-b dark:border-neutral-800 flex-shrink-0">
        <h2 className="text-lg font-semibold">个人订阅助手</h2>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex-1 p-4 space-y-6 overflow-y-auto">
        {messages.map((msg) => (
          <div key={msg.id} className="flex items-start gap-3">
            <Avatar className="h-8 w-8 flex-shrink-0">
              {msg.sender === "ai" ? (
                <Image src="/images/avatar-ai.png" alt="AI Avatar" width={32} height={32} className="rounded-full" />
              ) : (
                <>
                  <AvatarImage src="/placeholder.svg?width=32&height=32" />
                  <AvatarFallback>
                    <User size={16} />
                  </AvatarFallback>
                </>
              )}
            </Avatar>
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1">{msg.timestamp}</p>
              <div className="text-sm text-foreground break-words">
                {msg.isCollapsible ? (
                  <SummaryMessage content={msg.content} />
                ) : (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 dark:border-neutral-800 flex-shrink-0 border-t-0">
        <div className="relative">
          <Textarea
            placeholder="输入你的问题..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            className={cn(
              "w-full min-h-[80px] resize-none rounded-md p-3 pr-14",
              "bg-background dark:bg-neutral-900 border border-input",
              "focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
              "focus:border-input dark:focus:border-input",
            )}
            rows={3}
          />
          <Button
            onClick={handleSendMessage}
            aria-label="发送消息"
            size="icon"
            className="absolute bottom-[18px] right-[18px] h-8 w-8 bg-foreground text-background hover:bg-foreground/90 rounded-md"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
