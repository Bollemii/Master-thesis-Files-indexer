import { useState, useEffect } from "react"
import { Filter } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TopicResponse } from "@/types/api"

type ProcessingStatus = "all" | "processed" | "unprocessed"

type DashboardFiltersProps = {
  topics: TopicResponse[]
  applyFilters: (processed: string, topicId: string) => void
}

export default function DashboardFilters({ topics, applyFilters }: DashboardFiltersProps) {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<ProcessingStatus>("all")
  const [selectedTopic, setSelectedTopic] = useState<string>("all")

  const handleApplyFilters = () => {
    setOpen(false)
    applyFilters(status, selectedTopic === "all" ? "" : selectedTopic)
  }
  const handleResetFilters = () => {
    setStatus("all")
    setSelectedTopic("all")
    applyFilters("all", "")
    setOpen(false)
  }

  useEffect(() => {
    applyFilters(status, selectedTopic === "all" ? "" : selectedTopic)
  }, [status, selectedTopic])

  return (
    <div className="z-50">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button className="rounded-full shadow-lg dark:bg-gray-300 bg-white" size="icon">
            <Filter className="h-5 w-5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-4 bg-white" side="top" align="center">
          <div className="space-y-4">
            <div className="font-medium">Research Filters</div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Processing Status</label>
              <div className="flex rounded-md overflow-hidden border">
                <Button
                  type="button"
                  variant={status === "all" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    status === "all" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setStatus("all")}
                >
                  All
                </Button>
                <Button
                  type="button"
                  variant={status === "processed" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    status === "processed" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setStatus("processed")}
                >
                  Processed
                </Button>
                <Button
                  type="button"
                  variant={status === "unprocessed" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    status === "unprocessed" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setStatus("unprocessed")}
                >
                  Unprocessed
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Topic</label>
              <Select value={selectedTopic} onValueChange={setSelectedTopic}>
                <SelectTrigger className="hover:cursor-pointer">
                  <SelectValue placeholder="Select a topic" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" className="hover:cursor-pointer dark:bg-white bg-white">All Topics</SelectItem>
                  {topics.map((topic) => (
                    <SelectItem key={topic.id} value={topic.id} className="hover:cursor-pointer dark:bg-white bg-white">
                      {topic.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={handleResetFilters} size="sm">
                Reset
              </Button>
              <Button onClick={handleApplyFilters} size="sm" className="dark:bg-blue-600 dark:text-white">
                Apply Filters
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
