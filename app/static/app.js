const registerForm = document.getElementById("register-form");
const registerResult = document.getElementById("register-result");

const verifyForm = document.getElementById("verify-form");
const verifyResult = document.getElementById("verify-result");

const reloadRecordsButton = document.getElementById("reload-records");
const recordsResult = document.getElementById("records-result");
const recordsTbody = document.getElementById("records-tbody");

const verifyLedgerButton = document.getElementById("verify-ledger");
const ledgerResult = document.getElementById("ledger-result");
const ledgerSignatureResult = document.getElementById("ledger-signature-result");

const loadAnchorButton = document.getElementById("load-anchor");
const copyAnchorHashButton = document.getElementById("copy-anchor-hash");
const copyAnchorSignatureButton = document.getElementById("copy-anchor-signature");
const anchorResult = document.getElementById("anchor-result");

const healthDot = document.getElementById("health-dot");
const healthText = document.getElementById("health-text");
const anchorDot = document.getElementById("anchor-dot");
const anchorText = document.getElementById("anchor-text");

let latestAnchor = null;

function setResult(el, text, tone = "") {
  el.textContent = text;
  el.classList.remove("ok", "warn", "ng");
  if (tone) {
    el.classList.add(tone);
  }
}

function setBusy(button, busyText) {
  const original = button.dataset.originalText || button.textContent;
  button.dataset.originalText = original;
  button.disabled = true;
  button.textContent = busyText;
}

function clearBusy(button) {
  button.disabled = false;
  button.textContent = button.dataset.originalText || button.textContent;
}

function apiErrorMessage(json, fallback) {
  if (json && json.error && typeof json.error.message === "string") {
    return json.error.message;
  }
  return fallback;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setHealth(online) {
  healthDot.classList.toggle("ok", online);
  healthText.textContent = online ? "API接続: OK" : "API接続: NG";
}

function setAnchorState(ready) {
  anchorDot.classList.toggle("ok", ready);
  anchorText.textContent = ready ? "アンカー: 取得済み" : "アンカー: 未取得";
}

async function copyText(text) {
  if (!text) {
    return false;
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (_error) {
    return false;
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/v1/health");
    const data = await response.json();
    setHealth(response.status === 200 && data.status === "ok");
  } catch (_error) {
    setHealth(false);
  }
}

async function loadRecords() {
  setResult(recordsResult, "一覧を取得しています...", "warn");
  try {
    const response = await fetch("/api/v1/records");
    const data = await response.json();

    if (response.status !== 200) {
      setResult(recordsResult, apiErrorMessage(data, "一覧取得に失敗しました"), "ng");
      return;
    }

    recordsTbody.innerHTML = "";
    for (const item of data.items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(item.index)}</td>
        <td>${escapeHtml(item.timestamp_utc)}</td>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.version)}</td>
        <td>${escapeHtml(item.sha256)}</td>
        <td>${escapeHtml(item.file_size_bytes)}</td>
        <td>${escapeHtml(item.original_filename)}</td>
        <td>${escapeHtml(item.signing_key_id ?? "")}</td>
      `;
      recordsTbody.appendChild(tr);
    }
    setResult(recordsResult, `件数: ${data.count}`, "ok");
  } catch (_error) {
    setResult(recordsResult, "一覧取得に失敗しました", "ng");
  }
}

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const submitButton = registerForm.querySelector('button[type="submit"]');
  const name = document.getElementById("register-name").value.trim();
  const version = document.getElementById("register-version").value.trim();
  const fileInput = document.getElementById("register-file");
  const file = fileInput.files[0];

  if (!file) {
    setResult(registerResult, "入力値が不正です", "ng");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("version", version);
  formData.append("file", file);

  setBusy(submitButton, "登録中...");
  setResult(registerResult, "登録処理を実行しています...", "warn");
  try {
    const response = await fetch("/api/v1/records/register", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.status === 201) {
      setResult(
        registerResult,
        `登録完了: ${data.name} ${data.version}\nsha256=${data.sha256}\nindex=${data.index}`,
        "ok"
      );
      await loadRecords();
      return;
    }

    if (response.status === 409) {
      setResult(registerResult, "同じ name/version は登録済みです", "warn");
      return;
    }

    if (response.status === 400) {
      setResult(registerResult, "入力値が不正です", "ng");
      return;
    }

    setResult(registerResult, apiErrorMessage(data, "登録処理に失敗しました"), "ng");
  } catch (_error) {
    setResult(registerResult, "登録処理に失敗しました", "ng");
  } finally {
    clearBusy(submitButton);
  }
});

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const submitButton = verifyForm.querySelector('button[type="submit"]');
  const name = document.getElementById("verify-name").value.trim();
  const version = document.getElementById("verify-version").value.trim();
  const fileInput = document.getElementById("verify-file");
  const file = fileInput.files[0];

  if (!file) {
    setResult(verifyResult, "入力値が不正です", "ng");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("version", version);
  formData.append("file", file);

  setBusy(submitButton, "検証中...");
  setResult(verifyResult, "検証処理を実行しています...", "warn");
  try {
    const response = await fetch("/api/v1/records/verify", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.status === 200) {
      setResult(
        verifyResult,
        `検証成功: 登録情報と一致\nmatch_mode=${data.match_mode}\nname=${data.name}, version=${data.version}\nsha256=${data.sha256}`,
        "ok"
      );
      return;
    }

    if (response.status === 404) {
      setResult(verifyResult, "一致する登録が見つかりません", "warn");
      return;
    }

    if (response.status === 400) {
      setResult(verifyResult, "入力値が不正です", "ng");
      return;
    }

    setResult(verifyResult, apiErrorMessage(data, "検証処理に失敗しました"), "ng");
  } catch (_error) {
    setResult(verifyResult, "検証処理に失敗しました", "ng");
  } finally {
    clearBusy(submitButton);
  }
});

reloadRecordsButton.addEventListener("click", async () => {
  setBusy(reloadRecordsButton, "更新中...");
  try {
    await loadRecords();
  } finally {
    clearBusy(reloadRecordsButton);
  }
});

verifyLedgerButton.addEventListener("click", async () => {
  setBusy(verifyLedgerButton, "検証中...");
  setResult(ledgerResult, "台帳を検証しています...", "warn");
  setResult(ledgerSignatureResult, "署名検証: 実行中", "warn");
  try {
    const response = await fetch("/api/v1/ledger/verify", { method: "POST" });
    const data = await response.json();

    if (response.status === 200 && data.valid === true) {
      const sigOk = data.checks && data.checks.signature_valid === true ? "OK" : "NG";
      setResult(ledgerResult, "台帳検証成功: すべてのブロック整合性が有効です", "ok");
      setResult(ledgerSignatureResult, `署名検証: ${sigOk}`, sigOk === "OK" ? "ok" : "ng");
      return;
    }

    if (response.status === 409 && data.valid === false) {
      const index = data.error && data.error.index;
      const reason = data.error && data.error.reason;
      const sigValid = data.checks ? data.checks.signature_valid : null;
      const sigText = sigValid === true ? "OK" : "NG";
      setResult(ledgerResult, `台帳検証失敗: index=${index}, reason=${reason}`, "ng");
      setResult(ledgerSignatureResult, `署名検証: ${sigText}`, "ng");
      return;
    }

    setResult(ledgerResult, apiErrorMessage(data, "台帳検証に失敗しました"), "ng");
    setResult(ledgerSignatureResult, "署名検証: NG", "ng");
  } catch (_error) {
    setResult(ledgerResult, "台帳検証に失敗しました", "ng");
    setResult(ledgerSignatureResult, "署名検証: NG", "ng");
  } finally {
    clearBusy(verifyLedgerButton);
  }
});

loadAnchorButton.addEventListener("click", async () => {
  setBusy(loadAnchorButton, "取得中...");
  setResult(anchorResult, "アンカーを取得しています...", "warn");
  try {
    const response = await fetch("/api/v1/anchors/latest");
    const data = await response.json();

    if (response.status !== 200) {
      setResult(anchorResult, apiErrorMessage(data, "アンカー取得に失敗しました"), "ng");
      latestAnchor = null;
      setAnchorState(false);
      return;
    }

    latestAnchor = data;
    setAnchorState(true);
    setResult(
      anchorResult,
      `latest_index=${data.latest_index}\nblock_hash=${data.block_hash}\nsignature=${data.signature}`,
      "ok"
    );
  } catch (_error) {
    setResult(anchorResult, "アンカー取得に失敗しました", "ng");
    latestAnchor = null;
    setAnchorState(false);
  } finally {
    clearBusy(loadAnchorButton);
  }
});

copyAnchorHashButton.addEventListener("click", async () => {
  const ok = await copyText(latestAnchor && latestAnchor.block_hash);
  setResult(
    anchorResult,
    ok ? "block_hash をコピーしました" : "コピーに失敗しました（先にアンカー取得してください）",
    ok ? "ok" : "warn"
  );
});

copyAnchorSignatureButton.addEventListener("click", async () => {
  const ok = await copyText(latestAnchor && latestAnchor.signature);
  setResult(
    anchorResult,
    ok ? "signature をコピーしました" : "コピーに失敗しました（先にアンカー取得してください）",
    ok ? "ok" : "warn"
  );
});

async function init() {
  setAnchorState(false);
  await checkHealth();
  await loadRecords();
}

init();
