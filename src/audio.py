import pygame
import os

# get absolute path to sounds directory regardless of where script is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

pygame.mixer.init()
searching_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "searching.wav"))
locked_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "locked.wav"))

def play_searching():
    pass

def play_locked():
    searching_sound.stop()
    locked_sound.play()