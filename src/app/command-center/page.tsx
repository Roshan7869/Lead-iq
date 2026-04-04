import dynamic from "next/dynamic";

const CommandCenterPage = dynamic(() => import("@/views/CommandCenter"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <CommandCenterPage />;
}
