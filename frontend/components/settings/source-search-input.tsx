"use client"

import { useState, useEffect, useRef, useCallback } from "react"
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
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastSearchTermRef = useRef<string>("") // 记录上次搜索的内容

  // 更新搜索函数的引用
  const onSearchRef = useRef(onSearch)
  const mockResultsRef = useRef(mockResults)

  useEffect(() => {
    onSearchRef.current = onSearch
    mockResultsRef.current = mockResults
  }, [onSearch, mockResults])

  // 优化的搜索函数
  const performSearch = useCallback(async (query: string) => {
    // 如果查询为空，不进行搜索
    if (!query.trim()) {
      setResults([])
      setShowResults(false)
      return
    }

    // 如果搜索内容与上次相同，不重复搜索
    if (query.trim() === lastSearchTermRef.current) {
      return
    }

    lastSearchTermRef.current = query.trim()
        setIsLoading(true)
    
    try {
      if (onSearchRef.current) {
        // 使用异步搜索函数
        const searchResults = await onSearchRef.current(query.trim())
        setResults(searchResults)
      } else if (mockResultsRef.current) {
        // 使用mock数据进行本地过滤
        const filtered = mockResultsRef.current.filter(
            (r) =>
            r.display_name.toLowerCase().includes(query.toLowerCase()) ||
            r.description.toLowerCase().includes(query.toLowerCase()) ||
            r.platform.toLowerCase().includes(query.toLowerCase()),
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
  }, [])

  // 防抖效果
  useEffect(() => {
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // 如果搜索词为空，立即清空结果
    if (!searchTerm.trim()) {
      setResults([])
      setShowResults(false)
      setIsLoading(false)
      lastSearchTermRef.current = ""
      return
    }

    // 如果搜索内容与上次相同，不重复搜索
    if (searchTerm.trim() === lastSearchTermRef.current) {
      return
    }

    // 设置防抖定时器
    debounceTimerRef.current = setTimeout(() => {
      performSearch(searchTerm)
    }, 300)

    // 清理函数
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [searchTerm, performSearch])

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
    lastSearchTermRef.current = "" // 重置搜索记录
  }

  const handleClearSearch = () => {
    setSearchTerm("")
    setResults([])
    setShowResults(false)
    setIsLoading(false)
    lastSearchTermRef.current = "" // 重置搜索记录
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchTerm(value)
    
    // 如果输入为空，立即清空结果
    if (!value.trim()) {
      setResults([])
      setShowResults(false)
      setIsLoading(false)
      lastSearchTermRef.current = ""
    }
  }

  return (
    <div className="space-y-2 max-w-2xl mx-auto" ref={searchContainerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={() => searchTerm && results.length > 0 && setShowResults(true)}
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
