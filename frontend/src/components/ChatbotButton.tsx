import { MessageCircle } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function ChatbotButton({chatUrl}: {chatUrl: string}) {
    const navigate = useNavigate()
    const [isHovered, setIsHovered] = useState(false)

    return (
        <div className="relative">
            <button
                onClick={() => navigate(chatUrl)}
                className={`p-4 bg-blue-500 text-white dark:bg-blue-600 dark:hover:bg-blue-500 rounded-full cursor-pointer shadow-lg transition-colors duration-200 flex items-center justify-center group`}
                aria-label="Go to Chatbot"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <MessageCircle className="w-6 h-6" />
            </button>
            {isHovered && (
                <div className="absolute left-full ml-4 top-1/2 bg-blue-500 dark:bg-blue-600 text-white p-3 rounded-lg shadow-xl animate-fadeIn">
                    <div className="relative">
                        <div className="absolute left-0 top-1/2 -translate-x-5 -translate-y-1/2 w-0 h-0 border-t-8 border-t-transparent border-r-8 border-r-blue-500 dark:border-r-blue-600 border-b-8 border-b-transparent"></div>
                        <p className="whitespace-nowrap font-medium">Talk to me! 😊</p>
                    </div>
                </div>
            )}
        </div>
    )
}
