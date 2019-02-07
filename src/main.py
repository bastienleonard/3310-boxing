#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import random
import time

import pyxel

SCREEN_WIDTH = 84
SCREEN_HEIGHT = 48

COLOR_LIGHT = 0
COLOR_DARK = 1

MAX_HP = 100

HP_BAR_SIDE_MARGIN = 4

SPRITE_HEIGHT = 32
SPRITE_WIDTH = 32

JAB_DURATION = 0.2
PULL_DURATION = 0.1


def on_jab(jabber, jabbee, delay):
    def f():
        if jabbee.state.hittable() and jabbee.hp > 0:
            jabbee.hp -= 10

    if jabbee.is_human:
        # Leave the player some time to pull
        delay(0.3, f)
    else:
        f()


class Timer:
    def __init__(self):
        self.delays = collections.defaultdict(list)

    def start(self):
        self.tick = time.perf_counter()

    def update(self, frames, elapsed):
        for delay, funcs in self.delays.copy().items():
            del self.delays[delay]
            delay -= elapsed

            if delay <= 0:
                for f in funcs:
                    f()
            else:
                self.delays[delay] += funcs

    def elapsed(self):
        return time.perf_counter() - self.tick

    def delay(self, delay, f):
        self.delays[float(delay)].append(f)


class Sprite:
    def __init__(self, offset):
        self._offset = offset

    def draw(self, x, y, flip=False):
        width = SPRITE_WIDTH

        if flip:
            width = -width

        pyxel.blt(x, y, 0, 0, self._offset * SPRITE_HEIGHT, width,
                  SPRITE_HEIGHT, COLOR_LIGHT)


class Sprites:
    IDLE = Sprite(0)
    JAB = Sprite(1)
    PULL = Sprite(2)


class BoxerState:
    IDLE = 0
    JABBING = 1
    PULLING = 2

    TRANSITIONS = {
        IDLE: (JABBING, PULLING),
        JABBING: (IDLE, ),
        PULLING: (IDLE, )
    }

    def __init__(self):
        self.current = BoxerState.IDLE
        self.current_state_duration = 0

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        self.current_state_duration = 0

    def hittable(self):
        return self.current != BoxerState.PULLING

    def change_to(self, new_state):
        if self.current == new_state:
            return False

        if new_state in self.TRANSITIONS[self.current]:
            self.current = new_state
            return True

        return False

    def update(self, frames, elapsed):
        self.current_state_duration += elapsed

        if self.current == BoxerState.JABBING:
            if self.current_state_duration >= JAB_DURATION:
                self.change_to(BoxerState.IDLE)
        elif self.current == BoxerState.PULLING:
            if self.current_state_duration >= PULL_DURATION:
                self.change_to(BoxerState.IDLE)

    def sprite(self):
        return {
            BoxerState.IDLE: Sprites.IDLE,
            BoxerState.JABBING: Sprites.JAB,
            BoxerState.PULLING: Sprites.PULL
        }[self.current]


class Ai:
    def __init__(self, jab):
        self.idle_for = 0
        self.jab = jab
        self.hit_after = random.randint(1, 4)

    def update(self, frames, elapsed):
        self.idle_for += elapsed

        if self.idle_for > self.hit_after:
            self.jab()
            self.idle_for = 0
            self.hit_after = random.randint(1, 5)


class Boxer:
    def __init__(self, x, is_human):
        self.x = x
        self.is_human = is_human
        self.hp = MAX_HP
        self.state = BoxerState()

    def update(self, frames, elapsed):
        self.state.update(frames, elapsed)

    def draw(self, flip):
        self.state.sprite().draw(
            self.x, SCREEN_HEIGHT - 3 - SPRITE_HEIGHT, flip=flip)

    def jab(self, other, timer):
        if self.state.change_to(BoxerState.JABBING):
            on_jab(self, other, lambda d, f: timer.delay(d, f))

    def pull(self):
        self.state.change_to(BoxerState.PULLING)


class HpBar:
    HEIGHT = 2

    def __init__(self, x, y, width, boxer):
        self.x = x
        self.y = y
        self.width = width
        self.boxer = boxer

    def draw(self):
        width = self.boxer.hp / MAX_HP * self.width

        if width > 0:
            pyxel.rect(self.x, self.y, self.x + width - 1, self.HEIGHT,
                       COLOR_DARK)


class Game:
    def __init__(self):
        self.player_a = Boxer(SCREEN_WIDTH / 2 - 22, is_human=True)
        self.player_b = Boxer(SCREEN_WIDTH / 2 - 10, is_human=False)
        self.player_a_hp_bar = HpBar(HP_BAR_SIDE_MARGIN, 0, 30, self.player_a)
        self.player_b_hp_bar = HpBar(SCREEN_WIDTH - HP_BAR_SIDE_MARGIN - 30, 0,
                                     30, self.player_b)
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            caption='Boxing',
            palette=(0xc7f0d8, 0x43523d, *((0xff00ff, ) * 14)),
            scale=6)
        pyxel.image(0).load(0, 0, 'sprites/sprites-sheet.png')
        self.timer = Timer()
        self.ai = Ai(lambda: self.player_b.jab(self.player_a, self.timer))

    def run(self):
        self.last_frame_count = pyxel.frame_count
        self.timer.start()
        pyxel.run(self.update, self.draw)

    def update(self):
        frames = pyxel.frame_count - self.last_frame_count
        self.last_frame_count = pyxel.frame_count
        elapsed = self.timer.elapsed()
        self.timer.start()

        if frames <= 0 or elapsed <= 0:
            return

        self.timer.update(frames, elapsed)
        self.player_a.update(frames, elapsed)
        self.player_b.update(frames, elapsed)

        if pyxel.btn(pyxel.KEY_Z):
            self.player_a.jab(self.player_b, self.timer)

        if pyxel.btn(pyxel.KEY_X):
            self.player_a.pull()

        self.ai.update(frames, elapsed)

    def draw(self):
        pyxel.cls(0)
        self.player_a.draw(False)
        self.player_b.draw(True)
        self.player_a_hp_bar.draw()
        self.player_b_hp_bar.draw()


def main():
    Game().run()


if __name__ == '__main__':
    main()
