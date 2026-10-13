import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Interactive AI Demo · SarcoScan Sarcopenia & Osteoporosis Triage",
  description:
    "Test SarcoScan's multimodal AI engine with custom knee AP radiographs or clinical presets, 3-trial handgrip dynamometer calculator, and immediate risk tier staging.",
  keywords: [
    "Sarcopenia AI Demo",
    "Knee X-Ray Ingestion",
    "Handgrip Dynamometer Calculator",
    "Osteoporosis Screening Demo",
    "AWGS 2019 Criteria",
    "SarcoScan Live Demo",
  ],
  openGraph: {
    title: "Interactive AI Demo · SarcoScan Screening Station",
    description:
      "Upload a knee AP radiograph and calculate handgrip force to simulate on-premise AI triage for sarcopenia and osteoporosis.",
    url: "https://sarcoscan.ai/demo",
    siteName: "SarcoScan",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Interactive AI Demo · SarcoScan",
    description:
      "Simulate on-premise AI clinical triage with routine knee AP X-rays and handgrip dynamometer trials.",
  },
};

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
