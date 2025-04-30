import { ChatbotConversation } from "@/components/ChatbotConversation";
import { TopBar } from "@/components/TopBar"

export function ChatbotPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <TopBar />
      <main className="flex-1 w-full mx-auto py-6 sm:px-6 lg:px-8 mt-16">
        <ChatbotConversation />
      </main>
    </div>
  );
}
