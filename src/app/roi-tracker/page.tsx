import dynamic from "next/dynamic";

const ROITrackerPage = dynamic(() => import("@/views/ROITracker"), {
  ssr: false,
  loading: () => <div className="flex-1 p-8 animate-pulse" />,
});

export default function Page() {
  return <ROITrackerPage />;
}
