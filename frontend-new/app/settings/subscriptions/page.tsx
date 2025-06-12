"use client"

import { useState } from "react"
import SubscriptionSources from "@/components/settings/subscription-sources"
import SubscriptionFrequency from "@/components/settings/subscription-frequency"
import SettingsSidebar from "@/components/settings/settings-sidebar"

export default function SettingsSubscriptionsPage() {
  const [activeTab, setActiveTab] = useState<"sources" | "frequency">("sources")

  return (
    <div className="flex flex-col md:flex-row gap-8">
      <SettingsSidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="flex-1">
        {activeTab === "sources" && <SubscriptionSources />}
        {activeTab === "frequency" && <SubscriptionFrequency />}
      </div>
    </div>
  )
}
