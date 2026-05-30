import { useRef, type ReactNode } from "react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import {
  useLangGraphRuntime,
  type LangChainMessage,
} from "@assistant-ui/react-langgraph";
import {
  createThread,
  getCheckpointId,
  getThreadState,
  sendMessage,
  type ChatApiContext,
} from "./lib/chatApi";

type Props = {
  assistantId?: string;
  apiKey: string | null;
  children: ReactNode;
};

export function RuntimeProvider({
  assistantId = "agent",
  apiKey,
  children,
}: Props) {
  const ctxRef = useRef<ChatApiContext>({
    apiUrl: window.location.origin,
    assistantId,
    apiKey,
  });
  ctxRef.current = {
    apiUrl: window.location.origin,
    assistantId,
    apiKey,
  };

  const runtime = useLangGraphRuntime({
    unstable_allowCancellation: true,
    stream: async function* (messages, { initialize, ...config }) {
      const { externalId } = await initialize();
      if (!externalId) throw new Error("Thread not found");
      yield* sendMessage(ctxRef.current, {
        threadId: externalId,
        messages,
        config,
      });
    },
    create: async () => {
      const { thread_id } = await createThread(ctxRef.current);
      return { externalId: thread_id };
    },
    load: async (externalId) => {
      const state = await getThreadState(ctxRef.current, externalId);
      const stateValues = state.values as { messages?: LangChainMessage[] };
      return {
        messages: stateValues.messages ?? [],
        interrupts: state.tasks[0]?.interrupts ?? [],
      };
    },
    getCheckpointId: (threadId, parentMessages) =>
      getCheckpointId(ctxRef.current, threadId, parentMessages),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
