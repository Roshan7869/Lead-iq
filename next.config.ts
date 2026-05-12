import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  reactStrictMode: true,
  compress: true,
  productionBrowserSourceMaps: false,  // smaller bundles in production

  // ── Image optimization ─────────────────────────────────────────────────────
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [],
  },

  // ── Bundle optimizations (Day 26) ──────────────────────────────────────────
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-dialog",
      "@radix-ui/react-select",
      "@radix-ui/react-tabs",
      "recharts",
      "@tanstack/react-query",
      "date-fns",
    ],
  },

  // ── Transpile large packages for better tree-shaking ───────────────────────
  transpilePackages: [
    "lucide-react",
  ],

  // ── Webpack split-chunk strategy: shared vendor + UI chunk ─────────────────
  webpack(config, { isServer }) {
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          ...(config.optimization.splitChunks as object),
          chunks: "all" as const,
          maxInitialRequests: 25,
          minSize: 20000,
          cacheGroups: {
            radix: {
              name: "chunk-radix",
              test: /node_modules\/@radix-ui/,
              chunks: "all" as const,
              priority: 20,
            },
            recharts: {
              name: "chunk-recharts",
              test: /node_modules\/recharts/,
              chunks: "all" as const,
              priority: 18,
            },
            lucide: {
              name: "chunk-lucide",
              test: /node_modules\/lucide-react/,
              chunks: "all" as const,
              priority: 16,
            },
            framer: {
              name: "chunk-framer",
            },
            reactQuery: {
              name: "chunk-react-query",
              test: /node_modules\/@tanstack\/react-query/,
              chunks: "all" as const,
              priority: 14,
            },
            vendors: {
              name: "chunk-vendors",
              test: /node_modules/,
              chunks: "all" as const,
              priority: 10,
              minChunks: 2,
            },
            common: {
              name: "chunk-common",
              minChunks: 2,
              chunks: "all" as const,
              priority: 5,
              reuseExistingChunk: true,
            },
          },
        },
      };
    }
    return config;
  },

  // ── Security headers ───────────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Content-Security-Policy", value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https:; frame-ancestors 'none';" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
        ],
      },
      // Cache static assets aggressively (immutable hashed filenames)
      {
        source: "/_next/static/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);

