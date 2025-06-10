"use client"

import { useState, useEffect, useRef } from "react"
import Image from "next/image"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Loader2 } from "lucide-react"
import { searchSubscriptionSources } from "@/lib/api-client"
import type { SearchResult } from "@/lib/api-client"

interface SourceSearchInputProps {
  onSelect: (source: SearchResult) => void
}

export default function SourceSearchInput({ onSelect }: SourceSearchInputProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [showResults, setShowResults] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const searchContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = setTimeout(async () => {
      if (searchTerm) {
        setIsLoading(true)
        try {
          // 调用后端API获取真实搜索结果 (数据协议适配)
          const response = await searchSubscriptionSources({ 
            query: searchTerm,
            limit: 10 
          })
          setResults(response.results)
          setShowResults(true)
        } catch (error) {
          console.error('搜索订阅源失败:', error)
          setResults([])
        } finally {
          setIsLoading(false)
        }
      } else {
        setResults([])
        setShowResults(false)
      }
    }, 300) // Debounce input

    return () => {
      clearTimeout(handler)
    }
  }, [searchTerm])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowResults(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [searchContainerRef])

  const handleSelectResult = (result: SearchResult) => {
    onSelect(result)
    setSearchTerm("") // Clear search term after selection
    setShowResults(false)
  }

  return (
    <div className="space-y-2 max-w-2xl mx-auto" ref={searchContainerRef}>
      {" "}
      {/* Increased width from max-w-md to max-w-2xl */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => searchTerm && setShowResults(true)}
          className="w-full pl-10 text-base"
          // Removed placeholder attribute
        />
      </div>
      <p className="text-xs text-muted-foreground text-center">
        请输入想订阅的平台，如微博、b站等，或直接粘贴想订阅的up主、想看的即刻圈子的页面url
      </p>
      {showResults && (
        <Card className="absolute z-10 w-full max-w-2xl mt-1 shadow-lg">
          {" "}
          {/* Matched width */}
          <CardContent className="p-2 max-h-72 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : results.length > 0 ? (
              results.map((result) => (
                <div
                  key={result.id}
                  onClick={() => handleSelectResult(result)}
                  className="flex items-center gap-3 p-3 hover:bg-muted rounded-md cursor-pointer"
                >
                  <Image
                    src={result.icon || "/placeholder.svg"}
                    alt={result.platform}
                    width={24}
                    height={24}
                    className="h-6 w-6"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-sm">{result.display_name}</p>
                    <p className="text-xs text-muted-foreground">{result.description}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="p-3 text-sm text-center text-muted-foreground">暂无匹配结果</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
