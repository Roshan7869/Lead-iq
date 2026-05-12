"use client";

import dynamic from "next/dynamic";

const JobSignalsPage = dynamic(() => import("@/views/JobSignals"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <JobSignalsPage />;
}
