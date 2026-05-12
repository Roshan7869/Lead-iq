"use client";

import dynamic from "next/dynamic";

const SchemesPage = dynamic(() => import("@/views/Schemes"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <SchemesPage />;
}
