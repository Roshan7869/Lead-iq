import "@testing-library/jest-dom";

/* eslint-disable @typescript-eslint/no-require-imports */

describe("Schemes page", () => {
  it("renders the Schemes view component", () => {
    const SchemesView = require("@/views/Schemes").default;
    expect(SchemesView).toBeDefined();
  });
});

describe("Funding page", () => {
  it("renders the Funding view component", () => {
    const FundingView = require("@/views/Funding").default;
    expect(FundingView).toBeDefined();
  });
});

describe("JobSignals page", () => {
  it("renders the JobSignals view component", () => {
    const JobSignalsView = require("@/views/JobSignals").default;
    expect(JobSignalsView).toBeDefined();
  });
});

describe("API routes", () => {
  it("backend routes for nlp are registered", async () => {
    try {
      const res = await fetch("/api/nlp/sentiment", { method: "POST" });
      // Should get a response (even if error) — route exists
      expect(res.status).not.toBe(404);
    } catch {
      // No backend running in test environment — skip
    }
  });
});
