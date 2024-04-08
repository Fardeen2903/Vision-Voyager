// script.js
function startYoloDetection() {
    fetch('/start_yolov_detection')
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response from the server
            // Handle the response as needed (e.g., display a message to the user)
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle errors if any
        });
}
