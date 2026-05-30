import { useState, type FC, type FormEvent } from "react";

type Props = {
  onSubmit: (apiKey: string) => void;
};

/**
 * Shown when no LangSmith API key is set and the agent server is gated.
 *
 * The user pastes a `lsv2_pt_…` (or any) workspace API key; we persist
 * it to localStorage and reload so the SDK Client picks it up on the
 * next render. Strictly client-side credentials — fine for the stage
 * demo, NOT a production auth model.
 */
const ApiKeyGate: FC<Props> = ({ onSubmit }) => {
  const [value, setValue] = useState("");

  const handle = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <div className="flex min-h-dvh items-center justify-center bg-[var(--background)] p-4">
      <form
        onSubmit={handle}
        className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-sm"
      >
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)]">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
              <path d="M12 2L2 12l10 10 10-10z" />
            </svg>
          </div>
          <h1 className="text-base font-semibold">Connect to the deployment</h1>
        </div>
        <p className="text-sm text-[var(--muted-foreground)]">
          This deployment requires a LangSmith API key to call{" "}
          <code className="rounded bg-[var(--muted)] px-1 text-xs">
            /threads
          </code>
          ,{" "}
          <code className="rounded bg-[var(--muted)] px-1 text-xs">
            /runs
          </code>
          , and{" "}
          <code className="rounded bg-[var(--muted)] px-1 text-xs">
            /assistants
          </code>
          . Paste a workspace key with permission to invoke this agent.
        </p>
        <label className="mt-4 block text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">
          LangSmith API key
        </label>
        <input
          type="password"
          autoFocus
          autoComplete="off"
          spellCheck={false}
          placeholder="lsv2_pt_…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 font-mono text-sm outline-none placeholder:text-[var(--muted-foreground)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent-bg)]"
        />
        <button
          type="submit"
          disabled={value.trim().length === 0}
          className="mt-4 w-full rounded-lg bg-[var(--primary)] py-2 text-sm font-medium text-[var(--primary-foreground)] disabled:opacity-50"
        >
          Save key and continue
        </button>
        <p className="mt-3 text-xs text-[var(--muted-foreground)]">
          Stored only in your browser&apos;s localStorage. Clear with{" "}
          <code className="rounded bg-[var(--muted)] px-1 text-[10px]">
            localStorage.removeItem(&quot;concierge:apiKey&quot;)
          </code>
          .
        </p>
      </form>
    </div>
  );
};

export default ApiKeyGate;
