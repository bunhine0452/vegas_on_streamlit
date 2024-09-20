import pygame
from pygame.math import Vector3
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import numpy as np
from main import VegasGame, Player, Casino

class Vegas3D:
    def __init__(self):
        pygame.init()
        self.display = (1024, 768)
        pygame.display.set_mode(self.display, pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("Las Vegas 3D")
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

        self.reshape(*self.display)
        glTranslatef(0.0, 0.0, -20)

        self.game = VegasGame(2)  # 2명의 플레이어로 게임 시작
        self.setup_3d_objects()
        self.font = pygame.font.Font(None, 36)
        self.dice_rotation = 0
        self.rolling = False
        self.roll_frames = 0
        self.dice_results = []

    def reshape(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (width / height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def setup_3d_objects(self):
        self.casino_positions = [
            (-7, 3, 0), (-2, 3, 0), (3, 3, 0),
            (-7, -3, 0), (-2, -3, 0), (3, -3, 0)
        ]
        self.dice_positions = [(-9, 0, 0), (9, 0, 0)]
        self.casino_colors = [
            (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            (1.0, 1.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0)
        ]

    def draw_complex_cube(self):
        vertices = [
            [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1],
            [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1]
        ]
        edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]
        faces = [
            (0,1,2,3), (4,5,6,7), (0,3,7,4), (1,2,6,5),
            (0,1,5,4), (2,3,7,6)
        ]

        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()

        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

    def draw_casinos(self):
        for i, pos in enumerate(self.casino_positions):
            glPushMatrix()
            glTranslatef(*pos)
            glScalef(1.0, 1.0, 0.5)
            glColor3fv(self.casino_colors[i])
            self.draw_complex_cube()
            glPopMatrix()

            self.render_text(f"Casino {i+1}", pos[0], pos[1]+1.5, pos[2])
            money = sum(self.game.casinos[i].money)
            self.render_text(f"${money}", pos[0], pos[1]-1.5, pos[2])

            dice_str = ", ".join([f"P{p+1}: {c}" for p, c in self.game.casinos[i].dice.items()])
            self.render_text(dice_str, pos[0], pos[1]-2, pos[2])

    def draw_dice(self):
        for i, pos in enumerate(self.dice_positions):
            glPushMatrix()
            glTranslatef(*pos)
            if self.rolling and i == self.game.current_player:
                glRotatef(self.dice_rotation, 1, 1, 1)
            glScalef(0.5, 0.5, 0.5)
            glColor3f(1.0, 1.0, 1.0)
            self.draw_complex_cube()
            glPopMatrix()

            player = self.game.players[i]
            self.render_text(f"Player {i+1}: ${player.money}", pos[0], pos[1]-1, pos[2])
            if player.current_roll:
                roll_text = ", ".join(map(str, player.current_roll))
                self.render_text(f"Roll: {roll_text}", pos[0], pos[1]-1.5, pos[2])
            self.render_text(f"Dice left: {player.dice}", pos[0], pos[1]-2, pos[2])

    def render_text(self, text, x, y, z):
        glDisable(GL_LIGHTING)
        glColor3f(1, 1, 1)  # 흰색 텍스트
        glRasterPos3f(x, y, z)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glEnable(GL_LIGHTING)

    def draw_scene(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -20)

        # 배경색 변경
        glClearColor(0.2, 0.2, 0.2, 1)  # 어두운 회색

        self.draw_casinos()
        self.draw_dice()

        self.render_text(f"Round: {self.game.current_round}", -5, 5, 0)
        self.render_text(f"Current Player: {self.game.current_player + 1}", 0, 5, 0)

        if self.dice_results:
            self.render_text("Dice Results:", -5, 6, 0)
            for i, result in enumerate(self.dice_results):
                self.render_text(f"{i+1}: {result}", -5, 6.5 + i*0.5, 0)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.roll_dice()
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                    self.place_dice(int(pygame.key.name(event.key)))

    def roll_dice(self):
        if not self.rolling and self.game.play_round():
            self.rolling = True
            self.roll_frames = 0
            self.dice_results = self.game.players[self.game.current_player].current_roll

    def animate_roll(self):
        if self.rolling:
            self.dice_rotation += 10
            self.roll_frames += 1
            if self.roll_frames >= 30:  # 30 프레임 동안 회전
                self.rolling = False
                self.dice_rotation = 0
                print(f"Player {self.game.current_player + 1} rolled: {self.dice_results}")

    def place_dice(self, casino_index):
        if self.game.place_dice(casino_index):
            print(f"Player {self.game.current_player + 1} placed dice in Casino {casino_index}")
            self.dice_results = []  # 주사위 결과 초기화
            if all(player.dice == 0 for player in self.game.players):
                self.end_round()

    def end_round(self):
        winnings = self.game.end_round()
        print(f"Round {self.game.current_round - 1} ended")
        for player_id, player_winnings in winnings.items():
            print(f"Player {player_id + 1} winnings:")
            for casino_number, amount in player_winnings:
                if amount > 0:
                    print(f"  Casino {casino_number}: ${amount}")
        if self.game.current_round > 4:
            self.end_game()

    def end_game(self):
        winner = self.game.get_winner()
        print(f"Game Over! Winner: Player {winner.id + 1} (${winner.money}, {winner.card_count} cards)")
        pygame.quit()
        quit()

    def run(self):
        while True:
            self.handle_events()
            self.animate_roll()
            self.draw_scene()
            pygame.time.wait(10)

if __name__ == "__main__":
    Vegas3D().run()