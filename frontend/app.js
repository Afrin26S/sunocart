const API_URL = "http://127.0.0.1:5000";

const voiceButton = document.getElementById("voiceButton");
const searchButton = document.getElementById("searchButton");
const languageSelect = document.getElementById("language");
const queryBox = document.getElementById("query");
const statusEl = document.getElementById("status");
const productsEl = document.getElementById("products");
productsEl.innerHTML = '<p style="color:#57607a;">Your results will show up here after you search.</p>';

const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognitionImpl) {
  recognition = new SpeechRecognitionImpl();
  recognition.continuous = false;
  recognition.interimResults = false;

  voiceButton.addEventListener("click", () => {
    recognition.lang = languageSelect.value;
    statusEl.textContent = "🎧 Listening...";
    try { recognition.start(); } catch (err) {}
  });

  recognition.onresult = (event) => {
    queryBox.value = event.results[0][0].transcript;
    statusEl.textContent = "Voice captured. Tap Find Products.";
  };

  recognition.onerror = () => {
    statusEl.textContent = "Voice input failed — you can type instead.";
  };
} else {
  voiceButton.disabled = true;
  statusEl.textContent = "Voice input isn't supported in this browser — please type your request.";
}

searchButton.addEventListener("click", searchProducts);

async function searchProducts() {
  const text = queryBox.value.trim();
  if (!text) {
    statusEl.textContent = "Please speak or type a request first.";
    return;
  }

  statusEl.textContent = "Searching...";
  productsEl.innerHTML = "";

  try {
    const response = await fetch(`${API_URL}/api/shop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed");

    renderProducts(data.products);
    statusEl.textContent = data.message;
    speak(data.message);
  } catch (error) {
    console.error(error);
    statusEl.textContent = "Something went wrong — is the backend running on port 5000?";
  }
}

function renderProducts(products) {
  if (!products.length) {
    productsEl.innerHTML = "<p>No matching products found. Try a different request.</p>";
    return;
  }
  products.forEach((product) => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <h3>${escapeHtml(product.name)}</h3>
      <p class="product-price">₹${product.price}</p>
      <p>${escapeHtml(product.description)}</p>
      <p class="product-meta">Category: ${escapeHtml(product.category)}</p>
    `;
    productsEl.appendChild(card);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function speak(message) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(message);
  utterance.lang = languageSelect.value;
  utterance.rate = 0.95;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}// --- WarrantyWallet ---
const invoiceFileInput = document.getElementById("invoiceFile");
const extractButton = document.getElementById("extractButton");
const extractStatus = document.getElementById("extractStatus");
const confirmForm = document.getElementById("confirmForm");
const fieldProductName = document.getElementById("fieldProductName");
const fieldPurchaseDate = document.getElementById("fieldPurchaseDate");
const fieldWarrantyText = document.getElementById("fieldWarrantyText");
const saveWarrantyButton = document.getElementById("saveWarrantyButton");
const warrantyListEl = document.getElementById("warrantyList");

let currentS3Key = null;

extractButton.addEventListener("click", async () => {
  const file = invoiceFileInput.files[0];
  if (!file) {
    extractStatus.textContent = "Please choose an invoice image first.";
    return;
  }

  extractStatus.textContent = "Uploading and reading the invoice...";
  confirmForm.style.display = "none";

  const formData = new FormData();
  formData.append("invoice", file);

  try {
    const response = await fetch(`${API_URL}/api/warranty/extract`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Extraction failed");

    fieldProductName.value = data.product_name || "";
    fieldPurchaseDate.value = data.purchase_date || "";
    fieldWarrantyText.value = data.warranty_text || "";
    currentS3Key = data.s3_key;

    confirmForm.style.display = "block";
    extractStatus.textContent = "Review the details below, fix anything wrong, then save.";
  } catch (error) {
    console.error(error);
    extractStatus.textContent = `Error: ${error.message}`;
  }
});

saveWarrantyButton.addEventListener("click", async () => {
  const payload = {
    product_name: fieldProductName.value.trim(),
    purchase_date: fieldPurchaseDate.value.trim(),
    warranty_text: fieldWarrantyText.value.trim(),
    s3_key: currentS3Key,
  };

  if (!payload.product_name) {
    extractStatus.textContent = "Product name is required.";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/warranty/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Save failed");

    extractStatus.textContent = "Saved!";
    confirmForm.style.display = "none";
    invoiceFileInput.value = "";
    loadWarranties();
  } catch (error) {
    console.error(error);
    extractStatus.textContent = `Error: ${error.message}`;
  }
});

async function loadWarranties() {
  try {
    const response = await fetch(`${API_URL}/api/warranty/list`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load warranties");
    renderWarranties(data.items || []);
  } catch (error) {
    console.error(error);
  }
}

function renderWarranties(items) {
  if (!items.length) {
    warrantyListEl.innerHTML = "<p>No warranties saved yet.</p>";
    return;
  }
  warrantyListEl.innerHTML = "";
  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <h3>${escapeHtml(item.product_name)}</h3>
      <p class="product-meta">Purchased: ${escapeHtml(item.purchase_date || "unknown")}</p>
      <p>${escapeHtml(item.warranty_text || "No warranty details recorded")}</p>
    `;
    warrantyListEl.appendChild(card);
  });
}

loadWarranties();