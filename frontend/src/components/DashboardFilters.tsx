import { useState, useContext } from "react"
import { Filter } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TopicResponse } from "@/types/api"
import { DashboardFiltersContext } from "@/contexts/DashboardFiltersContext"

type DashboardFiltersProps = {
  topics: TopicResponse[]
}

export default function DashboardFilters({ topics }: DashboardFiltersProps) {
  const { filters, setFilters, setProcessingStatus, setTopicId } = useContext(DashboardFiltersContext)
  const [open, setOpen] = useState(false)

  const handleResetFilters = () => {
    setFilters({ processed: "all", topicId: "" })
    setOpen(false)
  }

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
                  variant={filters.processed === "all" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    filters.processed === "all" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setProcessingStatus("all")}
                >
                  All
                </Button>
                <Button
                  type="button"
                  variant={filters.processed === "processed" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    filters.processed === "processed" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setProcessingStatus("processed")}
                >
                  Processed
                </Button>
                <Button
                  type="button"
                  variant={filters.processed === "unprocessed" ? "default" : "outline"}
                  className={`flex-1 rounded-none ${
                    filters.processed === "unprocessed" ? "bg-white dark:bg-gray-800 text-black dark:text-white hover:cursor-default" : "dark:bg-white bg-gray-800 dark:text-black text-white"
                  }`}
                  onClick={() => setProcessingStatus("unprocessed")}
                >
                  Unprocessed
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Topic</label>
              <Select value={filters.topicId !== "" ? filters.topicId : "all"} onValueChange={setTopicId}>
                <SelectTrigger className="hover:cursor-pointer">
                  <SelectValue placeholder="Select a topic" />
                </SelectTrigger>
                <SelectContent className="dark:bg-white bg-white">
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
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
