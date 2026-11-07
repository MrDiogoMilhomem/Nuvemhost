const uploadArea = document.getElementById("uploadArea")
const fileInput = document.getElementById("project_file")
const fileInfo = document.getElementById("fileInfo")
const fileName = document.getElementById("fileName")
const fileSize = document.getElementById("fileSize")
const uploadForm = document.getElementById("uploadForm")
const submitBtn = document.getElementById("submitBtn")
const uploadProgress = document.getElementById("uploadProgress")
const bootstrap = window.bootstrap // Declare the bootstrap variable

function showAlert(message, type) {
  // Remove existing alerts
  const existingAlerts = document.querySelectorAll(".alert")
  existingAlerts.forEach((alert) => alert.remove())

  // Create new alert
  const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="bi bi-${type === "success" ? "check-circle" : "exclamation-triangle"} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `

  // Insert alert at the top of the container
  const container = document.querySelector(".upload-container")
  container.insertAdjacentHTML("afterbegin", alertHTML)

  // Auto-hide after 5 seconds
  setTimeout(() => {
    const alert = container.querySelector(".alert")
    if (alert) {
      const bsAlert = new bootstrap.Alert(alert)
      bsAlert.close()
    }
  }, 5000)
}

// Drag and drop functionality
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault()
  uploadArea.classList.add("dragover")
})

uploadArea.addEventListener("dragleave", (e) => {
  e.preventDefault()
  if (!uploadArea.contains(e.relatedTarget)) {
    uploadArea.classList.remove("dragover")
  }
})

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault()
  uploadArea.classList.remove("dragover")

  const files = e.dataTransfer.files
  if (files.length > 0) {
    fileInput.files = files
    handleFileSelect()
  }
})

fileInput.addEventListener("change", handleFileSelect)

function handleFileSelect() {
  const file = fileInput.files[0]
  if (file) {
    // Validate file type
    if (!file.name.toLowerCase().endsWith(".zip")) {
      showAlert("Please select a ZIP file.", "danger")
      resetFileInput()
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      showAlert("File size must be less than 10MB.", "danger")
      resetFileInput()
      return
    }

    // Update UI
    fileName.textContent = file.name
    fileSize.textContent = formatFileSize(file.size)
    fileInfo.style.display = "block"

    // Hide upload zone and show file info
    uploadArea.style.display = "none"
  }
}

function removeFile() {
  resetFileInput()
}

function resetFileInput() {
  fileInput.value = ""
  fileInfo.style.display = "none"
  uploadArea.style.display = "block"
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// Form submission with progress
uploadForm.addEventListener("submit", (e) => {
  e.preventDefault()

  if (!fileInput.files[0]) {
    showAlert("Please select a file to upload.", "danger")
    return
  }

  const formData = new FormData(uploadForm)

  // Update UI
  submitBtn.disabled = true
  submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Uploading...'
  uploadProgress.style.display = "block"

  const xhr = new XMLHttpRequest()

  // Upload progress
  xhr.upload.addEventListener("progress", (e) => {
    if (e.lengthComputable) {
      const percentComplete = Math.round((e.loaded / e.total) * 100)
      const progressBar = uploadProgress.querySelector(".progress-bar")
      const progressPercentage = uploadProgress.querySelector(".progress-percentage")

      progressBar.style.width = percentComplete + "%"
      progressPercentage.textContent = percentComplete + "%"
    }
  })

  // Upload complete
  xhr.addEventListener("load", () => {
    if (xhr.status === 200) {
      // Success - redirect will happen automatically
      showAlert("Project uploaded successfully! Redirecting...", "success")
      setTimeout(() => {
        window.location.href = "/dashboard"
      }, 1500)
    } else {
      showAlert("Upload failed. Please try again.", "danger")
      resetForm()
    }
  })

  // Upload error
  xhr.addEventListener("error", () => {
    showAlert("Upload failed. Please check your connection and try again.", "danger")
    resetForm()
  })

  // Upload timeout
  xhr.addEventListener("timeout", () => {
    showAlert("Upload timed out. Please try again.", "danger")
    resetForm()
  })

  xhr.timeout = 60000 // 60 seconds timeout
  xhr.open("POST", "/upload")
  xhr.send(formData)
})

function resetForm() {
  submitBtn.disabled = false
  submitBtn.innerHTML = '<i class="bi bi-rocket-takeoff me-2"></i>Upload & Deploy'
  uploadProgress.style.display = "none"
  uploadProgress.querySelector(".progress-bar").style.width = "0%"
  uploadProgress.querySelector(".progress-percentage").textContent = "0%"
}

// Add animation on page load
document.addEventListener("DOMContentLoaded", () => {
  const uploadContainer = document.querySelector(".upload-container")
  if (uploadContainer) {
    uploadContainer.classList.add("fade-in-up")
  }
})

// Confirm delete function
function confirmDelete(projectId) {
  const confirmation = confirm("Are you sure you want to delete this project? This action cannot be undone.")
  if (confirmation) {
    window.location.href = `delete_project/${projectId}`
  }
}

// Copy URL to clipboard
function copyUrl(url) {
  navigator.clipboard.writeText(window.location.origin + url).then(() => {
    showAlert('URL copied to clipboard!', 'success')
  }).catch(() => {
    showAlert('Failed to copy URL', 'danger')
  })
}

// Toggle project status (pause/reactivate)
function toggleProjectStatus(projectId, currentStatus) {
  console.log('toggleProjectStatus called:', projectId, currentStatus)
  const action = currentStatus === 'active' ? 'pause' : 'reactivate'
  const confirmation = confirm(`Are you sure you want to ${action} this project?`)
  if (!confirmation) return

  console.log('Sending POST to:', `/toggle_project_status/${projectId}`)
  
  fetch(`/toggle_project_status/${projectId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      console.log('Response status:', response.status)
      return response.json()
    })
    .then(data => {
      console.log('Response data:', data)
      location.reload()
      showAlert(data.message, 'success')
    })
    .catch(error => {
      console.error('Error:', error)
      showAlert('An error occurred. Please try again.', 'danger')
    })
}