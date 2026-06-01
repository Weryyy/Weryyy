(function () {
  "use strict";

  console.log("stimation-tool.js loaded - version stimation-v01");

  var CONFIG = {
    apiUrl: "https://backend-placeholder.example.com/api/stimation/estimate"
  };

  var root = document.getElementById("stimation-tool-app");

  if (!root) {
    console.error("stimation-tool-app not found");
    return;
  }

  function expandModernWebPartCanvas() {
    var current = root.parentElement;
    var levels = 0;

    while (current && levels < 12) {
      current.classList.add("stimation-fullbleed-parent");
      current = current.parentElement;
      levels++;
    }

    document.documentElement.classList.add("stimation-page-loaded");
  }

  expandModernWebPartCanvas();

  var $mode = root.querySelector("#stimation-mode");
  var $file = root.querySelector("#stimation-file");
  var $includeAudit = root.querySelector("#stimation-include-audit");
  var $run = root.querySelector("#stimation-run");
  var $status = root.querySelector("#stimation-status");
  var $error = root.querySelector("#stimation-error");
  var $resultCard = root.querySelector("#stimation-result-card");
  var $download = root.querySelector("#stimation-download");

  var lastResultBlob = null;
  var lastResultFileName = "stimation-result.xlsx";

  function setStatus(message) {
    $status.textContent = message;
  }

  function showError(message) {
    $error.textContent = message;
    $error.hidden = false;
  }

  function clearError() {
    $error.textContent = "";
    $error.hidden = true;
  }

  function resetResult() {
    lastResultBlob = null;
    lastResultFileName = "stimation-result.xlsx";
    $resultCard.hidden = true;
  }

  function getFileNameFromContentDisposition(headerValue) {
    if (!headerValue) {
      return "";
    }

    var match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);

    if (match && match[1]) {
      return decodeURIComponent(match[1]);
    }

    match = headerValue.match(/filename="?([^"]+)"?/i);

    return match && match[1] ? match[1] : "";
  }

  async function runEstimation() {
    clearError();
    resetResult();

    var file = $file.files && $file.files[0];

    if (!file) {
      showError("Please select an Excel file before running the estimation.");
      return;
    }

    if (!/\.xlsx$/i.test(file.name)) {
      showError("Only .xlsx files are supported.");
      return;
    }

    var formData = new FormData();

    formData.append("mode", $mode.value);
    formData.append("includeAudit", $includeAudit.checked ? "true" : "false");
    formData.append("file", file, file.name);

    $run.disabled = true;
    setStatus("Uploading and processing file…");

    try {
      var response = await fetch(CONFIG.apiUrl, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        var errorText = await response.text();

        try {
          var errorJson = JSON.parse(errorText);
          throw new Error(errorJson.error || errorJson.details || errorText);
        } catch (parseError) {
          throw new Error(errorText || "Backend request failed: " + response.status);
        }
      }

      var blob = await response.blob();
      var disposition = response.headers.get("Content-Disposition");
      var fileName = getFileNameFromContentDisposition(disposition);

      lastResultBlob = blob;
      lastResultFileName =
        fileName ||
        "stimation-result-" + new Date().toISOString().slice(0, 10) + ".xlsx";

      setStatus("Estimation completed successfully.");
      $resultCard.hidden = false;
    } catch (error) {
      console.error("Estimation failed:", error);
      setStatus("Estimation failed.");
      showError(error.message || "Unexpected error.");
    } finally {
      $run.disabled = false;
    }
  }

  function downloadResult() {
    if (!lastResultBlob) {
      showError("No generated Excel file is available yet.");
      return;
    }

    var url = URL.createObjectURL(lastResultBlob);
    var link = document.createElement("a");

    link.href = url;
    link.download = lastResultFileName;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  $run.addEventListener("click", runEstimation);
  $download.addEventListener("click", downloadResult);
})();
