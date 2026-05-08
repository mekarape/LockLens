import pygame
import os

# get absolute path to sounds directory regardless of where script is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

pygame.mixer.init()
locked_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "locked.wav"))

# searching audio disabled
def play_searching():
    pass

def play_locked():
    locked_sound.play()