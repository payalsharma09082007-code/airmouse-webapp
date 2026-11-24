

from flask import Flask, render_template, jsonify, Response, stream_with_context
import time

import air_mouse

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    success = air_mouse.start_air_mouse()

    return jsonify({
        "success": success,
        "message": "Air Mouse started"
    })


@app.route("/stop", methods=["POST"])
def stop():
    air_mouse.stop_air_mouse()

    return jsonify({
        "success": True,
        "message": "Air Mouse stopped"
    })


@app.route("/status")
def status():
    return jsonify(air_mouse.get_status())


@app.route("/video_feed")
def video_feed():

    @stream_with_context
    def generate():
        while True:
            frame = air_mouse.get_frame()

            if frame is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.03)

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(debug=True, threaded=True, use_reloader=False)
