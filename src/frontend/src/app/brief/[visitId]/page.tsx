import { Suspense } from "react";
import BriefView from "./brief-view";

// Server shell: the view reads the visit id and day from the URL on the
// client (useParams/useSearchParams suspend during prerender), so it renders
// behind a Suspense boundary per the Next.js docs.
export default function BriefPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <BriefView />
    </Suspense>
  );
}
