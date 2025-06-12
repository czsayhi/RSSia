"use client"

import { Button } from "@/components/ui/button"
import { ListChecks, Timer } from "lucide-react"
import { cn } from "@/lib/utils"

interface SettingsSidebarProps {
  activeTab: "sources" | "frequency"
  setActiveTab: (tab: "sources" | "frequency") => void
}

export default function SettingsSidebar({ activeTab, setActiveTab }: SettingsSidebarProps) {
  const navItems = [
    { id: "sources", label: "订阅源", icon: ListChecks },
    { id: "frequency", label: "订阅频率", icon: Timer },
  ]

  return (
    <aside className="w-full md:w-64 flex-shrink-0">
      <nav className="flex flex-col space-y-1">
        {navItems.map((item) => (
          <Button
            key={item.id}
            variant="ghost"
            className={cn(
              "w-full justify-start px-3 py-2 text-left",
              activeTab === item.id && "bg-muted font-semibold text-primary hover:bg-muted",
            )}
            onClick={() => setActiveTab(item.id as "sources" | "frequency")}
          >
            {item.icon && <item.icon className="mr-2 h-5 w-5" />}
            {item.label}
          </Button>
        ))}
      </nav>
    </aside>
  )
}
