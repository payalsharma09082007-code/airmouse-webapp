

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const liveBtn = document.getElementById("liveBtn");

const mouseStatus = document.getElementById("mouseStatus");
const cameraStatus = document.getElementById("cameraStatus");
const gestureStatus = document.getElementById("gestureStatus");

const cameraScreen = document.getElementById("cameraScreen");

const detectedGesture = document.getElementById("detectedGesture");
const trackingStatus = document.getElementById("trackingStatus");

let statusTimer = null;
let cameraStarted = false;

// Start Air Mouse
startBtn.addEventListener("click", async () => {
    try {
        startBtn.disabled = true;
        mouseStatus.textContent = "Starting...";

        const response = await fetch("/start", {
            method: "POST"
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Could not start Air Mouse");
        }

        mouseStatus.textContent = "Starting";
        cameraStatus.textContent = "Connecting...";
        gestureStatus.textContent = "Searching...";

        // Display live webcam
        if (!cameraStarted) {
            cameraScreen.innerHTML = "";

            const video = document.createElement("img");
            video.id = "cameraFeed";
            video.alt = "Live webcam feed";
            video.src = "/video_feed";

            video.style.width = "100%";
            video.style.height = "100%";
            video.style.objectFit = "contain";

            cameraScreen.appendChild(video);
            cameraStarted = true;
        }

        // Update dashboard every 250 milliseconds
        if (!statusTimer) {
            statusTimer = setInterval(updateStatus, 250);
        }

        updateStatus();

    } catch (error) {
        mouseStatus.textContent = "Error";
        cameraStatus.textContent = "Not Connected";
        gestureStatus.textContent = "Inactive";
        alert(error.message);

    } finally {
        startBtn.disabled = false;
    }
});


// Stop Air Mouse
stopBtn.addEventListener("click", async () => {
    try {
        stopBtn.disabled = true;

        const response = await fetch("/stop", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Could not stop Air Mouse");
        }

        if (statusTimer) {
            clearInterval(statusTimer);
            statusTimer = null;
        }

        const video = document.getElementById("cameraFeed");

        if (video) {
            video.remove();
        }

        cameraStarted = false;

        cameraScreen.innerHTML =
            '<p id="cameraMessage">📷 Camera preview will appear here</p>';

        mouseStatus.textContent = "Stopped";
        cameraStatus.textContent = "Not Connected";
        gestureStatus.textContent = "Inactive";
        detectedGesture.textContent = "Waiting...";
        trackingStatus.textContent = "Inactive";

    } catch (error) {
        alert(error.message);

    } finally {
        stopBtn.disabled = false;
    }
});


// Update dashboard information
async function updateStatus() {
    try {
        const response = await fetch("/status", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Status request failed");
        }

        const data = await response.json();

        mouseStatus.textContent =
            data.running ? "Running" : "Stopped";

        cameraStatus.textContent =
            data.camera ? "Connected" : "Not Connected";

        gestureStatus.textContent =
            data.running ? "Active" : "Inactive";

        // Show current detected gesture
        detectedGesture.textContent =
            data.gesture || "Waiting...";

        trackingStatus.textContent =
            data.tracking || "Searching for hand";

        // Stop polling if application stops
        if (!data.running && !data.camera) {
            if (statusTimer) {
                clearInterval(statusTimer);
                statusTimer = null;
            }
        }

    } catch (error) {
        console.error("Status update failed:", error);
    }
}


// Live Detection button
liveBtn.addEventListener("click", () => {
    const liveSection = document.getElementById("live");

    if (liveSection) {
        liveSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }
});
