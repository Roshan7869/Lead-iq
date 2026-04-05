import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode for catching potential issues early
  reactStrictMode: true,

  // Compress responses
  compress: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [],
  },

  // ── Bundle optimizations ───────────────────────────────────────────────────
  experimental: {
    // Optimise package imports — tree-shake large icon/UI libraries
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-dialog",
      "@radix-ui/react-select",
      "@radix-ui/react-tabs",
      "recharts",
    ],
  },

  // Webpack split-chunk strategy: shared vendor + UI chunk
  webpack(config, { isServer }) {
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          ...(config.optimization.splitChunks as object),
          cacheGroups: {
            // Large UI libraries → separate chunk, cached aggressively
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
          },
        },
      };
    }
    return config;
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;

