export const API_BASE_URL = "http://localhost:7071/api";

export const RELEASES_QUERY = `
  query Releases($year: Int, $month: Int) {
    releases(year: $year, month: $month) {
      tmdbId
      title
      releaseDate
      originalLanguage
      overview
      popularity
      genres
    }
  }
`;

export function normaliseRelease(release) {
  return {
    tmdbId: release.tmdbId ?? release.tmdb_id,
    title: release.title,
    releaseDate: release.releaseDate ?? release.release_date,
    genres: release.genres ?? [],
  };
}

export function buildRestUrl(year, month) {
  const params = new URLSearchParams();

  if (year !== null) {
    params.set("year", String(year));
  }

  if (month !== null) {
    params.set("month", String(month));
  }

  const queryString = params.toString();
  const suffix = queryString ? `?${queryString}` : "";

  return `${API_BASE_URL}/releases${suffix}`;
}

export async function fetchRestReleases(year, month) {
  const response = await fetch(buildRestUrl(year, month));
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error ?? `REST returned ${response.status}`);
  }

  return {
    releases: payload.releases,
    raw: payload,
  };
}

export async function fetchGraphQLReleases(year, month) {
  const response = await fetch(`${API_BASE_URL}/graphql`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: RELEASES_QUERY,
      variables: { year, month },
    }),
  });

  const payload = await response.json();

  if (!response.ok) {
    throw new Error(
      payload.error ?? `GraphQL HTTP returned ${response.status}`,
    );
  }

  if (payload.errors?.length) {
    const messages = payload.errors.map((error) => error.message);
    throw new Error(messages.join("; "));
  }

  return {
    releases: payload.data.releases,
    raw: payload,
  };
}
