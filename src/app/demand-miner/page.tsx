import dynamic from "next/dynamic";

const DemandMinerPage = dynamic(() => import("@/views/DemandMiner"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <DemandMinerPage />;
}
