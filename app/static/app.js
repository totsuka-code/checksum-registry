const registerForm = document.getElementById("register-form");
const registerResult = document.getElementById("register-result");

const verifyForm = document.getElementById("verify-form");
const verifyResult = document.getElementById("verify-result");

const reloadRecordsButton = document.getElementById("reload-records");
const recordsResult = document.getElementById("records-result");
const recordsTbody = document.getElementById("records-tbody");

const verifyLedgerButton = document.getElementById("verify-ledger");
const ledgerResult = document.getElementById("ledger-result");

function setText(el, text) {
  el.textContent = text;
}

function apiErrorMessage(json, fallback) {
  if (json && json.error && typeof json.error.message === "string") {
    return json.error.message;
  }
  return fallback;
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
  } catch (error) {
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
  } catch (error) {
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
      `;
      recordsTbody.appendChild(tr);
    }
    setText(recordsResult, `件数: ${data.count}`);
  } catch (error) {
    setText(recordsResult, "一覧取得に失敗しました");
  }
});

verifyLedgerButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/v1/ledger/verify", { method: "POST" });
    const data = await response.json();

    if (response.status === 200 && data.valid === true) {
      setText(ledgerResult, "台帳検証成功: すべてのブロック整合性が有効です");
      return;
    }

    if (response.status === 409 && data.valid === false) {
      const index = data.error && data.error.index;
      const reason = data.error && data.error.reason;
      setText(ledgerResult, `台帳検証失敗: index=${index} のブロックが不正です（reason=${reason}）`);
      return;
    }

    setText(ledgerResult, apiErrorMessage(data, "台帳検証に失敗しました"));
  } catch (error) {
    setText(ledgerResult, "台帳検証に失敗しました");
  }
});
