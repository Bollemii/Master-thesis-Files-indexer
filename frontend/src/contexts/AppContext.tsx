import { createContext } from "react";

export type Status = "idle" | "pending" | "done" | "error";

export type AppContextType = {
  setPollTaskId: (taskId: string | null) => void;
  chatbotStatus: Status;
  setChatbotStatus: (status: Status) => void;
};

export const AppContext = createContext<AppContextType>({
  setPollTaskId: () => {},
  chatbotStatus: "idle",
  setChatbotStatus: () => {},
});

export function AppContextProvider({
  setPollTaskId,
  chatbotStatus,
  setChatbotStatus,
  children,
}: {
  setPollTaskId: (taskId: string | null) => void;
  chatbotStatus: Status;
  setChatbotStatus: (status: Status) => void;
  children: React.ReactNode;
}) {
  return (
    <AppContext.Provider
      value={{ setPollTaskId, chatbotStatus, setChatbotStatus }}
    >
      {children}
    </AppContext.Provider>
  );
}
