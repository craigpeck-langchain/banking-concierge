import { Client, type ThreadState } from "@langchain/langgraph-sdk";
import type {
  LangChainMessage,
  LangGraphMessagesEvent,
  LangGraphSendMessageConfig,
} from "@assistant-ui/react-langgraph";

export type ChatApiContext = {
  apiUrl: string;
  assistantId: string;
  apiKey?: string | null;
};

const createClient = (ctx: Pick<ChatApiContext, "apiUrl" | "apiKey">) =>
  new Client({
    apiUrl: ctx.apiUrl,
    // The SDK turns `apiKey` into an `x-api-key` header on every request.
    // Pass `null` (not undefined) to suppress the env-var fallback that
    // would otherwise kick in if process.env happened to be polyfilled.
    apiKey: ctx.apiKey ?? null,
  });

export const createThread = (ctx: ChatApiContext) =>
  createClient(ctx).threads.create();

export const getThreadState = (
  ctx: ChatApiContext,
  threadId: string,
): Promise<ThreadState<Record<string, unknown>>> =>
  createClient(ctx).threads.getState(threadId);

const matchesParentMessages = (
  stateMessages: LangChainMessage[] | undefined,
  parentMessages: LangChainMessage[],
) => {
  if (!stateMessages || stateMessages.length !== parentMessages.length) return false;
  const hasStableIds =
    parentMessages.every((m) => typeof m.id === "string") &&
    stateMessages.every((m) => typeof m.id === "string");
  if (!hasStableIds) return false;
  return parentMessages.every((m, i) => m.id === stateMessages[i]?.id);
};

export const getCheckpointId = async (
  ctx: ChatApiContext,
  threadId: string,
  parentMessages: LangChainMessage[],
): Promise<string | null> => {
  const history = await createClient(ctx).threads.getHistory(threadId);
  for (const state of history) {
    const stateMessages = (state.values as { messages?: LangChainMessage[] })
      .messages;
    if (matchesParentMessages(stateMessages, parentMessages)) {
      return state.checkpoint.checkpoint_id ?? null;
    }
  }
  return null;
};

export const sendMessage = (
  ctx: ChatApiContext,
  params: {
    threadId: string;
    messages: LangChainMessage[];
    config?: LangGraphSendMessageConfig & { abortSignal?: AbortSignal };
  },
): AsyncGenerator<LangGraphMessagesEvent<LangChainMessage>> => {
  const { checkpointId, abortSignal, ...restConfig } = params.config ?? {};
  return createClient(ctx).runs.stream(params.threadId, ctx.assistantId, {
    input: params.messages.length > 0 ? { messages: params.messages } : null,
    streamMode: ["messages-tuple", "values"],
    streamSubgraphs: true,
    onDisconnect: "cancel",
    // assistant-ui passes `abortSignal`; langgraph-sdk expects `signal`.
    ...(abortSignal && { signal: abortSignal }),
    ...(checkpointId && { checkpoint_id: checkpointId }),
    ...restConfig,
  }) as AsyncGenerator<LangGraphMessagesEvent<LangChainMessage>>;
};
