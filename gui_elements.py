import pygame
screen = None

class FuelGUI:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.img = pygame.image.load('./img/fuel.png')

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

    def update(self):
        pass

def add_gui_elements(gui, screen_param):
    global screen
    screen = screen_param

    gui.fuel = FuelGUI()

    gui.elements = [gui.fuel]