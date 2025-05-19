import { AppContext } from "@/contexts/AppContext";
import { useAuth } from "@/hooks/useAuth";
import { AuthError, fetchWithAuth } from "@/services/api";
import { ChevronDown, ChevronUp, FileText, Send, Trash2 } from "lucide-react";
import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PulseLoader } from "react-spinners";

enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
}

type Message = {
  id: string;
  position: number;
  role: MessageRole;
  content: string;
  sources?: string[];
};

const welcomeMessage: Message = {
  id: crypto.randomUUID(),
  position: 0,
  role: MessageRole.ASSISTANT,
  content: "Hi! I'm your AI assistant. How can I help you today?",
};

export function ChatbotConversation() {
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const { setPollTaskId, chatbotStatus } = useContext(AppContext);
  const [history, setHistory] = useState<Message[]>([welcomeMessage]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleAuthError = useCallback(
    (error: Error) => {
      if (error instanceof AuthError) {
        logout();
        navigate("/login");
      }
    },
    [logout, navigate]
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  useEffect(() => {
    if (chatbotStatus === "done") {
      setHistory(JSON.parse(localStorage.getItem("chatbotHistory") || "[]"));
      setPollTaskId(null);
    }
  }, [chatbotStatus]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const inputElement = document.getElementById(
          "message-input"
        ) as HTMLInputElement | null;
        if (inputElement) {
          e.preventDefault();
          inputElement.value += e.key;
          setInput(inputElement.value);
          inputElement.focus();
        }
      }
    };

    const storedHistory = localStorage.getItem("chatbotHistory");
    if (storedHistory) {
      const parsedHistory: Message[] = JSON.parse(storedHistory);
      setHistory(parsedHistory);
    } else {
      setHistory([welcomeMessage]);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const addMessage = (message: Message) => {
    const storedHistory = (JSON.parse(
      localStorage.getItem("chatbotHistory") || "[]"
    ) as Message[]).sort((a, b) => a.position - b.position);
    // Fix the position of the new message
    message.position = storedHistory.length;
    const newHistory = [...storedHistory, message];
    localStorage.setItem("chatbotHistory", JSON.stringify(newHistory));
    setHistory(newHistory);
  }
  const clearConversation = () => {
    setHistory([welcomeMessage]);
    localStorage.setItem("chatbotHistory", JSON.stringify([welcomeMessage]));
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (chatbotStatus === "pending" || !input.trim()) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      position: history.length,
      role: MessageRole.USER,
      content: input.trim(),
    };
    const question = input.trim();
    setInput("");
    const oldHistory = [...history];
    addMessage(userMessage);

    try {
      const response = await fetchWithAuth(`/chatbot/ask`, token, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          conversation_history: oldHistory
            .slice(-5) // Keep the last 5 messages for context
            .map((message) => [message.role, message.content]),
        }),
      });

      const taskId = response.task_id;

      // Déclenche le polling
      setPollTaskId(taskId);
    } catch (error) {
      console.error("Error fetching response:", error);
      handleAuthError(error as Error);
    }
  };

  return (
    <div>
      {/* Chat history display area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-20">
        {history.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Begin the conversation by typing a message!</p>
          </div>
        ) : (
          history
            .sort((a, b) => a.position - b.position)
            .map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
        )}
        {chatbotStatus === "pending" && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-3 bg-gray-200 text-gray-800 animate-pulse">
              <PulseLoader size={6} />
            </div>
          </div>
        )}
        {chatbotStatus === "error" && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-3 bg-red-200 text-red-800">
              <p className="whitespace-pre-wrap">
                An error occurred while the assistant was processing your request. Please try again.
              </p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {/* Input field and send button */}
      <div className="fixed bottom-4 left-4 right-4 flex flex-row shadow-md">
        <button
          className="p-2 mr-2 text-gray-500 hover:text-gray-700 transition-colors duration-200 cursor-pointer"
          onClick={clearConversation}
          disabled={chatbotStatus === "pending"}
          aria-label="Clear chat history"
          title="Clear chat history"
        >
          <Trash2 size={24} />
        </button>
        <div
          className="p-4 w-full bg-white cursor-text"
          onClick={(e) => {
            const target = e.target as HTMLInputElement;
            if (target.tagName !== "INPUT") {
              const inputElement = document.getElementById(
                "message-input"
              ) as HTMLInputElement | null;
              inputElement?.focus();
            }
          }}
        >
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <input
              id="message-input"
              value={input}
              autoFocus
              autoComplete="off"
              onChange={handleInputChange}
              placeholder="Tapez votre message..."
              className="flex-1 focus-visible:border-none focus-visible:outline-none"
            />
            <button
              type="submit"
              disabled={chatbotStatus === "pending" || !input.trim()}
              className="cursor-pointer"
            >
              <Send size={24} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const [expanded, setExpanded] = useState(false);
  const toggleExpanded = () => setExpanded((prev) => !prev);

  return (
    <div
      className={`flex ${
        message.role === MessageRole.USER ? "justify-end" : "justify-start"
      } ${message.sources && message.sources.length > 0 ? "cursor-pointer" : ""}`}
      onClick={
        message.sources && message.sources.length > 0
          ? toggleExpanded
          : undefined
      }
    >
      <div
        className={`max-w-[80%] rounded-lg p-3 ${
          message.role === MessageRole.USER
            ? "bg-blue-500 text-white rounded-tr-none"
            : "bg-gray-200 text-gray-800 rounded-tl-none"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <div className="text-blue-500 underline flex flex-row items-center ml-auto">
              {expanded ? (
                <>
                  <ChevronUp size={14} className="mr-2" />
                  <p className="text-xs">Hide sources</p>
                </>
              ) : (
                <>
                  <ChevronDown size={14} className="mr-2" />
                  <p className="text-xs">Show sources</p>
                </>
              )}
            </div>
            {expanded && (
              <div className="mt-2 pt-2 border-t border-gray-300 space-y-1 animate-slideDown">
                <p className="text-xs font-medium text-gray-500 mb-1">
                  Sources:
                </p>
                {message.sources?.map((source, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-1 text-xs text-gray-600"
                  >
                    <FileText size={12} />
                    <span>{source}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
