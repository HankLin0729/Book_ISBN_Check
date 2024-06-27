const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const dataDiv = document.getElementById("data");
const debugDiv = document.getElementById("debug_info");
let intervalId;

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true }).then(function(stream) {
        video.srcObject = stream;
        video.play();
    });
}

function captureFrame() {
    context.drawImage(video, 0, 0, 640, 480);
    canvas.toBlob(function(blob) {
        const formData = new FormData();
        formData.append('file', blob, 'capture.png');
        fetch('/', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
          .then(data => showResult(data))
          .catch(error => console.error('Error:', error));
    });
}

intervalId = setInterval(captureFrame, 5000);

document.getElementById('upload_form').onsubmit = function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    fetch('/', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => showResult(data))
      .catch(error => console.error('Error:', error));
};

function showResult(result) {
    var debugInfos = result.debug_infos;
    var imagePaths = result.image_paths;
    debugDiv.innerHTML = "";
    dataDiv.innerHTML = "";

    for (var i = 0; i < debugInfos.length; i++) {
        var debugP = document.createElement("p");
        debugP.innerHTML = debugInfos[i];
        debugDiv.appendChild(debugP);

        if (imagePaths && imagePaths[i]) {
            var img = document.createElement("img");
            img.src = imagePaths[i].replace(/\\/g, '/');
            img.className = "thumbnail";
            dataDiv.appendChild(img);
        }
    }

    document.getElementById("continue_button").style.display = "block";
    clearInterval(intervalId);
}

function continueProcess() {
    document.getElementById("continue_button").style.display = "none";
    debugDiv.innerHTML = "";
    dataDiv.innerHTML = "";
    intervalId = setInterval(captureFrame, 5000);
}

function search(query) {
    var div = document.getElementById("data");
    div.innerHTML = 'Loading...';

    var jsonScript = document.getElementById("jsonScript");
    if (jsonScript) {
        jsonScript.parentNode.removeChild(jsonScript);
    }

    var scriptElement = document.createElement("script");
    scriptElement.setAttribute("id", "jsonScript");
    scriptElement.setAttribute("src",
        "https://books.google.com/books?bibkeys=" +
        escape(query.isbns.value) + "&jscmd=viewapi&callback=listEntries");
    scriptElement.setAttribute("type", "text/javascript");
    document.documentElement.firstChild.appendChild(scriptElement);
}

function listEntries(booksInfo) {
    var div = document.getElementById("data");
    div.innerHTML = ''; 

    var mainDiv = document.createElement("div");

    for (var i in booksInfo) {
        var book = booksInfo[i];
        var thumbnailDiv = document.createElement("div");
        thumbnailDiv.className = "thumbnail";

        var a = document.createElement("a");
        a.href = book.info_url;
        a.innerHTML = book.bib_key;

        var img = document.createElement("img");
        img.src = book.thumbnail_url;
        a.appendChild(img);

        thumbnailDiv.appendChild(a);

        var p = document.createElement("p");
        p.innerHTML = book.preview;
        if (p.innerHTML == "noview"){
            p.style.fontWeight = "bold";
            p.style.color = "#f00";
        }

        thumbnailDiv.appendChild(p);
        mainDiv.appendChild(thumbnailDiv);
    }
    div.appendChild(mainDiv);
}

document.addEventListener('mousemove', function(e) {
    const cursorCircle = document.querySelector('.cursor-circle');
    const cursorDot = document.querySelector('.cursor-dot');
    cursorCircle.style.left = e.pageX + 'px';
    cursorCircle.style.top = e.pageY + 'px';
    cursorDot.style.left = e.pageX + 'px';
    cursorDot.style.top = e.pageY + 'px';
});
