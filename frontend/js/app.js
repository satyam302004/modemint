const BASE_URL = window.location.origin;

const state = { catalog: [], favorites: [], lastOutfits: [] };

const outfitContainer = document.getElementById("outfits");
const catalogContainer = document.getElementById("catalog");
const favoritesContainer = document.getElementById("favorites");
const trendSignals = document.getElementById("trendSignals");
const wardrobeList = document.getElementById("wardrobeList");
const wardrobeOutfits = document.getElementById("wardrobeOutfits");
const wardrobeImageInput = document.getElementById("wardrobeImage");
const wardrobePreview = document.getElementById("wardrobePreview");
const wardrobeAnalysis = document.getElementById("wardrobeAnalysis");
const chatResponse = document.getElementById("chatResponse");
const resultsSummary = document.getElementById("resultsSummary");
const openCameraButton = document.getElementById("openCameraButton");
const closeCameraButton = document.getElementById("closeCameraButton");
const snapPhotoButton = document.getElementById("snapPhotoButton");
const cameraContainer = document.getElementById("cameraContainer");
const cameraStreamElement = document.getElementById("cameraStream");
const cameraCanvas = document.getElementById("cameraCanvas");
let currentCameraStream = null;

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.error || data.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return data;
}

function currency(value) {
  return `Rs. ${Number(value).toLocaleString("en-IN")}`;
}

function absoluteImage(path) {
  return path ? `${BASE_URL}${path}` : "";
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function createEmpty(message) {
  return createElement("div", "empty", message);
}

function createPill(text) {
  return createElement("span", "pill", text);
}

function createExternalLink(label, href) {
  const link = createElement("a", "", label);
  link.href = href || "#";
  link.target = "_blank";
  link.rel = "noreferrer";
  return link;
}

function createButton(label, className, dataAttribute, value) {
  const button = createElement("button", className, label);
  button.dataset[dataAttribute] = value;
  return button;
}

function appendMetaRow(container, values) {
  const row = createElement("div", "meta-row");
  values.forEach((value) => row.appendChild(createPill(value)));
  container.appendChild(row);
}

function appendPlainText(container, text) {
  const lines = text.split("\n");
  lines.forEach((line, index) => {
    if (index > 0) container.appendChild(document.createElement("br"));
    if (line) container.appendChild(document.createTextNode(line));
  });
}

function appendTextWithBreaksAndLinks(container, text) {
  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  let lastIndex = 0;
  let match;

  while ((match = linkPattern.exec(text)) !== null) {
    appendPlainText(container, text.slice(lastIndex, match.index));
    const link = createExternalLink(match[1], match[2]);
    link.style.fontWeight = "600";
    link.style.textDecoration = "underline";
    container.appendChild(link);
    lastIndex = linkPattern.lastIndex;
  }

  appendPlainText(container, text.slice(lastIndex));
}

function switchTab(name) {
  document.querySelectorAll(".nav-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.tab === name);
  });
  document.querySelectorAll(".section").forEach((section) => {
    section.classList.toggle("active", section.dataset.section === name);
  });
}

function renderCatalog() {
  catalogContainer.innerHTML = "";
  if (!state.catalog.length) {
    catalogContainer.appendChild(createEmpty("No products loaded yet."));
    return;
  }

  state.catalog.slice().sort((a, b) => b.trend_score - a.trend_score).forEach((product) => {
    const card = createElement("article", "card");
    appendMetaRow(card, [product.category, `Trend ${product.trend_score}`]);
    card.appendChild(createElement("h3", "", product.name));
    card.appendChild(createElement("p", "muted", `${product.brand} - ${product.designer_type}`));
    card.appendChild(createElement("p", "", product.description));
    const priceTag = createElement("p", "price-tag");
    priceTag.appendChild(createElement("strong", "", currency(product.price)));
    card.appendChild(priceTag);
    card.appendChild(createExternalLink("Buy link", product.buy_link));
    catalogContainer.appendChild(card);
  });

  document.getElementById("catalogCount").textContent = state.catalog.length;
}

async function loadTrends() {
  try {
    const response = await fetch(`${BASE_URL}/trends`);
    const trends = await parseResponse(response);
    trendSignals.innerHTML = "";
    if (!trends.length) {
      trendSignals.appendChild(createEmpty("No trend signals loaded yet."));
      return;
    }

    trends.slice(0, 6).forEach((trend) => {
      const card = createElement("article", "card");
      appendMetaRow(card, [trend.region, `Score ${trend.score}`]);
      card.appendChild(createElement("h3", "", trend.keyword));
      card.appendChild(createElement("p", "muted", `${trend.source} - ${trend.season}`));
      const pillRow = createElement("div", "pill-row");
      (trend.styles || []).slice(0, 3).forEach((value) => pillRow.appendChild(createPill(value)));
      card.appendChild(pillRow);
      card.appendChild(createElement("p", "", trend.notes || "Curated fashion signal for ranking."));
      trendSignals.appendChild(card);
    });
  } catch (error) {
    trendSignals.innerHTML = "";
    trendSignals.appendChild(createEmpty(error.message));
  }
}

function renderOutfits(outfits) {
  outfitContainer.innerHTML = "";
  state.lastOutfits = outfits;
  document.getElementById("resultCount").textContent = outfits.length;
  document.getElementById("topTrendScore").textContent = outfits[0] ? outfits[0].trend_score.toFixed(1) : "0.0";
  if (!outfits.length) {
    outfitContainer.appendChild(createEmpty("No outfits matched your filters."));
    return;
  }

  outfits.forEach((outfit, index) => {
    const card = createElement("article", `card ${index === 0 ? "best" : ""}`.trim());

    const resultHero = createElement("div", "result-hero");
    const heroCopy = createElement("div");
    heroCopy.appendChild(createElement("h3", "", index === 0 ? "Best Outfit" : "Outfit"));
    heroCopy.appendChild(createElement("p", "muted", "Generated for your current filter set."));
    const priceTag = createElement("div", "price-tag");
    priceTag.appendChild(createElement("strong", "", currency(outfit.total_price)));
    resultHero.appendChild(heroCopy);
    resultHero.appendChild(priceTag);
    card.appendChild(resultHero);

    const statsRow = createElement("div", "pill-row");
    statsRow.appendChild(createPill(`Score ${outfit.score}`));
    statsRow.appendChild(createPill(`Trend ${outfit.trend_score}`));
    card.appendChild(statsRow);

    const itemList = createElement("div", "item-list");
    Object.entries(outfit.items).forEach(([category, product]) => {
      const itemChip = createElement("div", "item-chip");
      itemChip.appendChild(createElement("strong", "", category));
      itemChip.appendChild(createElement("div", "", product.name));
      itemChip.appendChild(createElement("div", "muted", `${product.brand} - ${currency(product.price)}`));
      itemChip.appendChild(createExternalLink("View product", product.buy_link));
      itemList.appendChild(itemChip);
    });
    card.appendChild(itemList);

    const reasonsRow = createElement("div", "pill-row");
    outfit.reasons.forEach((reason) => reasonsRow.appendChild(createPill(reason)));
    card.appendChild(reasonsRow);

    const buttonRow = createElement("div", "button-row");
    buttonRow.appendChild(createButton("Save outfit", "primary", "save", index));
    card.appendChild(buttonRow);

    outfitContainer.appendChild(card);
  });
}

function renderFavorites() {
  favoritesContainer.innerHTML = "";
  document.getElementById("favoriteCount").textContent = state.favorites.length;
  if (!state.favorites.length) {
    favoritesContainer.appendChild(createEmpty("No favorites yet."));
    return;
  }

  state.favorites.forEach((favorite) => {
    const names = Object.values(favorite.outfit.items).map((item) => item.name).join(", ");
    const card = createElement("article", "card");
    card.appendChild(createElement("h3", "", favorite.name));
    card.appendChild(createElement("p", "muted", names));
    const buttonRow = createElement("div", "button-row");
    buttonRow.appendChild(createButton("Remove", "ghost", "delete", favorite.id));
    card.appendChild(buttonRow);
    favoritesContainer.appendChild(card);
  });
}

function renderWardrobe(items) {
  wardrobeList.innerHTML = "";
  if (!items.length) {
    wardrobeList.appendChild(createEmpty("Add a few items to your wardrobe."));
    return;
  }

  items.forEach((item) => {
    const card = createElement("article", "card");
    if (item.image) {
      const image = document.createElement("img");
      image.className = "wardrobe-photo";
      image.src = absoluteImage(item.image);
      image.alt = item.name;
      card.appendChild(image);
    }
    card.appendChild(createElement("h3", "", item.name));
    card.appendChild(createElement("p", "muted", `${item.category} - ${item.color} - ${item.style}`));
    const buttonRow = createElement("div", "button-row");
    buttonRow.appendChild(createButton("Remove", "ghost", "deleteWardrobe", item.id));
    card.appendChild(buttonRow);
    wardrobeList.appendChild(card);
  });
}

function renderWardrobeOutfits(outfits) {
  wardrobeOutfits.innerHTML = "";
  if (!outfits.length) {
    wardrobeOutfits.appendChild(createEmpty("Your wardrobe needs at least a top, bottom, and shoes."));
    return;
  }

  outfits.forEach((outfit, index) => {
    const card = createElement("article", `card ${index === 0 ? "best" : ""}`.trim());
    card.appendChild(createElement("h3", "", index === 0 ? "Best From Wardrobe" : "Wardrobe Outfit"));
    const scoreLine = createElement("p");
    scoreLine.appendChild(createElement("strong", "", `Score ${outfit.score}`));
    card.appendChild(scoreLine);

    const itemList = createElement("div", "item-list");
    Object.entries(outfit.items).forEach(([category, item]) => {
      const itemChip = createElement("div", "item-chip");
      if (item.image) {
        const image = document.createElement("img");
        image.src = absoluteImage(item.image);
        image.alt = item.name;
        itemChip.appendChild(image);
      }
      itemChip.appendChild(createElement("strong", "", category));
      itemChip.appendChild(createElement("div", "", item.name));
      itemChip.appendChild(createElement("div", "muted", `${item.color} - ${item.style}`));
      itemList.appendChild(itemChip);
    });
    card.appendChild(itemList);

    const reasonsRow = createElement("div", "pill-row");
    outfit.reasons.forEach((reason) => reasonsRow.appendChild(createPill(reason)));
    card.appendChild(reasonsRow);
    wardrobeOutfits.appendChild(card);
  });
}

async function loadCatalog() {
  try {
    const response = await fetch(`${BASE_URL}/products`);
    state.catalog = await parseResponse(response);
    renderCatalog();
  } catch (error) {
    catalogContainer.innerHTML = "";
    catalogContainer.appendChild(createEmpty(error.message));
  }
}

async function loadFavorites() {
  try {
    const response = await fetch(`${BASE_URL}/favorites`);
    state.favorites = await parseResponse(response);
    renderFavorites();
  } catch (error) {
    favoritesContainer.innerHTML = "";
    favoritesContainer.appendChild(createEmpty(error.message));
  }
}

async function loadWardrobe() {
  try {
    const response = await fetch(`${BASE_URL}/wardrobe`);
    renderWardrobe(await parseResponse(response));
  } catch (error) {
    wardrobeList.innerHTML = "";
    wardrobeList.appendChild(createEmpty(error.message));
  }
}

async function generateOutfits() {
  const payload = {
    occasion: document.getElementById("occasion").value,
    budget: Number(document.getElementById("budget").value || 0),
    style: document.getElementById("style").value
  };
  try {
    const response = await fetch(`${BASE_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await parseResponse(response);
    resultsSummary.textContent = `${data.summary.count} outfits found.`;
    renderOutfits(data.outfits);
  } catch (error) {
    resultsSummary.textContent = error.message;
    outfitContainer.innerHTML = "";
    outfitContainer.appendChild(createEmpty(error.message));
  }
}

async function saveFavorite(index) {
  const outfit = state.lastOutfits[index];
  if (!outfit) return;
  try {
    const response = await fetch(`${BASE_URL}/favorites`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: `Saved ${document.getElementById("occasion").value} look`, outfit })
    });
    await parseResponse(response);
    await loadFavorites();
  } catch (error) {
    resultsSummary.textContent = error.message;
  }
}

async function deleteFavorite(id) {
  try {
    const response = await fetch(`${BASE_URL}/favorites/${id}`, { method: "DELETE" });
    await parseResponse(response);
    await loadFavorites();
  } catch (error) {
    resultsSummary.textContent = error.message;
  }
}

async function askChatbot() {
  const message = document.getElementById("chatInput").value.trim();
  if (!message) {
    chatResponse.textContent = "Add a question first.";
    return;
  }
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await parseResponse(response);
    const warning = data.warning ? `\n\nFallback note: ${data.warning}` : "";
    const text = data.model ? `${data.response}\n\nModel: ${data.model}${warning}` : data.response;
    chatResponse.textContent = "";
    appendTextWithBreaksAndLinks(chatResponse, text);
  } catch (error) {
    chatResponse.textContent = error.message;
  }
}

async function addWardrobeItem() {
  let image = wardrobeImageInput.dataset.uploadedImage || "";
  if (!image && wardrobeImageInput.files && wardrobeImageInput.files[0]) {
    const formData = new FormData();
    formData.append("image", wardrobeImageInput.files[0]);
    const uploadResponse = await fetch(`${BASE_URL}/wardrobe/upload`, { method: "POST", body: formData });
    const uploadData = await parseResponse(uploadResponse);
    image = uploadData.image || "";
  }

  const payload = {
    name: document.getElementById("wardrobeName").value.trim(),
    category: document.getElementById("wardrobeCategory").value,
    color: document.getElementById("wardrobeColor").value.trim() || "unknown",
    style: document.getElementById("wardrobeStyle").value,
    occasion: document.getElementById("wardrobeOccasion").value,
    image
  };
  if (!payload.name) return;

  try {
    const response = await fetch(`${BASE_URL}/wardrobe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await parseResponse(response);

    document.getElementById("wardrobeName").value = "";
    document.getElementById("wardrobeColor").value = "";
    wardrobeImageInput.value = "";
    wardrobeImageInput.dataset.uploadedImage = "";
    wardrobePreview.style.display = "none";
    wardrobePreview.src = "";
    wardrobeAnalysis.textContent = "Upload a clothing image and the app will try to guess the details.";
    await loadWardrobe();
    await generateWardrobeOutfits();
  } catch (error) {
    wardrobeAnalysis.textContent = error.message;
  }
}

async function generateWardrobeOutfits() {
  try {
    const response = await fetch(`${BASE_URL}/wardrobe/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        occasion: document.getElementById("wardrobeOccasion").value,
        style: document.getElementById("wardrobeStyle").value
      })
    });
    const data = await parseResponse(response);
    renderWardrobeOutfits(data.outfits);
  } catch (error) {
    wardrobeOutfits.innerHTML = "";
    wardrobeOutfits.appendChild(createEmpty(error.message));
  }
}

async function deleteWardrobeItem(id) {
  try {
    const response = await fetch(`${BASE_URL}/wardrobe/${id}`, { method: "DELETE" });
    await parseResponse(response);
    await loadWardrobe();
    await generateWardrobeOutfits();
  } catch (error) {
    wardrobeAnalysis.textContent = error.message;
  }
}

document.querySelectorAll(".nav-card").forEach((card) => {
  card.addEventListener("click", () => switchTab(card.dataset.tab));
});

document.getElementById("recommendButton").addEventListener("click", generateOutfits);
document.getElementById("chatButton").addEventListener("click", askChatbot);
document.getElementById("addWardrobeButton").addEventListener("click", addWardrobeItem);
document.getElementById("generateWardrobeButton").addEventListener("click", generateWardrobeOutfits);
document.getElementById("presetCollege").addEventListener("click", () => {
  document.getElementById("occasion").value = "college";
  document.getElementById("budget").value = "3000";
  document.getElementById("style").value = "streetwear";
  generateOutfits();
});

async function processWardrobeMedia(file) {
  if (!file) {
    wardrobePreview.style.display = "none";
    wardrobePreview.src = "";
    wardrobeAnalysis.textContent = "Upload or snap a clothing image and the app will try to guess the details.";
    wardrobeImageInput.dataset.uploadedImage = "";
    return;
  }

  wardrobePreview.src = URL.createObjectURL(file);
  wardrobePreview.style.display = "block";
  wardrobeAnalysis.textContent = "Analyzing image...";

  const formData = new FormData();
  formData.append("image", file);
  try {
    const response = await fetch(`${BASE_URL}/wardrobe/upload`, {
      method: "POST",
      body: formData
    });
    const data = await parseResponse(response);
    const analysis = data.analysis || {};
    const inferredItem = (analysis.items && analysis.items[0]) || {};

    document.getElementById("wardrobeName").value = inferredItem.name || document.getElementById("wardrobeName").value;
    document.getElementById("wardrobeCategory").value = inferredItem.category || document.getElementById("wardrobeCategory").value;
    document.getElementById("wardrobeColor").value = inferredItem.color || document.getElementById("wardrobeColor").value;
    document.getElementById("wardrobeStyle").value = inferredItem.style || document.getElementById("wardrobeStyle").value;
    document.getElementById("wardrobeOccasion").value = inferredItem.occasion || document.getElementById("wardrobeOccasion").value;
    wardrobeImageInput.dataset.uploadedImage = data.image || "";
    wardrobeAnalysis.textContent = `AI guessed ${inferredItem.name || "item"} - ${inferredItem.category || "top"} - ${inferredItem.color || "unknown"} (${analysis.source || "fallback"})`;
  } catch (error) {
    wardrobeAnalysis.textContent = error.message;
  }
}

wardrobeImageInput.addEventListener("change", async () => {
  const file = wardrobeImageInput.files && wardrobeImageInput.files[0];
  await processWardrobeMedia(file);
});

openCameraButton.addEventListener("click", async () => {
  try {
    currentCameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    cameraStreamElement.srcObject = currentCameraStream;
    cameraContainer.style.display = "block";
    wardrobePreview.style.display = "none";
  } catch (err) {
    alert(`Camera access denied or unavailable: ${err.message}`);
  }
});

closeCameraButton.addEventListener("click", () => {
  if (currentCameraStream) {
    currentCameraStream.getTracks().forEach((track) => track.stop());
    currentCameraStream = null;
  }
  cameraContainer.style.display = "none";
});

snapPhotoButton.addEventListener("click", async () => {
  if (!currentCameraStream) return;
  const video = cameraStreamElement;
  cameraCanvas.width = video.videoWidth;
  cameraCanvas.height = video.videoHeight;
  const ctx = cameraCanvas.getContext("2d");
  ctx.drawImage(video, 0, 0, cameraCanvas.width, cameraCanvas.height);

  currentCameraStream.getTracks().forEach((track) => track.stop());
  currentCameraStream = null;
  cameraContainer.style.display = "none";

  cameraCanvas.toBlob(async (blob) => {
    if (!blob) return;
    const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
    await processWardrobeMedia(file);
  }, "image/jpeg", 0.9);
});

outfitContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-save]");
  if (button) saveFavorite(Number(button.dataset.save));
});

favoritesContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete]");
  if (button) deleteFavorite(button.dataset.delete);
});

wardrobeList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete-wardrobe]");
  if (button) deleteWardrobeItem(button.dataset.deleteWardrobe);
});

Promise.allSettled([loadCatalog(), loadFavorites(), loadWardrobe(), loadTrends()]).then(() => {
  generateOutfits();
  generateWardrobeOutfits();
});
