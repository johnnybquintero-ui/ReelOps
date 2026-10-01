import test from "node:test";
import assert from "node:assert/strict";

import {
  buildRestUrl,
  fetchRestReleases,
  fetchGraphQLReleases,
} from "../api.js";

test("buildRestUrl adds year and month query parameters", () => {
  const result = buildRestUrl(2026, 10);

  assert.equal(
    result,
    "http://localhost:7071/api/releases?year=2026&month=10",
  );
});

test("buildRestUrl works with year only", () => {
  assert.equal(
    buildRestUrl(2026, null),
    "http://localhost:7071/api/releases?year=2026",
  );
});

test("buildRestUrl works with no filters", () => {
  assert.equal(
    buildRestUrl(null, null),
    "http://localhost:7071/api/releases",
  );
});

test("fetchRestReleases returns releases", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        releases: [
          {
            tmdb_id: 123,
            title: "Example Film",
          },
        ],
      }),
    });

    const result = await fetchRestReleases(2026, 10);

    assert.equal(result.releases.length, 1);
    assert.equal(result.releases[0].title, "Example Film");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchGraphQLReleases returns releases", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        data: {
          releases: [
            {
              tmdbId: 123,
              title: "Example Film",
            },
          ],
        },
      }),
    });

    const result = await fetchGraphQLReleases(2026, 10);

    assert.equal(result.releases[0].title, "Example Film");
  } finally {
    globalThis.fetch = originalFetch;
  }
});