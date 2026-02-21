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

let latestAnchor = null;

function setText(el, text) {
  el.textContent = text;
}

function apiErrorMessage(json, fallback) {
  if (json && json.error && typeof json.error.message === "string") {
    return json.error.message;
  }
  return fallback;
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

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = document.getElementById("register-name").value;
  const version = document.getElementById("register-version").value;
  const fileInput = document.getElementById("register-file");
  const file = fileInput.files[0];

  if (!file) {
    setText(registerResult, "入力値が不正です");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("version", version);
  formData.append("file", file);

  try {
    const response = await fetch("/api/v1/records/register", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.status === 201) {
      setText(
        registerResult,
        `登録完了: ${data.name} ${data.version} / sha256=${data.sha256}`
      );
      return;
    }

    if (response.status === 409) {
      setText(registerResult, "同じ name/version は登録済みです");
      return;
    }

    if (response.status === 400) {
      setText(registerResult, "入力値が不正です");
      return;
    }

    setText(registerResult, apiErrorMessage(data, "登録処理に失敗しました"));
  } catch (_error) {
    setText(registerResult, "登録処理に失敗しました");
  }
});

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = document.getElementById("verify-name").value;
  const version = document.getElementById("verify-version").value;
  const fileInput = document.getElementById("verify-file");
  const file = fileInput.files[0];

  if (!file) {
    setText(verifyResult, "入力値が不正です");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("version", version);
  formData.append("file", file);

  try {
    const response = await fetch("/api/v1/records/verify", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.status === 200) {
      setText(
        verifyResult,
        `検証成功: 登録情報と一致しました（name=${data.name}, version=${data.version}, sha256=${data.sha256}）`
      );
      return;
    }

    if (response.status === 404) {
      setText(verifyResult, "一致する登録が見つかりません");
      return;
    }

    if (response.status === 400) {
      setText(verifyResult, "入力値が不正です");
      return;
    }

    setText(verifyResult, apiErrorMessage(data, "検証処理に失敗しました"));
  } catch (_error) {
    setText(verifyResult, "検証処理に失敗しました");
  }
});

reloadRecordsButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/v1/records");
    const data = await response.json();

    if (response.status !== 200) {
      setText(recordsResult, apiErrorMessage(data, "一覧取得に失敗しました"));
      return;
    }

    recordsTbody.innerHTML = "";
    for (const item of data.items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.index}</td>
        <td>${item.timestamp_utc}</td>
        <td>${item.name}</td>
        <td>${item.version}</td>
        <td>${item.sha256}</td>
        <td>${item.file_size_bytes}</td>
        <td>${item.original_filename}</td>
        <td>${item.signing_key_id ?? ""}</td>
      `;
      recordsTbody.appendChild(tr);
    }
    setText(recordsResult, `件数: ${data.count}`);
  } catch (_error) {
    setText(recordsResult, "一覧取得に失敗しました");
  }
});

verifyLedgerButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/v1/ledger/verify", { method: "POST" });
    const data = await response.json();

    if (response.status === 200 && data.valid === true) {
      setText(ledgerResult, "台帳検証成功: すべてのブロック整合性と署名が有効です");
      const sigOk = data.checks && data.checks.signature_valid === true ? "OK" : "NG";
      setText(ledgerSignatureResult, `署名検証: ${sigOk}`);
      return;
    }

    if (response.status === 409 && data.valid === false) {
      const index = data.error && data.error.index;
      const reason = data.error && data.error.reason;
      const sigValid = data.checks ? data.checks.signature_valid : null;
      const sigText = sigValid === true ? "OK" : "NG";
      setText(ledgerResult, `台帳検証失敗: index=${index} のブロックが不正です（reason=${reason}）`);
      setText(ledgerSignatureResult, `署名検証: ${sigText}`);
      return;
    }

    setText(ledgerResult, apiErrorMessage(data, "台帳検証に失敗しました"));
    setText(ledgerSignatureResult, "署名検証: NG");
  } catch (_error) {
    setText(ledgerResult, "台帳検証に失敗しました");
    setText(ledgerSignatureResult, "署名検証: NG");
  }
});

loadAnchorButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/v1/anchors/latest");
    const data = await response.json();

    if (response.status !== 200) {
      setText(anchorResult, apiErrorMessage(data, "アンカー取得に失敗しました"));
      latestAnchor = null;
      return;
    }

    latestAnchor = data;
    setText(
      anchorResult,
      `latest_index=${data.latest_index}\nblock_hash=${data.block_hash}\nsignature=${data.signature}`
    );
  } catch (_error) {
    setText(anchorResult, "アンカー取得に失敗しました");
    latestAnchor = null;
  }
});

copyAnchorHashButton.addEventListener("click", async () => {
  const ok = await copyText(latestAnchor && latestAnchor.block_hash);
  setText(anchorResult, ok ? "block_hash をコピーしました" : "コピーに失敗しました（先にアンカー取得してください）");
});

copyAnchorSignatureButton.addEventListener("click", async () => {
  const ok = await copyText(latestAnchor && latestAnchor.signature);
  setText(anchorResult, ok ? "signature をコピーしました" : "コピーに失敗しました（先にアンカー取得してください）");
});
