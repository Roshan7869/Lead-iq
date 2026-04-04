import dynamic from "next/dynamic";

const PipelinePage = dynamic(() => import("@/views/Pipeline"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <PipelinePage />;
}
