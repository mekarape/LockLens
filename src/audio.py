import pygame

pygame.mixer.init()
searching_sound = pygame.mixer.Sound("sounds/searching.wav")
locked_sound = pygame.mixer.Sound("sounds/locked.wav")

def play_searching():
    if not searching_sound.get_num_channels():
        searching_sound.play(loops=-1)

def play_locked():
    searching_sound.stop()
    locked_sound.play()
