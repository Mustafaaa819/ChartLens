/* ChartLens upload UI — vanilla JS, no external dependencies */
(function () {
  "use strict";

  var MAX_BYTES = 50 * 1024 * 1024; // 50 MB

  // ── DOM refs ──────────────────────────────────────────────────────────────

  var dropZone       = document.getElementById("drop-zone");
  var fileInput      = document.getElementById("file-input");
  var clearBtn       = document.getElementById("clear-file");
  var uploadForm     = document.getElementById("upload-form");
  var submitBtn      = document.getElementById("submit-btn");
  var progressSec    = document.getElementById("progress-section");
  var progressBar    = document.getElementById("progress-bar");
  var progressLabel  = document.getElementById("progress-label");
  var progressPct    = document.getElementById("progress-pct");
  var stepUploading  = document.getElementById("step-uploading");
  var stepProcessing = document.getElementById("step-processing");
  var jsError        = document.getElementById("js-error");
  var jsErrorText    = document.getElementById("js-error-text");
  var filePreview    = document.getElementById("file-preview");
  var dropHint       = document.getElementById("drop-hint");
  var fileName       = document.getElementById("file-name");
  var fileMeta       = document.getElementById("file-meta");

  // ── Drag-and-drop ─────────────────────────────────────────────────────────

  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add("border-[#2563eb]", "bg-blue-50");
  });

  dropZone.addEventListener("dragleave", function (e) {
    e.stopPropagation();
    // only remove highlight when leaving the zone entirely, not a child element
    if (!dropZone.contains(e.relatedTarget)) {
      dropZone.classList.remove("border-[#2563eb]", "bg-blue-50");
    }
  });

  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("border-[#2563eb]", "bg-blue-50");

    var file = e.dataTransfer.files[0];
    if (!file) return;

    if (!isPdf(file)) {
      alert("Please upload a PDF file only");
      return;
    }

    applyFile(file);
  });

  // Clicking the zone (or anything that isn't the clear button) opens the picker
  dropZone.addEventListener("click", function (e) {
    if (e.target === clearBtn || clearBtn.contains(e.target)) return;
    fileInput.click();
  });

  // ── File input change ──────────────────────────────────────────────────────

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
      applyFile(fileInput.files[0]);
    }
  });

  // ── Clear button ───────────────────────────────────────────────────────────

  clearBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    fileInput.value = "";
    hidePreview();
    clearError();
  });

  // ── File helpers ───────────────────────────────────────────────────────────

  function isPdf(file) {
    return (
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf")
    );
  }

  function applyFile(file) {
    clearError();

    if (file.size > MAX_BYTES) {
      showError("File exceeds 50MB upload limit. Please use a smaller PDF.");
      fileInput.value = "";
      hidePreview();
      return;
    }

    // When the file came from drag-and-drop, transfer it to the real input
    if (fileInput.files.length === 0 || fileInput.files[0] !== file) {
      try {
        var dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
      } catch (_) {
        // DataTransfer not supported in very old browsers — upload will still
        // work if the user chose the file via the native picker
      }
    }

    var estimatedPages = Math.ceil(file.size / 3072);
    fileName.textContent = file.name;
    fileMeta.textContent = "~" + estimatedPages + " pages estimated";

    dropHint.classList.add("hidden");
    filePreview.classList.remove("hidden");
  }

  function hidePreview() {
    filePreview.classList.add("hidden");
    dropHint.classList.remove("hidden");
    fileName.textContent = "";
    fileMeta.textContent = "";
  }

  // ── Error banner ───────────────────────────────────────────────────────────

  function showError(msg) {
    jsErrorText.textContent = msg;
    jsError.classList.remove("hidden");
    jsError.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function clearError() {
    jsError.classList.add("hidden");
    jsErrorText.textContent = "";
  }

  // ── Progress bar ───────────────────────────────────────────────────────────

  function setProgress(pct, label) {
    progressBar.style.width = pct + "%";
    progressPct.textContent = pct + "%";
    progressLabel.textContent = label;
  }

  function activateStep(step) {
    step.classList.remove("text-gray-400");
    step.classList.add("text-gray-700", "font-medium");
  }

  // ── Form submission ────────────────────────────────────────────────────────

  uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();
    clearError();

    var clientName = document.getElementById("client_name").value.trim();
    if (!clientName) {
      showError("Client name is required.");
      return;
    }

    if (!fileInput.files || fileInput.files.length === 0) {
      showError("Please select a PDF file to upload.");
      return;
    }

    startUpload();
  });

  function startUpload() {
    // Switch view: hide form, show progress
    uploadForm.classList.add("hidden");
    progressSec.classList.remove("hidden");
    submitBtn.disabled = true;
    setProgress(0, "Uploading...");
    activateStep(stepUploading);

    // Simulate progress 0 → 90 % while the network request is in flight
    var pct = 0;
    var ticker = setInterval(function () {
      pct = Math.min(pct + 4, 90);
      setProgress(pct, "Uploading...");
    }, 180);

    var formData = new FormData(uploadForm);

    fetch("/cases/upload", { method: "POST", body: formData })
      .then(function (response) {
        clearInterval(ticker);

        // Case A: server issued a redirect (after Prompt #19 wires the pipeline)
        if (response.redirected) {
          activateStep(stepProcessing);
          setProgress(100, "Complete! Redirecting...");
          setTimeout(function () {
            window.location.href = response.url;
          }, 600);
          return;
        }

        // Case B: successful JSON response (current behaviour)
        if (response.ok) {
          return response.json().then(function (data) {
            setProgress(90, "Uploading...");
            activateStep(stepProcessing);
            setProgress(95, "Processing with AI...");

            setTimeout(function () {
              setProgress(100, "Complete! Redirecting...");
              setTimeout(function () {
                if (data.case_id) {
                  window.location.href = "/cases/" + data.case_id;
                } else {
                  window.location.href = "/dashboard";
                }
              }, 500);
            }, 800);
          });
        }

        // Case C: server returned an error
        return response.json().then(function (errData) {
          var msg = (errData && errData.detail)
            ? errData.detail
            : "Upload failed. Please try again.";
          restoreForm(msg);
        }).catch(function () {
          restoreForm("Upload failed (HTTP " + response.status + "). Please try again.");
        });
      })
      .catch(function () {
        clearInterval(ticker);
        restoreForm("Network error — please check your connection and try again.");
      });
  }

  function restoreForm(errorMsg) {
    progressSec.classList.add("hidden");
    uploadForm.classList.remove("hidden");
    submitBtn.disabled = false;
    setProgress(0, "Uploading...");
    // reset step indicators
    stepProcessing.classList.remove("text-gray-700", "font-medium");
    stepProcessing.classList.add("text-gray-400");
    stepUploading.classList.remove("font-medium");
    showError(errorMsg);
  }

})();
