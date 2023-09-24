
let video = document.querySelector("#webcam");

if (navigator.mediaDevices.getUserMedia){
     // passing arguemnt as an object
     navigator.mediaDevices.getUserMedia({video : true})
     .then (function (stream) {
          // send data first
          video.srcObject = stream;
          console.log(stream);
     })
     // if sum go wrong
     .catch (function(error) {
          console.log("Something is up");
     })
}

else{
     console.log("getUserMedie does not support");
}

// Something is up with this part
// const socket = new WebSocket("wss://http://127.0.0.1:5501/version2/index.html#about");
// socket.addEventListener("message", function (event) {
//      const data = event.data;
//      console.log("Data received from backend:", data);
// });
