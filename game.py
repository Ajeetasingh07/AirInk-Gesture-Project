import cv2 as cv
import numpy as np
import HandDetectionModule as htm
import time

cap = cv.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = htm.handDetector(detectionCon=0.8)

W, H = 1280, 720
lanes = [W//4, W//2, 3*W//4]

# ---------- GAME STATE ----------
game_state = "menu"   # menu, play, pause, over

lane_index = 1
player_y = 550
player_h = 60

jump = False
jump_count = 10
slide = False

obs_x, obs_y = lanes[1], -100
coin_x, coin_y = lanes[0], -300

speed = 10
score = 0
lives = 3
shield = False
shield_time = 0

bg_offset = 0

while True:
    success, frame = cap.read()
    if not success:
        continue

    frame = cv.flip(frame, 1)

    frame = detector.findHands(frame)
    lmList = detector.findPosition(frame, draw=False)

    key = cv.waitKey(1) & 0xFF

    # ---------- MENU ----------
    if game_state == "menu":
        cv.putText(frame, "TEMPLE RUN AI", (350, 300),
                   cv.FONT_HERSHEY_SIMPLEX, 2, (0,255,255), 4)
        cv.putText(frame, "Press S to Start", (420, 400),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        if key == ord('s'):
            game_state = "play"

    # ---------- PLAY ----------
    elif game_state == "play":

        if key == ord('p'):
            game_state = "pause"

        if len(lmList) != 0:
            fingers = detector.fingersUp()

            if fingers[1] == 1 and fingers[2] == 0:
                lane_index = max(0, lane_index - 1)

            elif fingers[1] == 1 and fingers[2] == 1:
                lane_index = min(2, lane_index + 1)

            if sum(fingers) == 5:
                jump = True

            if sum(fingers) == 0:
                slide = True
            else:
                slide = False

        player_x = lanes[lane_index]

        # Jump
        if jump:
            if jump_count >= -10:
                neg = 1 if jump_count >= 0 else -1
                player_y -= (jump_count ** 2) * 0.25 * neg
                jump_count -= 1
            else:
                jump = False
                jump_count = 10
        else:
            player_y = 550

        # Slide
        player_h = 40 if slide else 60

        # Background scroll
        bg_offset += speed
        for i in range(0, H, 40):
            y = (i + bg_offset) % H
            cv.line(frame, (0, y), (W, y), (40,40,40), 1)

        # Draw player
        color = (0,255,0) if not shield else (255,255,0)
        cv.rectangle(frame, (player_x-30, int(player_y)),
                     (player_x+30, int(player_y+player_h)),
                     color, -1)

        # Obstacle
        obs_y += speed
        if obs_y > H:
            obs_y = -100
            obs_x = lanes[np.random.randint(0,3)]
            score += 1
            speed += 0.2

        cv.rectangle(frame, (obs_x-30, obs_y),
                     (obs_x+30, obs_y+60),
                     (0,0,255), -1)

        # Coin
        coin_y += speed
        if coin_y > H:
            coin_y = -300
            coin_x = lanes[np.random.randint(0,3)]

        cv.circle(frame, (coin_x, coin_y), 15, (0,255,255), -1)

        # Coin collect
        if abs(player_x - coin_x) < 40 and player_y < coin_y+20:
            score += 5
            coin_y = -300

        # Shield power-up
        if score > 0 and score % 20 == 0:
            shield = True
            shield_time = time.time()

        if shield and time.time() - shield_time > 5:
            shield = False

        # Collision
        if (abs(player_x - obs_x) < 50 and player_y < obs_y+60):
            if not shield:
                lives -= 1
                obs_y = -100

        if lives <= 0:
            game_state = "over"

        # UI
        cv.putText(frame, f"Score: {score}", (20,50),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv.putText(frame, f"Lives: {lives}", (20,90),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    # ---------- PAUSE ----------
    elif game_state == "pause":
        cv.putText(frame, "PAUSED", (500,350),
                   cv.FONT_HERSHEY_SIMPLEX, 2, (255,255,0), 4)
        if key == ord('r'):
            game_state = "play"

    # ---------- GAME OVER ----------
    elif game_state == "over":
        cv.putText(frame, "GAME OVER", (400,300),
                   cv.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 5)
        cv.putText(frame, "Press S to Restart", (400,400),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        if key == ord('s'):
            score = 0
            lives = 3
            speed = 10
            game_state = "play"

    cv.imshow("Temple Run AI", frame)

    if key == ord('q'):
        break

cap.release()
cv.destroyAllWindows()