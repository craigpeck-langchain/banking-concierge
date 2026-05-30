import { type FC } from "react";
import {
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAuiState,
  useMessagePartText,
  type EmptyMessagePartComponent,
  type ToolCallMessagePartComponent,
} from "@assistant-ui/react";
import { StreamdownTextPrimitive } from "@assistant-ui/react-streamdown";

const SUGGESTIONS = [
  "What's the monthly fee on Everyday Checking?",
  "Look up customer CUST-0001.",
  "Find the nearest branch to 94103.",
];

export const ThreadView: FC = () => (
  <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col">
    <ThreadPrimitive.Viewport className="relative flex min-h-0 flex-1 flex-col overflow-y-auto px-3 py-4 sm:px-6 sm:py-6">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        <ThreadEmpty />
        <div className="flex flex-col gap-3">
          <ThreadPrimitive.Messages>{() => <ThreadMessage />}</ThreadPrimitive.Messages>
        </div>
      </div>
    </ThreadPrimitive.Viewport>
  </ThreadPrimitive.Root>
);

const ThreadEmpty: FC = () => (
  <ThreadPrimitive.Empty>
    <div className="flex flex-1 flex-col items-center justify-center py-20 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary)] text-[var(--primary-foreground)]">
        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="currentColor">
          <path d="M12 2L2 12l10 10 10-10z" />
        </svg>
      </div>
      <h2 className="text-2xl font-semibold">Customer Service Concierge</h2>
      <p className="mt-2 max-w-md text-sm text-[var(--muted-foreground)]">
        Ask about Meridian National personal banking, look up customer accounts, find a
        branch, or initiate a transfer.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <ThreadPrimitive.Suggestion key={s} prompt={s} asChild>
            <button className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-xs font-medium text-[var(--muted-foreground)] transition-colors hover:bg-[var(--accent-bg)] hover:text-[var(--foreground)]">
              {s}
            </button>
          </ThreadPrimitive.Suggestion>
        ))}
      </div>
    </div>
  </ThreadPrimitive.Empty>
);

const ThreadMessage: FC = () => {
  const role = useAuiState((s) => s.message.role);
  if (role === "user") return <UserMessage />;
  return <AssistantMessage />;
};

const UserMessage: FC = () => (
  <MessagePrimitive.Root data-role="user" className="anim-msg flex justify-end">
    <div className="max-w-[90%] rounded-2xl rounded-br-sm bg-[var(--primary)] px-4 py-2.5 text-sm leading-relaxed text-[var(--primary-foreground)]">
      <MessagePrimitive.Parts />
    </div>
  </MessagePrimitive.Root>
);

const AssistantTextPart: FC = () => {
  const part = useMessagePartText();
  if (!part.text) return null;
  return (
    <div className="max-w-[90%] rounded-2xl rounded-bl-sm border border-[var(--border-subtle)] bg-[var(--surface)] px-4 py-2.5 text-sm leading-relaxed text-[var(--foreground)] shadow-sm">
      <StreamdownTextPrimitive />
    </div>
  );
};

const PulsingDots: EmptyMessagePartComponent = () => (
  <div className="rounded-2xl rounded-bl-sm border border-[var(--border-subtle)] bg-[var(--surface)] px-4 py-2.5 text-sm shadow-sm">
    <span className="inline-flex items-center gap-1 text-[var(--muted-foreground)]">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:120ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:240ms]" />
    </span>
  </div>
);

const TOOL_RENDERERS: Record<string, ToolCallMessagePartComponent> = {};

const ToolFallback: ToolCallMessagePartComponent = ({ toolName, argsText, result }) => (
  <details className="w-full max-w-[90%] rounded-xl border border-[var(--border-subtle)] bg-[var(--surface)] px-3 py-2 text-xs">
    <summary className="cursor-pointer">
      <span className="rounded bg-[var(--accent-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--foreground)]">
        tool
      </span>
      <span className="ml-2 font-medium">{toolName}</span>
    </summary>
    {argsText && (
      <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded bg-[var(--muted)] p-2 text-[11px] text-[var(--muted-foreground)]">
        {argsText}
      </pre>
    )}
    {result !== undefined && (
      <pre className="mt-2 max-h-60 overflow-auto whitespace-pre-wrap break-words rounded bg-[var(--muted)] p-2 text-[11px] text-[var(--muted-foreground)]">
        {typeof result === "string" ? result : JSON.stringify(result, null, 2)}
      </pre>
    )}
  </details>
);

const AssistantMessage: FC = () => (
  <MessagePrimitive.Root
    data-role="assistant"
    className="anim-msg flex flex-col items-start gap-2"
  >
    <MessagePrimitive.Parts
      unstable_showEmptyOnNonTextEnd={false}
      components={{
        Empty: PulsingDots,
        Text: AssistantTextPart,
        tools: { by_name: TOOL_RENDERERS, Fallback: ToolFallback },
      }}
    />
    <ErrorPrimitive.Root className="rounded-md border border-red-300 bg-red-50 px-2 py-1 text-xs text-red-700">
      <ErrorPrimitive.Message />
    </ErrorPrimitive.Root>
  </MessagePrimitive.Root>
);

export const Composer: FC = () => (
  <div className="border-t border-[var(--border)] bg-[var(--background)] px-3 py-3 sm:px-6 sm:py-4">
    <div className="mx-auto w-full max-w-3xl">
      <ComposerPrimitive.Root className="composer flex items-end gap-2 px-3 py-2.5">
        <ComposerPrimitive.Input
          autoFocus
          rows={1}
          placeholder="Message the concierge…"
          className="flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-[var(--muted-foreground)]"
        />
        <ThreadPrimitive.If running={false}>
          <ComposerPrimitive.Send className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-xs font-medium text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50">
            Send
          </ComposerPrimitive.Send>
        </ThreadPrimitive.If>
        <ThreadPrimitive.If running>
          <ComposerPrimitive.Cancel className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs font-medium text-[var(--muted-foreground)] hover:bg-[var(--accent-bg)]">
            Stop
          </ComposerPrimitive.Cancel>
        </ThreadPrimitive.If>
      </ComposerPrimitive.Root>
    </div>
  </div>
);
