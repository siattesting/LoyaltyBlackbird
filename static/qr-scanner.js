// QR Code Scanner functionality
class QRScanner {
  constructor() {
    this.stream = null;
    this.video = null;
    this.canvas = null;
    this.context = null;
    this.isScanning = false;
  }

  async startScanner(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.context = this.canvas.getContext('2d');

    try {
      // Get camera stream
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // Use rear camera on mobile
      });

      this.video.srcObject = this.stream;
      this.video.play();
      this.isScanning = true;

      // Start scanning loop
      this.scanFrame();

    } catch (error) {
      console.error('Error accessing camera:', error);
      throw new Error('Camera access denied or not available');
    }
  }

  scanFrame() {
    if (!this.isScanning) return;

    if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
      // Set canvas size to video size
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;

      // Draw video frame to canvas
      this.context.drawImage(this.video, 0, 0);

      // Get image data
      const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);

      // Try to decode QR code (simplified implementation)
      const qrData = this.decodeQR(imageData);
      
      if (qrData) {
        this.onQRDetected(qrData);
        return;
      }
    }

    // Continue scanning
    requestAnimationFrame(() => this.scanFrame());
  }

  decodeQR(imageData) {
    // Simplified QR detection - in production, use a proper QR library like jsQR
    // This is a placeholder that would need a real QR decoding library
    
    // For demo purposes, we'll simulate QR detection
    // In reality, you would use: https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js
    
    try {
      // Placeholder for QR decoding logic
      // const code = jsQR(imageData.data, imageData.width, imageData.height);
      // if (code) return code.data;
      
      return null; // No QR code detected
    } catch (error) {
      console.error('QR decode error:', error);
      return null;
    }
  }

  onQRDetected(qrData) {
    console.log('QR Code detected:', qrData);
    
    // Send QR data to server
    fetch('/transactions/scan_qr', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ qr_data: qrData })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showAlert(data.message, 'success');
      } else {
        showAlert(data.message, 'error');
      }
    })
    .catch(error => {
      console.error('Error processing QR code:', error);
      showAlert('Error processing QR code', 'error');
    });

    // Stop scanning
    this.stopScanner();
  }

  stopScanner() {
    this.isScanning = false;
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.video) {
      this.video.srcObject = null;
    }
  }
}

// Initialize QR scanner when needed
let qrScanner = null;

function initQRScanner() {
  if (!qrScanner) {
    qrScanner = new QRScanner();
  }
  return qrScanner;
}

// QR Scanner modal functionality
document.addEventListener('DOMContentLoaded', function() {
  const qrScanButton = document.getElementById('qr-scan-button');
  const qrModal = document.getElementById('qr-modal');
  const qrVideo = document.getElementById('qr-video');
  const qrCanvas = document.getElementById('qr-canvas');
  const closeQRModal = document.getElementById('close-qr-modal');

  if (qrScanButton && qrModal) {
    qrScanButton.addEventListener('click', async function() {
      try {
        const scanner = initQRScanner();
        qrModal.style.display = 'block';
        await scanner.startScanner(qrVideo, qrCanvas);
      } catch (error) {
        showAlert('Error starting camera: ' + error.message, 'error');
        qrModal.style.display = 'none';
      }
    });

    if (closeQRModal) {
      closeQRModal.addEventListener('click', function() {
        if (qrScanner) {
          qrScanner.stopScanner();
        }
        qrModal.style.display = 'none';
      });
    }
  }
});

// Utility function for alerts (if not already defined)
if (typeof showAlert === 'undefined') {
  function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
      alertDiv.remove();
    }, 5000);
  }
}
