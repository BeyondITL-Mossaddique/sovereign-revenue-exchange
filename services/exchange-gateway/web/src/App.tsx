import * as React from "react";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import { IdentityCard } from "./components/IdentityCard";
import { ReturnsCard } from "./components/ReturnsCard";
import { GovernanceStrip } from "./components/GovernanceStrip";
import { DuplicateFinder } from "./components/DuplicateFinder";
import { ProfileSkeleton } from "./components/ProfileSkeleton";
import { ErrorNotice, NotFoundNotice } from "./components/StatusNotice";
import { fetchTaxpayerProfile, NotFoundError } from "./lib/api";
import type { TaxpayerProfile } from "./lib/types";

const DEFAULT_TIN = "900000000001";

type State =
  | { kind: "idle" }
  | { kind: "loading"; tin: string }
  | { kind: "success"; tin: string; profile: TaxpayerProfile }
  | { kind: "not-found"; tin: string }
  | { kind: "error"; tin: string; message: string };

export default function App() {
  const [tin, setTin] = React.useState(DEFAULT_TIN);
  const [state, setState] = React.useState<State>({ kind: "idle" });

  const lookup = React.useCallback(async (next: string) => {
    setState({ kind: "loading", tin: next });
    try {
      const profile = await fetchTaxpayerProfile(next);
      setState({ kind: "success", tin: next, profile });
    } catch (err) {
      if (err instanceof NotFoundError) {
        setState({ kind: "not-found", tin: next });
      } else {
        setState({
          kind: "error",
          tin: next,
          message: (err as Error).message || "Unknown error",
        });
      }
    }
  }, []);

  // Populate the dashboard on first load.
  React.useEffect(() => {
    lookup(DEFAULT_TIN);
  }, [lookup]);

  const loading = state.kind === "loading";

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main
        id="main"
        className="mx-auto w-full max-w-page flex-1 px-6 py-10 sm:py-12"
      >
        <Hero
          tin={tin}
          onTinChange={setTin}
          onSubmit={() => lookup(tin.trim())}
          loading={loading}
        />

        <div className="mt-10 space-y-6" aria-live="polite">
          {state.kind === "loading" && <ProfileSkeleton />}

          {state.kind === "not-found" && <NotFoundNotice tin={state.tin} />}

          {state.kind === "error" && (
            <ErrorNotice message={state.message} />
          )}

          {state.kind === "success" && (
            <>
              <div className="grid gap-4 lg:grid-cols-2">
                <IdentityCard
                  taxpayer={state.profile.taxpayer}
                  servedToAgency={state.profile.served_to_agency}
                />
                <ReturnsCard returns={state.profile.returns} />
              </div>
              <GovernanceStrip />
              <DuplicateFinder />
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
