import cv2
import pygame
from cvzone.HandTrackingModule import HandDetector
import random
import math

pygame.init()

clock = pygame.time.Clock()
fps = 60

# Get the display size
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Create a full screen display
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

cv2.namedWindow("Webcam", cv2.WINDOW_AUTOSIZE)
cap = cv2.VideoCapture(0)
cap.set(3, screen_width)
cap.set(4, screen_height)

pygame.display.set_caption('Flappy Bird')

# define font
font = pygame.font.SysFont('Bauhaus 93', 60)

# define colours
white = (255, 255, 255)

# define game variables
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
circle_frequency = 1500  # milliseconds
last_circle = pygame.time.get_ticks() - circle_frequency
score = 0

# load images and scale them to screen size
bg = pygame.image.load('img/bg.png')
bg = pygame.transform.scale(bg, (screen_width, screen_height))
ground_img = pygame.image.load('img/ground.png')
ground_img = pygame.transform.scale(ground_img, (screen_width, int(screen_height * 0.1)))
button_img = pygame.image.load('img/restart.png')
button_img = pygame.transform.scale(button_img, (100, 50))

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def reset_game():
    global score
    circle_group.empty()
    flappy.rect.x = 100
    flappy.rect.y = int(screen_height / 2)
    score = 0
    return score

class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f'img/bird{num}.png')
            img = pygame.transform.scale(img, (int(screen_width * 0.1), int(screen_height * 0.1)))
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.vel = 0

    def update(self):
        global flying

        if flying:
            # gravity
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            if self.rect.bottom < screen_height * 0.9:
                self.rect.y += int(self.vel)

        if not game_over:
            if is_hand_closed and self.clicked == False:
                self.clicked = True
                self.vel = -10
            if not is_hand_closed:
                self.clicked = False
            # handle the animation
            self.counter += 1
            flap_cooldown = 5

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
            self.image = self.images[self.index]

            # rotate the bird
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)

class Circle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (25, 25), 25)
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()

        # check if mouse is over the button
        if self.rect.collidepoint(pos):
            if is_hand_closed:
                action = True

        # draw button
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action

global is_hand_closed
is_hand_closed = False
bird_group = pygame.sprite.Group()
circle_group = pygame.sprite.Group()

flappy = Bird(100, int(screen_height / 2))
bird_group.add(flappy)

# create restart button instance
button = Button(screen_width // 2 - 50, screen_height // 2 - 25, button_img)

detector = HandDetector(maxHands=1, detectionCon=0.8)

# Define finger tip landmark IDs (adjust based on HandTrackingModule documentation)
thumbTipId = 4
indexTipId = 8
middleTipId = 12
ringTipId = 16
pinkyTipId = 20

# Threshold distance for considering a hand closed
closed_hand_threshold = 100

run = True
while run:
    clock.tick(fps)

    # draw background
    screen.blit(bg, (0, 0))

    bird_group.draw(screen)
    bird_group.update()
    circle_group.draw(screen)

    # draw the ground
    screen.blit(ground_img, (ground_scroll, screen_height * 0.9))

    success, img = cap.read()
    if success:
        img = cv2.flip(img, 1)  # Flip the image horizontally
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert the color to RGB for hand detection

        # Rotate the image to landscape mode
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        # Hands
        hands, img = detector.findHands(img)

        # Data to send (open/closed state)
        is_hand_closed = False

        if hands:
            # Get the first hand detected
            hand = hands[0]
            # Get landmark list
            lmList = hand['lmList']

            # Calculate distances between fingertips
            thumb_index_dist = math.sqrt(
                (lmList[thumbTipId][0] - lmList[indexTipId][0]) ** 2 + (lmList[thumbTipId][1] - lmList[indexTipId][1]) ** 2
            )
            thumb_middle_dist = math.sqrt(
                (lmList[thumbTipId][0] - lmList[middleTipId][0]) ** 2 + (lmList[thumbTipId][1] - lmList[middleTipId][1]) ** 2
            )

            # Check if distances are below the closed hand threshold
            is_hand_closed = thumb_index_dist < closed_hand_threshold and thumb_middle_dist < closed_hand_threshold

        # Check if the mouse button is pressed
        if is_hand_closed:
            flappy.vel = -10
            flying = True

        # Display hand closed status on the image
        cv2.putText(img, f"Hand Closed: {is_hand_closed}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)


        webcam_width, webcam_height = int(screen_height * 0.25), int(screen_width * 0.25)
        img = cv2.resize(img, (webcam_width, webcam_height))

        img = pygame.surfarray.make_surface(img)
        img = pygame.transform.rotate(img, -180)
        screen.blit(img, (0, 0))

    # check the score
    if pygame.sprite.spritecollide(flappy, circle_group, True):
        score += 1

    draw_text(str(score), font, white, int(screen_width / 2), 20)

    # bird hitting ground
    if flappy.rect.bottom >= screen_height * 0.9:
        game_over = True

    if not game_over and flying:
        # generate new circles
        time_now = pygame.time.get_ticks()
        if time_now - last_circle > circle_frequency:
            circle_y = random.randint(100, int(screen_height * 0.8))
            circle = Circle(screen_width, circle_y)
            circle_group.add(circle)
            last_circle = time_now

        # draw and scroll the ground
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

        circle_group.update()

    # check for game over and reset
    if game_over:
        if button.draw():
            game_over = False
            reset_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

cap.release()
cv2.destroyAllWindows()
pygame.quit()
