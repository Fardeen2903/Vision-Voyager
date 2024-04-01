document.getElementById('startCameraButton').addEventListener('click', function() {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(function(stream) {
        var video = document.createElement('video');
        video.setAttribute('autoplay', '');
        video.setAttribute('playsinline', '');
        video.srcObject = stream;
        document.getElementById('cameraContainer').appendChild(video);
      })
      .catch(function(error) {
        console.error('Error accessing the camera: ', error);
        alert('Error accessing the camera. Please make sure it is enabled.');
      });
  } else {
    alert('getUserMedia is not supported by your browser. Please try a different browser.');
  }
});
// Get the modal element
var modal = document.getElementById("cookieModal");

// Get the button that opens the modal
var btn = document.getElementById("startCameraButton");

// When the user clicks the button, open the modal
btn.onclick = function() {
  modal.style.display = "block";
}

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

// Add event listener to the "Understood" button inside the modal
document.getElementById("cookieAcceptButton").addEventListener("click", function() {
  // Hide the modal
  modal.style.display = "none";

  // Check if the browser supports getUserMedia
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(function(stream) {
        var video = document.createElement('video');
        video.setAttribute('autoplay', '');
        video.setAttribute('playsinline', '');
        video.srcObject = stream;
        document.getElementById('cameraContainer').appendChild(video);
      })
      .catch(function(error) {
        console.error('Error accessing the camera: ', error);
        alert('Error accessing the camera. Please make sure it is enabled.');
      });
  } else {
    alert('getUserMedia is not supported by your browser. Please try a different browser.');
  }
});

// Add event listener to the "Cancel" button inside the modal
document.getElementById("cancelButton").addEventListener("click", function() {
  // Hide the modal
  modal.style.display = "none";
});
