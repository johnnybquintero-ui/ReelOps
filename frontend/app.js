import {
  fetchGraphQLReleases,
  fetchRestReleases,
  normaliseRelease,
} from "./api.js";

const form = document.querySelector("#query-form");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const rawResponse = document.querySelector("#raw-response");

function optionalNumber(value) {
  return value === "" ? null : Number(value);
}

function renderReleases(releases) {
  results.replaceChildren();

  for (const rawRelease of releases) {
    const release = normaliseRelease(rawRelease);
    const article = document.createElement("article");

    const title = document.createElement("h3");
    title.textContent = release.title;

    const metadata = document.createElement("p");
    metadata.textContent = [
      release.releaseDate,
      release.genres.join(", ") || "Genre unavailable",
    ].join(" · ");

    article.append(title, metadata);
    results.append(article);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const transport = form.elements.transport.value;
  const year = optionalNumber(form.elements.year.value);
  const month = optionalNumber(form.elements.month.value);

  status.textContent = `Loading through ${transport.toUpperCase()}…`;
  results.replaceChildren();
  rawResponse.textContent = "";

  try {
    const request =
      transport === "graphql"
        ? fetchGraphQLReleases
        : fetchRestReleases;

    const response = await request(year, month);

    renderReleases(response.releases);
    rawResponse.textContent = JSON.stringify(response.raw, null, 2);
    status.textContent = `${response.releases.length} releases loaded.`;
  } catch (error) {
    status.textContent = error.message;
  }
});
