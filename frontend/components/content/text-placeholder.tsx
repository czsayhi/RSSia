"use client"

import { useEffect, useState } from "react"

interface TextPlaceholderProps {
  content: string
  className?: string
}

// 简单的HTML清理函数（生产环境建议使用DOMPurify）
const sanitizeHTML = (html: string): string => {
  // 基础的HTML标签白名单
  const allowedTags = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "a",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "div",
    "span",
  ]
  const allowedAttributes = ["href", "target", "rel"]

  // 这里是简化版本，实际项目中应该使用DOMPurify
  return html
}

export default function TextPlaceholder({ content, className = "" }: TextPlaceholderProps) {
  const [sanitizedContent, setSanitizedContent] = useState("")

  useEffect(() => {
    const cleaned = sanitizeHTML(content)
    setSanitizedContent(cleaned)
  }, [content])

  if (!content) {
    return (
      <div className={`text-center text-muted-foreground py-8 ${className}`}>
        <p>暂无内容描述</p>
      </div>
    )
  }

  return (
    <div className={`prose prose-sm max-w-none dark:prose-invert ${className}`}>
      <div className="text-sm text-foreground leading-relaxed" dangerouslySetInnerHTML={{ __html: sanitizedContent }} />
    </div>
  )
}
