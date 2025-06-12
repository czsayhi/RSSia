"use client"

import { useState, useEffect, useRef } from "react"
import Image from "next/image"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Search, Loader2, X } from "lucide-react"

export interface SearchResult {
  id: string
  display_name: string
  description: string
  icon: string // Path to icon
  platform: string
}

interface SourceSearchInputProps {
  onSelect: (source: SearchResult) => void
  onSearch?: (query: string) => Promise<SearchResult[]> // 异步搜索函数
  mockResults?: SearchResult[] // 可选的mock数据，用于向后兼容
}

export default function SourceSearchInput({ onSelect, onSearch, mockResults }: SourceSearchInputProps) {
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
          if (onSearch) {
            // 使用异步搜索函数
            const searchResults = await onSearch(searchTerm)
            setResults(searchResults)
          } else if (mockResults) {
            // 使用mock数据进行本地过滤
            const filtered = mockResults.filter(
              (r) =>
                r.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                r.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                r.platform.toLowerCase().includes(searchTerm.toLowerCase()),
            )
            setResults(filtered)
          } else {
            setResults([])
          }
          setShowResults(true)
        } catch (error) {
          console.error('搜索失败:', error)
          setResults([])
          setShowResults(true)
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
  }, [searchTerm, onSearch, mockResults])

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

  const handleClearSearch = () => {
    setSearchTerm("")
    setShowResults(false)
  }

  return (
    <div className="space-y-2 max-w-2xl mx-auto" ref={searchContainerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => searchTerm && setShowResults(true)}
          className="w-full pl-10 pr-12 text-base focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-input [&::-webkit-search-cancel-button]:appearance-none [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-results-button]:appearance-none [&::-webkit-search-results-decoration]:appearance-none"
          placeholder="搜索订阅源..."
        />
        {searchTerm && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClearSearch}
            className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 bg-transparent hover:bg-muted"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
        {showResults && (
          <Card className="absolute z-10 w-full mt-0 shadow-lg border-t-0 rounded-t-none">
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
      <p className="text-xs text-muted-foreground text-center">
        请输入想订阅的平台，如微博、b站等，或直接粘贴想订阅的up主、想看的即刻圈子的页面url
      </p>
    </div>
  )
}
