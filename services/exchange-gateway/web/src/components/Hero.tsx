import { Search } from "lucide-react";

export function Hero({
  tin,
  onTinChange,
  onSubmit,
  loading,
}: {
  tin: string;
  onTinChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
}) {
  const tinValid = /^\d{12}$/.test(tin.trim());

  return (
    <section className="animate-fade-up" aria-labelledby="hero-title">
      <h1
        id="hero-title"
        className="font-display text-[40px] font-medium leading-[1.1] tracking-tight text-ink sm:text-[44px]"
      >
        Governed access to revenue records,
        <br className="hidden sm:block" /> for the agencies that need it.
      </h1>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted">
        Look up a single taxpayer through the inter-agency exchange. Every call
        is authenticated, rate-limited and logged. Tax liability is computed
        from current illustrative figures.
      </p>
      <form
        className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={(e) => {
          e.preventDefault();
          if (tinValid) onSubmit();
        }}
      >
        <div className="flex-1">
          <label
            htmlFor="tin-input"
            className="mb-1.5 block text-xs font-medium uppercase tracking-[0.08em] text-muted"
          >
            TIN <span lang="bn" className="text-muted/80">টিআইএন</span>
          </label>
          <input
            id="tin-input"
            inputMode="numeric"
            autoComplete="off"
            spellCheck={false}
            className="input-base tabular font-mono text-[1.05rem]"
            placeholder="12-digit synthetic TIN"
            value={tin}
            onChange={(e) => onTinChange(e.target.value)}
            aria-invalid={!tinValid}
            aria-describedby="tin-help"
          />
          <p id="tin-help" className="mt-1.5 text-xs text-muted">
            Example: <span className="font-mono">900000000001</span> — a valid
            seeded test taxpayer.
          </p>
        </div>
        <button
          type="submit"
          className="btn-primary sm:w-auto"
          disabled={!tinValid || loading}
        >
          <Search className="h-4 w-4" />
          {loading ? "Looking up…" : "Look up taxpayer"}
        </button>
      </form>
    </section>
  );
}
