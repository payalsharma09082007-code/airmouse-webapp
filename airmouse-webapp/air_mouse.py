

import cv2
import mediapipe as mp
import pyautogui
import math
import threading
import time

# Screen settings
screen_width, screen_height = pyautogui.size()

# Shared application state
running = False
camera_connected = False
gesture_status = "Waiting..."
tracking_status = "Inactive"

latest_frame = None

state_lock = threading.Lock()
stop_event = threading.Event()
worker_thread = None


def get_status():
    with state_lock:
        return {
            "running": running,
            "camera": camera_connected,
            "gesture": gesture_status,
            "tracking": tracking_status
        }


def get_frame():
    with state_lock:
        return latest_frame


def start_air_mouse():
    global worker_thread, running

    if worker_thread and worker_thread.is_alive():
        return True

    stop_event.clear()

    with state_lock:
        running = True

    worker_thread = threading.Thread(
        target=air_mouse_worker,
        daemon=True
    )

    worker_thread.start()
    return True


def stop_air_mouse():
    global running, gesture_status, tracking_status

    stop_event.set()

    with state_lock:
        running = False
        gesture_status = "Stopped"
        tracking_status = "Inactive"


def air_mouse_worker():
    global running, camera_connected
    global gesture_status, tracking_status, latest_frame

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        with state_lock:
            camera_connected = False
            running = False
            gesture_status = "Camera unavailable"
        return

    with state_lock:
        camera_connected = True
        tracking_status = "Searching for hand"

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    prev_x = screen_width // 2
    prev_y = screen_height // 2

    smooth = 5

    # Click detection settings
    left_pinching = False
    right_pinching = False

    left_frames = 0
    right_frames = 0

    click_threshold = 0.05
    release_threshold = 0.07

    required_frames = 3

    # Scroll settings
    previous_scroll_y = None
    scroll_sensitivity = 500
    scroll_threshold = 0.008

    try:

        while not stop_event.is_set():

            success, frame = cap.read()

            if not success:
                break

            frame = cv2.flip(frame, 1)

            frame_height, frame_width = frame.shape[:2]

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = hands.process(rgb_frame)

            status = "Show your hand"

            if results.multi_hand_landmarks:

                hand_landmarks = results.multi_hand_landmarks[0]

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                # Finger landmarks
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                middle = hand_landmarks.landmark[12]

                index_pip = hand_landmarks.landmark[6]
                middle_pip = hand_landmarks.landmark[10]
                ring_pip = hand_landmarks.landmark[14]
                pinky_pip = hand_landmarks.landmark[18]

                ring = hand_landmarks.landmark[16]
                pinky = hand_landmarks.landmark[20]

                # Yellow dot on index fingertip
                index_px = int(index.x * frame_width)
                index_py = int(index.y * frame_height)

                cv2.circle(
                    frame,
                    (index_px, index_py),
                    10,
                    (0, 255, 255),
                    -1
                )

                cv2.circle(
                    frame,
                    (index_px, index_py),
                    13,
                    (0, 0, 0),
                    2
                )

                # Finger positions
                index_raised = index.y < index_pip.y
                middle_raised = middle.y < middle_pip.y
                ring_raised = ring.y < ring_pip.y
                pinky_raised = pinky.y < pinky_pip.y

                index_folded = index.y > index_pip.y
                middle_folded = middle.y > middle_pip.y
                ring_folded = ring.y > ring_pip.y
                pinky_folded = pinky.y > pinky_pip.y

                # Calculate pinch distances
                left_distance = math.hypot(
                    thumb.x - index.x,
                    thumb.y - index.y
                )

                right_distance = math.hypot(
                    thumb.x - middle.x,
                    thumb.y - middle.y
                )

                # Pause gesture
                fist_detected = (
                    index_folded
                    and middle_folded
                    and ring_folded
                    and pinky_folded
                )

                # Scroll gesture
                open_palm = (
                    index_raised
                    and middle_raised
                    and ring_raised
                    and pinky_raised
                    and left_distance > release_threshold
                    and right_distance > release_threshold
                )

                if fist_detected:

                    status = "PAUSED - Open hand to resume"

                    left_pinching = False
                    right_pinching = False

                    left_frames = 0
                    right_frames = 0

                    previous_scroll_y = None

                elif open_palm:

                    current_scroll_y = hand_landmarks.landmark[0].y

                    if previous_scroll_y is not None:

                        movement = (
                            previous_scroll_y - current_scroll_y
                        )

                        if abs(movement) > scroll_threshold:

                            scroll_amount = int(
                                movement * scroll_sensitivity
                            )

                            if scroll_amount:
                                pyautogui.scroll(scroll_amount)

                    previous_scroll_y = current_scroll_y

                    status = "SCROLL MODE"

                    left_pinching = False
                    right_pinching = False

                    left_frames = 0
                    right_frames = 0

                else:

                    previous_scroll_y = None

                    # Smooth mouse movement
                    target_x = int(index.x * screen_width)
                    target_y = int(index.y * screen_height)

                    current_x = (
                        prev_x + (target_x - prev_x) / smooth
                    )

                    current_y = (
                        prev_y + (target_y - prev_y) / smooth
                    )

                    current_x = max(
                        0,
                        min(screen_width - 1, current_x)
                    )

                    current_y = max(
                        0,
                        min(screen_height - 1, current_y)
                    )

                    pyautogui.moveTo(
                        int(current_x),
                        int(current_y)
                    )

                    prev_x = current_x
                    prev_y = current_y

                    # Identify left and right pinch separately
                    left_candidate = (
                        left_distance < click_threshold
                        and left_distance + 0.01 < right_distance
                    )

                    right_candidate = (
                        right_distance < click_threshold
                        and right_distance + 0.01 < left_distance
                    )

                    # Detect new pinch
                    if not left_pinching and not right_pinching:

                        if left_candidate:
                            left_frames += 1
                        else:
                            left_frames = 0

                        if right_candidate:
                            right_frames += 1
                        else:
                            right_frames = 0

                        # LEFT CLICK
                        if left_frames >= required_frames:

                            pyautogui.click()

                            left_pinching = True

                            left_frames = 0
                            right_frames = 0

                        # RIGHT CLICK
                        elif right_frames >= required_frames:

                            pyautogui.rightClick()

                            right_pinching = True

                            right_frames = 0
                            left_frames = 0

                    # Release detection
                    if (
                        left_pinching
                        and left_distance > release_threshold
                    ):
                        left_pinching = False

                    if (
                        right_pinching
                        and right_distance > release_threshold
                    ):
                        right_pinching = False

                    # Keep gesture name visible while holding pinch
                    if left_pinching:

                        status = "LEFT CLICK"

                    elif right_pinching:

                        status = "RIGHT CLICK"

                    else:

                        status = "MOUSE MOVING"

                with state_lock:
                    tracking_status = "Hand detected"
                    gesture_status = status

            else:

                left_pinching = False
                right_pinching = False

                left_frames = 0
                right_frames = 0

                previous_scroll_y = None

                status = "No Hand Detected"

                with state_lock:
                    tracking_status = "No hand detected"
                    gesture_status = status

            # Display gesture on camera
            cv2.putText(
                frame,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Convert camera frame to JPEG
            success, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            if success:

                with state_lock:
                    latest_frame = buffer.tobytes()

    except Exception as error:

        with state_lock:
            gesture_status = f"Error: {error}"

    finally:

        hands.close()
        cap.release()

        with state_lock:
            running = False
            camera_connected = False
            tracking_status = "Inactive"
