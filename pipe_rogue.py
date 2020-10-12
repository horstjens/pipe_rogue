"""
pipe_rogue
a playable tutorial about roguelike programming using python3, pygame and other tools
part of the ThePythonGameBook project, see http://thepythongamebook.com
author: Horst JENS
email: horstjens@gmail.com
contact: see http://spielend-programmieren.at/de:kontakt
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
download: https://github.com/horstjens/pipe_rogue

based on: http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod,_part_4

field of view and exploration
see http://www.roguebasin.com/index.php?title=Comparative_study_of_field_of_view_algorithms_for_2D_grid_based_worlds

field of view improving, removing of artifacts:
see https://sites.google.com/site/jicenospam/visibilitydetermination

license for media, fonts etc: see /data/imagerights.txt

unicode tables:
# https://unicode.org/charts/PDF/U2600.pdf
# https://en.wikibooks.org/wiki/Unicode/Character_reference/2000-2FFF
# https://en.wikipedia.org/wiki/Box_Drawing_(Unicode_block)
# https://dejavu-fonts.github.io/
# defja vu sans: http://dejavu.sourceforge.net/samples/DejaVuSans.pdf
# deja vu sans mono: http://dejavu.sourceforge.net/samples/DejaVuSansMono.pdf
# free icons from google: https://material.io/resources/icons/?style=baseline

# useful: 3stars: \u2042
# pycharm colorpicker: alt+enter+c

# font vs freetype: font can not render long unicode characters... render can. render can also rotate text

"""
# TODO: movement phases -> player shoot, monster shoot, player move, monster move?
# TODO: Flytext is invisible when color=(0,0,0)
# TODO: flyingobject- mode (flytext) for viewer.run -> nothing else happens until all flyers are finished flying around
# TODO: aim mode: show hit-propability at cursor tile
# TODO: make update for effects instead of processing_effects
# TODO: shield: should protect from combat (and fire?) damange, should prevent attacking in meleee
# TODO: monster update should call monster_ai
# TODO: GUI buttons for commands
# TODO: GUI yes-no box
# TODO: save and load game to/from disk
# TODO: PgUp/PgDown should scroll log text
# TODO: flying arrow should not leave blurred "path" (repaint) #  arrow should end flying BEFORE monster start moving away
# TODO: help text of all keyboard commands
# TODO: better (longer) chars / glyphs for glass window, door
# TODO: better code for FireDragon ( hunt/flee ), keep distance, reload...
# TODO: Flames / Water becoming smaller and smaller before disappearing
# TODO: progress bar for terminal download
# TODO: learn LayerdDirty Spritegroups, update all sprites to DirtySprites -> make dirty and visible work correctly
# TODO: game menu, death of player -> newstart
# TODO: include pathfinding from test
# TODO: save levels to pickle, load levels when changing player.z
# TODO: dungeon generator, dungeon Viewer / Editor (pysimplegui?)
# TODO: include complex fight / strike system
# TODO: diplay unicode symbols for attack/defense rolls
# TODO: light emitting lamps, difference fov - light, turning lamps on and off, sight_distacne <> torchradius
# TODO: big enjoy Flytext: gridcursorsprite is painted OVER flytext -> should be: first grid, than flytext on top!
# TODO: (autohiding) hint/button in panel when player at stair and up/down command is possible
# TODO: Monster movement: actualy move (sprites) instead of teleport tiles. Fixed time (0.5 sec) for all movements?
# TODO: Monster moving toward each other when fighting
# TODO: animations of blocks / monsters when nothing happens -> animcycle
# TODO: non-player light source / additive lightmap
# TODO: drop items -> autoloot? manual pickup command?
# done: arrow sprite uses unicode glyph like Item
# done: shooting through walls is possible?!
# done: minimalspeed für Arrow, soll trotzdem am target_tile verschwinden - max_distance
# done: use arrows for shooting -> destroy used arrow
# done: replace soup and food icons with noto font glyph u1F35C
# done: shield: better icon : mushroom -> triangle Noto font
# done: shield: alpha for whole bitmap only works on Mac.
# done: make disk icon in panel smaller
# done: make correct docstring for make_text
# done: make font in download_effect smaller
# done: negative age for flytext does not work
# done: clean code in panel-update (why is fps showing there?)
# done: make trap-detect -radius for player
# done: items visible below monsters/player
# done: turn system - each effect must finish before next turn starts
# done: less max_age for effects (Trap, fight) -> 1 second max_age for Flytext
# done: import dice functions with re-roll, use for Trap damage
# done: Trap code should respect Trap.__init__ for damage etc
# done: better battle impact effects
# done: set_alpha , transparency for Flytext sprite. (setalpha works only with freetye.render_to, not with freetype.render
# done: fat skull for trap -> STRONG textstyle for Flytext
# done: in Viewer.load_images, iterate over all subclasses of Structure automatically
# done: shießen mit F geht nicht mehr
# done: cursorsprite : Fehler -> wird ungenau je mehr man nach rechts fährt
# done: schießen mit f zeigt falschen pfad nach levelwechsel
# done: cursorsprite: Fehler -> cursor kann rechten und unteren dungeonrand verlassen -Formel?
# done: eat food with "e"
# don: make bitmpap out of every maketext-char to faciliate easier replacing with images
# wontfix because using maketext:  fireeffect sprite erscheint in der linken oberen ecke -> create_image / init / update ?

import pygame
import pygame.freetype  # not automatically loaded when importing pygame!
import random
import os

version = 0.5


class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygames sprite class"""

    number = 0

    # numbers = {} # { number, Sprite }

    def __init__(self, **kwargs):
        self._default_parameters(**kwargs)
        self._overwrite_parameters()
        pygame.sprite.Sprite.__init__(
            self, self.groups
        )  # call parent class. NEVER FORGET !
        self.number = VectorSprite.number  # unique number for each sprite
        VectorSprite.number += 1
        # VectorSprite.numbers[self.number] = self
        self.visible = False
        self.create_image()
        self.distance_traveled = 0  # in pixel
        # self.rect.center = (-300,-300) # avoid blinking image in topleft corner
        if self.angle != 0:
            self.set_angle(self.angle)

    def _overwrite_parameters(self):
        """change parameters before create_image is called"""
        pass

    def _default_parameters(self, **kwargs):
        """get unlimited named arguments and turn them into attributes
        default values for missing keywords"""

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if "layer" not in kwargs:
            self.layer = 0
        # else:
        #    self.layer = self.layer
        if "pos" not in kwargs:
            self.pos = pygame.math.Vector2(200, 200)
        if "move" not in kwargs:
            self.move = pygame.math.Vector2(0, 0)
        if "angle" not in kwargs:
            self.angle = 0  # facing right?
        if "radius" not in kwargs:
            self.radius = 5
        if "width" not in kwargs:
            self.width = self.radius * 2
        if "height" not in kwargs:
            self.height = self.radius * 2
        if "color" not in kwargs:
            # self.color = None
            self.color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        if "hitpoints" not in kwargs:
            self.hitpoints = 100
        self.hitpointsfull = self.hitpoints  # makes a copy

        if "stop_on_edge" not in kwargs:
            self.stop_on_edge = False
        if "bounce_on_edge" not in kwargs:
            self.bounce_on_edge = False
        if "kill_on_edge" not in kwargs:
            self.kill_on_edge = False
        if "warp_on_edge" not in kwargs:
            self.warp_on_edge = False
        if "age" not in kwargs:
            self.age = 0  # age in seconds. A negative age means waiting time until sprite appears
        if "max_age" not in kwargs:
            self.max_age = None

        if "max_distance" not in kwargs:
            self.max_distance = None
        if "picture" not in kwargs:
            self.picture = None
        if "boss" not in kwargs:
            self.boss = None
        if "kill_with_boss" not in kwargs:
            self.kill_with_boss = False
        if "move_with_boss" not in kwargs:
            self.move_with_boss = False

    def kill(self):
        # check if this is a boss and kill all his underlings as well
        tokill = []
        for s in Viewer.allgroup:
            if "boss" in s.__dict__ and s.boss == self:
                tokill.append(s)
        for s in tokill:
            s.kill()
        # if self.number in self.numbers:
        #   del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)

    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos[0], 0), round(self.pos[1], 0))
        self.width = self.rect.width
        self.height = self.rect.height

    def rotate(self, by_degree):
        """rotates a sprite and changes it's angle by by_degree"""
        self.angle += by_degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def set_angle(self, degree):
        """rotates a sprite and changes it's angle to degree"""
        self.angle = degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        self.age += seconds
        if self.age < 0:
            return
        self.visible = True
        self.distance_traveled += self.move.length() * seconds
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # ---- movement with/without boss ----
        if self.boss and self.move_with_boss:
            self.pos = self.boss.pos
            self.move = self.boss.move
        else:
            # move independent of boss
            self.pos += self.move * seconds
            self.wallcheck()
        # print("rect:", self.pos.x, self.pos.y)
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def wallcheck(self):
        # ---- bounce / kill on screen edge ----
        # ------- left edge ----
        if self.pos.x < 0:
            if self.stop_on_edge:
                self.pos.x = 0
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = 0
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = Viewer.width
        # -------- upper edge -----
        # hud on top screen edge = 20 pixel = Viewer.hud_height
        if self.pos.y < Viewer.hudheight:
            if self.stop_on_edge:
                self.pos.y = Viewer.hudheight
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = Viewer.hudheight
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = Viewer.height
        # -------- right edge -----
        if self.pos.x > Viewer.width:
            if self.stop_on_edge:
                self.pos.x = Viewer.width
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = Viewer.width
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = 0
        # --------- lower edge ------------
        if self.pos.y > Viewer.height:
            if self.stop_on_edge:
                self.pos.y = Viewer.height
            if self.kill_on_edge:
                self.hitpoints = 0
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = Viewer.height
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = 0


class Flytext(VectorSprite):
    def __init__(
        self,
        tx=None,
        ty=None,
        pos=pygame.math.Vector2(50, 50),
        move=pygame.math.Vector2(0, -50),
        text="hallo",
        color=(255, 0, 0),
        bgcolor=None,
        max_age=0.5,
        age=0,
        acceleration_factor=1.0,
        fontsize=48,
        textrotation=0,
        style=pygame.freetype.STYLE_STRONG,
        alpha_start=255,
        alpha_end=255,
        width_start=None,
        width_end=None,
        height_start=None,
        height_end=None,
        rotate_start=0,
        rotate_end=0,
    ):
        """Create a flying VectorSprite with text that disappears after a while

        :param int tx:                      startposition x in tiles. If not None, it overwrites pos Vector
        :param int ty:                      startposition y in tiles. If not None, it overwrites pos Vector
        :param pygame.math.Vector2 pos:     startposition in Pixel. To attach the text to another Sprite, use an existing Vector.
        :param pygame.math.Vector2 move:    movevector in Pixel per second
        :param text:                        the text to render. accept unicode chars
        :param (int,int,int) color:         foregroundcolor for text
        :param (int,int,int) bgcolor:       backgroundcolor for text. If set to None, black is the transparent color
        :param float max_age:               lifetime of Flytext in seconds. Delete itself when age > max_age
        :param float age:                   start age in seconds. If negative, Flytext stay invisible until age >= 0
        :param float acceleration_factor:   1.0 for no acceleration. > 1 for acceleration of move Vector, < 1 for negative acceleration
        :param int fontsize:                fontsize for text
        :param float textrotation:          static textrotation in degree for rendering text.
        :param int style:                   effect for text rendering, see pygame.freetype constants
        :param int alpha_start:             alpha value for age =0. 255 is no transparency, 0 is full transparent
        :param int alpha_end:               alpha value for age = max_age.
        :param int width_start:              start value for dynamic zooming of width in pixel
        :param int width_end:                end value for dynamic zooming of width in pixel
        :param int height_start:             start value for dynamic zooming of height in pixel
        :param int height_end:               end value for dynamic zooming of height in pixel
        :param float rotate_start:          start angle for dynamic rotation of the whole Flytext Sprite
        :param float rotate_end:            end angle for dynamic rotation
        :return: None
        """

        if tx is not None and ty is not None:
            self.tx, self.ty = tx, ty
            px, py = Viewer.tile_to_pixel((tx, ty))
            posvector = pygame.math.Vector2(px, py)
            pos = posvector
        self.recalc_each_frame = False
        self.text = text
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.alpha_diff_per_second = (alpha_start - alpha_end) / max_age
        if alpha_end != alpha_start:
            self.recalc_each_frame = True
        self.style = style
        self.acceleration_factor = acceleration_factor
        self.fontsize = fontsize
        self.textrotation = textrotation
        self.color = color
        self.bgcolor = bgcolor
        self.width_start = width_start
        self.width_end = width_end
        self.height_start = height_start
        self.height_end = height_end
        if width_start is not None:
            self.width_diff_per_second = (width_end - width_start) / max_age
            self.recalc_each_frame = True
        else:
            self.width_diff_per_second = 0
        if height_start is not None:
            self.height_diff_per_second = (height_end - height_start) / max_age
            self.recalc_each_frame = True
        else:
            self.height_diff_per_second = 0
        self.rotate_start = rotate_start
        self.rotate_end = rotate_end
        if (rotate_start != 0 or rotate_end != 0) and rotate_start != rotate_end:
            self.rotate_diff_per_second = (rotate_end - rotate_start) / max_age
            self.recalc_each_frame = True
        else:
            self.rotate_diff_per_second = 0
        # self.visible = False
        VectorSprite.__init__(
            self,
            color=color,
            pos=pos,
            move=move,
            max_age=max_age,
            age=age,
        )
        self._layer = 7  # order of sprite layers (before / behind other sprites)
        # print("start visible", self.visible)

        # acceleration_factor  # if < 1, Text moves slower. if > 1, text moves faster.

    def create_image(self):
        myfont = Viewer.font
        # text, textrect = myfont.render(
        # fgcolor=self.color,
        # bgcolor=self.bgcolor,
        # get_rect(text, style=STYLE_DEFAULT, rotation=0, size=0) -> rect
        textrect = myfont.get_rect(
            text=self.text,
            size=self.fontsize,
            rotation=self.textrotation,
            style=self.style,
        )  # font 22
        self.image = pygame.Surface((textrect.width, textrect.height))
        # render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0) -> Rect
        textrect = myfont.render_to(
            surf=self.image,
            dest=(0, 0),
            text=self.text,
            fgcolor=self.color,
            bgcolor=self.bgcolor,
            style=self.style,
            rotation=self.textrotation,
            size=self.fontsize,
        )
        if self.bgcolor is None:
            self.image.set_colorkey((0, 0, 0))

        self.rect = textrect
        # transparcent ?
        if self.alpha_start == self.alpha_end == 255:
            pass
        elif self.alpha_start == self.alpha_end:
            self.image.set_alpha(self.alpha_start)
            # print("fix alpha", self.alpha_start)
        else:
            self.image.set_alpha(
                self.alpha_start - self.age * self.alpha_diff_per_second
            )
            # print("alpha:", self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        # save the rect center for zooming and rotating
        oldcenter = self.image.get_rect().center
        # dynamic zooming ?
        if self.width_start is not None or self.height_start is not None:
            if self.width_start is None:
                self.width_start = textrect.width
            if self.height_start is None:
                self.height_start = textrect.height
            w = self.width_start + self.age * self.width_diff_per_second
            h = self.height_start + self.age * self.height_diff_per_second
            self.image = pygame.transform.scale(self.image, (int(w), int(h)))
        # rotation?
        if self.rotate_start != 0 or self.rotate_end != 0:
            if self.rotate_diff_per_second == 0:
                self.image = pygame.transform.rotate(self.image, self.rotate_start)
            else:
                self.image = pygame.transform.rotate(
                    self.image,
                    self.rotate_start + self.age * self.rotate_diff_per_second,
                )
        # restore the old center after zooming and rotating
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def update(self, seconds):
        VectorSprite.update(self, seconds)
        # print("Flytext age:", self.age, self.visible)
        if self.age < 0:
            return
        self.move *= self.acceleration_factor
        if self.recalc_each_frame:
            self.create_image()


class BlueTile(VectorSprite):
    def _overwrite_parameters(self):
        self.color = (0, 0, 255)  # blue

    def create_image(self):
        self.image = pygame.surface.Surface((Viewer.gridsize[0], Viewer.gridsize[1]))
        # c = random.randint(100, 250)

        pygame.draw.rect(
            self.image, self.color, (0, 0, Viewer.gridsize[0], Viewer.gridsize[1]), 5
        )
        # self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(128)
        # self.image.convert_alpha()
        self.rect = self.image.get_rect()


class TileCursor(VectorSprite):
    def _overwrite_parameters(self):
        self.tx, self.ty = 0, 0

    def create_image(self):
        w = pulse(self.age, 1, 5, 5)
        self.image = pygame.surface.Surface(
            (Viewer.gridsize[0] + w, Viewer.gridsize[1] + w)
        )
        c = pulse(self.age, 200, 255, 55)
        w = pulse(self.age, 1, 5, 5)
        pygame.draw.rect(
            self.image,
            (100, 0, c),
            (0, 0, Viewer.gridsize[0] + w, Viewer.gridsize[1] + w),
            w,
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()

    def update(self, seconds):
        self.create_image()  # always make new image every frame with different color
        self.tx, self.ty = Viewer.pixel_to_tile(
            pygame.mouse.get_pos()
        )  # for panelinfo!
        # hero = Game.player
        # print("hero at ", hero.x, hero.y)
        x, y = Viewer.tile_to_pixel((self.tx, self.ty))
        # x,y = Viewer.tile_to_pixel((self.tx-hero.x,self.ty-hero.y))
        self.pos = pygame.math.Vector2((x, y))
        super().update(seconds)


class FlyingObject(VectorSprite):
    """arrow, fireball etc: flies in a pre-defined path from one dungeon tile to another
    except arguments: start_tile, end_tile"""

    def _overwrite_parameters(self):
        # self.picture = image #Viewer.images["arrow"]
        print("arrow from", self.start_tile, "to", self.end_tile)
        self.pos = Viewer.tile_to_pixel(self.start_tile)
        if self.max_age is None:
            self.max_age = 1.0  # secs

        x1, y1 = self.start_tile
        x2, y2 = self.end_tile
        m = pygame.math.Vector2(x2, y2) - pygame.math.Vector2(x1, y1)
        dist = m.length()
        # calculate speed by dist and max_age
        self.speed = dist * Viewer.gridsize[0] / self.max_age
        m.normalize_ip()
        m *= self.speed
        self.move = m
        self.angle = -m.angle_to(pygame.math.Vector2(1, 0))


class Bubble(VectorSprite):
    """a round fragment or bubble particle"""

    def _overwrite_parameters(self):
        self.speed = random.randint(10, 50)
        if self.max_age is None:
            self.max_age = 0.2 + random.random() * 0.5
        self.kill_on_edge = True
        self.kill_with_boss = False  # VERY IMPORTANT!!!
        if self.move == pygame.math.Vector2(0, 0):
            # self.move = pygame.math.Vector2(self.boss.move.x, self.boss.move.y)
            self.move = pygame.math.Vector2(1, 0)
            # self.move.normalize_ip()
            self.move *= self.speed
            # a, b = 160, 200
            # else:
            a, b = 0, 360
            #    self.move = pygame.math.Vector2(self.speed, 0)
            self.move.rotate_ip(random.randint(a, b))
        # print("ich bin da", self.pos, self.move)

    def create_image(self):
        self.radius = random.randint(3, 8)
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius))
        r, g, b = self.color
        r += random.randint(-30, 30)
        g += random.randint(-30, 30)
        b += random.randint(-30, 30)
        r = between(r)  # 0<-->255
        g = between(g)
        b = between(b)
        self.color = (r, g, b)
        pygame.draw.circle(
            self.image, self.color, (self.radius, self.radius), self.radius
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()


class Game:
    player = None
    torch_radius = 12
    dungeon = []
    # hold global variables
    zoo = {}  # container for all monsters, including the player
    monsternumber = 0  # counter for all monsters
    items = {}
    itemnumber = 0
    turn_number = 0
    effectnumber = 0
    running = True
    max_tiles_x = 0  # max. dimension of an auto-generated dungeon level
    max_tiles_y = 0  # max. dimension of an auto-generated dungeon level
    effects = {}  # effects for this dungeon level
    # lookup1: dx, dy -> index, start with north, then clockwise
    lookup_nesw = {(-1, 0): 0, (0, 1): 1, (1, 0): 2, (0, -1): 3}

    def __init__(self):
        # self.create_dungeon([level1, level2, level3])
        for z, level in enumerate([level1, level2, level3]):
            self.create_dungeon2(level, z)

        # extra food on2,4
        Food(2, 4, 0)
        # --------extra effects at start of game --------------
        # Fire(3, 1, max_age=5)
        # Fire(3, 2, max_age=7)
        # Fire(1, 2, max_age=10)
        # Water(4, 1, max_age=10)
        # Water(5, 1, max_age=10)
        self.calculate_fov()
        Game.turn_number = 0

    # @staticmethod
    # def make_empty_effect_map():
    #    # Game.effects = [ [None for element in line] for line in Game.dungeon[z] ]
    #    Game.effects = {}

    def process_effects(self):
        """next turn for each effect and remove destroyed effects"""
        for e in Game.effects.values():
            e.next_turn()
        Game.effects = {
            k: v for k, v in Game.effects.items() if not v.destroy
        }  # remove destroyed effects

    def create_dungeon2(self, raw_level, z):
        """append or replace level z in Game.dungeons, created from raw_level
        expect 'legend' dictionary {char:ClassName,..} at module level

        :param str raw_level:   a multi-lined text made up of chars for dungeon, according to dict 'legend'
        :param int z:           index of the new level in Game.dungeons. Use to append / replace level
        :return: None
        """
        raw = [list(line) for line in raw_level.splitlines() if len(line) > 1]
        new_level = []
        for ty, line in enumerate(raw):
            new_line = []
            for tx, char in enumerate(line):
                # monsters (including the player) and items generate a floor tile
                myclass = legend[char]  # legend is a top-level variable
                classnames = [
                    c.__name__ for c in myclass.mro()
                ]  # classname.mro() displays all superclasses
                if "Monster" in classnames or "Item" in classnames:
                    new_line.append(Floor())
                    if char == "@":
                        Game.player = Player(tx, ty, z)
                    else:
                        myclass(
                            tx, ty, z
                        )  # Monsters go to Game.zoo, Items go to Game.items
                else:
                    new_line.append(myclass())
            new_level.append(new_line)
        # ------------ append (or replace) new level to Game.dungeon -----------------------------
        if z == len(Game.dungeon):
            Game.dungeon.append(new_level)
        elif 0 <= z < len(Game.dungeon):
            Game.dungeon[z] = new_level
        else:
            raise ValueError("z too big for Game.dungeon")
        # --------------------- create picture for each structure tile , depending on neighbors -----------------------
        for ty, line in enumerate(new_level):
            for tx, tile in enumerate(line):
                print(
                    "creating pic for:",
                    Game.dungeon[z][ty][tx].__class__.__name__,
                    tx,
                    ty,
                )
                # get neighboring tiles to create picture:
                # start at 12:00 and move clockwise
                neighbors = []
                # for dx, dy in [(0,-1), (1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]:
                for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                    if (
                        tx + dx < 0
                        or tx + dx >= len(line)
                        or ty + dy < 0
                        or ty + dy >= len(new_level)
                    ):
                        neighbors.append(None)
                        continue
                    neighbors.append(new_level[ty + dy][tx + dx])
                Game.dungeon[z][ty][tx].create_pictures(neighbors)

    def bgcolor(self, distance, mingrey=0, maxgrey=255):
        """calculates a background (grey) color value, depending on
        distance from torch (player)
        close to torch -> maxgrey
        far away from torch ->mingrey"""
        distance = min(distance, Game.torch_radius)
        greydiff = maxgrey - mingrey
        d = distance / Game.torch_radius
        return 255 - int(mingrey + d * greydiff)

    def calculate_fov_points(self, points):
        """needs a points-list (from Bresham's get_line method)
        starting from player position to tile"""
        z = Game.player.z
        for point in points:
            x, y = point[0], point[1]
            # player tile always visible
            if x == Game.player.x and y == Game.player.y:
                Game.dungeon[z][y][
                    x
                ].fov = True  # make this tile visible and move to next point
                Game.dungeon[z][y][x].explored = True
                # Game.dungeon[z][y][x].bgcolor = Game.player.fgcolor + " on " + "rgb(200,200,200)"
                Game.dungeon[z][y][x].bgcolor = (200, 200, 200)
                continue
            # outside of dungeon level ?
            try:
                tile = Game.dungeon[z][y][x]
            except IndexError:
                continue  # outside of dungeon error
            # outside of torch radius ?
            distance = ((Game.player.x - x) ** 2 + (Game.player.y - y) ** 2) ** 0.5
            if distance > Game.torch_radius:
                continue
            # distance 0: max light (255)
            # distance == torch_radius: minimum light (128)
            g = self.bgcolor(distance, 32, 255)
            # Game.dungeon[z][y][x].bgcolor = f"rgb({g},{g},{g})"
            Game.dungeon[z][y][x].bgcolor = (g, g, g)
            Game.dungeon[z][y][x].fov = True  # make this tile visible
            Game.dungeon[z][y][x].explored = True
            if tile.block_sight:
                break  # forget the rest

    def calculate_fov(self):
        self.process_effects()
        ##Game.fov_map = []
        # self.checked = set() # clear the set of checked coordinates
        # checked = set() # clear set. a coordinate con only be once in a set.
        px, py, pz = Game.player.x, Game.player.y, Game.player.z
        # fmap = Game.dungeon[pz]

        # set all tiles to False
        for line in Game.dungeon[pz]:
            for tile in line:
                tile.fov = False
        # set player's tile to visible
        Game.dungeon[pz][py][px].fov = True
        # get coordinates form player to point at end of torchradius / torchsquare
        endpoints = set()
        for y in range(py - Game.torch_radius, py + Game.torch_radius + 1):
            if y == py - Game.torch_radius or y == py + Game.torch_radius:
                for x in range(px - Game.torch_radius, px + Game.torch_radius + 1):
                    endpoints.add((x, y))
            else:
                endpoints.add((px - Game.torch_radius, y))
                endpoints.add((px + Game.torch_radius, y))
        for coordinate in endpoints:
            # a line of points from the player position to the outer edge of the torchsquare
            points = get_line((px, py), (coordinate[0], coordinate[1]))
            self.calculate_fov_points(points)
        # print(Game.fov_map)
        # ---------- the fov map is now ready to use, but has some ugly artifacts ------------
        # ---------- start post-processing fov map to clean up the artifacts ---
        # -- basic idea: divide the torch-square into 4 equal sub-squares.
        # -- look of a invisible wall is behind (from the player perspective) a visible
        # -- ground floor. if yes, make this wall visible as well.
        # -- see https://sites.google.com/site/jicenospam/visibilitydetermination
        # ------ north-west of player
        for xstart, ystart, xstep, ystep, neighbors in [
            (-Game.torch_radius, -Game.torch_radius, 1, 1, [(0, 1), (1, 0), (1, 1)]),
            (-Game.torch_radius, Game.torch_radius, 1, -1, [(0, -1), (1, 0), (1, -1)]),
            (
                Game.torch_radius,
                -Game.torch_radius,
                -1,
                1,
                [(0, -1), (-1, 0), (-1, -1)],
            ),
            (Game.torch_radius, Game.torch_radius, -1, -1, [(0, 1), (-1, 0), (-1, 1)]),
        ]:

            for x in range(px + xstart, px, xstep):
                for y in range(py + ystart, py, ystep):
                    # not even in fov?
                    # visible = Game.dungeon[pz][py][px].fov#[y][x]
                    # if visible:
                    if Game.dungeon[pz][py][px].fov:
                        continue  # next, i search invisible tiles!
                    # oh, we found an invisble tile! now let's check:
                    # is it a wall?
                    if isinstance(Game.dungeon[pz][y][x], Wall):  ##char != "#":
                        continue  # next, i search walls!
                    # --ok, found an invisible wall.
                    # check south-east neighbors

                    for dx, dy in neighbors:
                        # does neigbor even exist?
                        if x + dx < 0 or y + dy < 0:
                            continue  # negative index
                        try:
                            # v = Game.dungeon[pz][y + dy][x + dx].fov
                            t = Game.dungeon[pz][y + dy][x + dx]
                        except IndexError:
                            continue
                        # is neighbor a tile AND visible?
                        if isinstance(t, Floor) and t.fov:
                            # ok, found a visible floor tile neighbor. now let's make this wall
                            # visible as well
                            Game.dungeon[pz][y][x].fov = True
                            Game.dungeon[pz][y][x].explored = True
                            break  # other neighbors are irrelevant now

    def move(self, monster, dx, dy):
        """
        move the monster instance (hero) through the dungeon, if possible
        assumes that the dungeon is surrounded by an outer wall
        hero can open a closed door if he has a spare key
        hero can strike at monster, monster can strike at hero
        """
        target = Game.dungeon[monster.z][monster.y + dy][monster.x + dx]
        legal = True  # we assume it is possible to move there
        text = []
        # if isinstance(target, Wall):  # same as target.__class__.__name__
        #    legal = False
        if not isinstance(target, Door):
            if target.block_movement:
                legal = False
        if isinstance(target, Door) and target.closed:
            legal = False
            if isinstance(monster, Player):
                text.append("You run into a locked door")
                keys = len(
                    [
                        i
                        for i in Game.items.values()
                        if i.backpack and isinstance(i, Key)
                    ]
                )
                if not target.locked:
                    text.append("You open the door withou using a key")
                    target.open()
                elif keys <= 0:
                    text.append("You need to find a key to open this door")
                else:
                    text.append("You open the door but loose a key")
                    target.open()  # open the door
                    for i2 in Game.items.values():
                        if i2.backpack and isinstance(i2, Key):
                            break  # found a suitable key to use & destroy
                    del Game.items[i2.number]  # destroy key
        if not legal:
            dx, dy = 0, 0
            if isinstance(monster, Player):  # only the player creates text msg
                text.append("Ouch! move not possible")
        else:
            # check for fight with monsters / players
            for m in [
                m
                for m in Game.zoo.values()
                if m.z == monster.z
                and m.number != monster.number
                and m.friendly != monster.friendly
                and m.hp > 0
                and m.x == monster.x + dx
                and m.y == monster.y + dy
            ]:
                dx, dy = 0, 0
                text.extend(fight(monster, m))
                break  # maximum one monster per tile possible
        # ------------------
        monster.x += dx
        monster.y += dy
        return text

    def close_door(self):
        Game.turn_number += 1
        """player tries to close a (hopefully nearby) door"""
        # standing next to an open door?
        hero = self.player
        text = []
        for (vx, vy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            tile = Game.dungeon[hero.z][hero.y + vy][hero.x + vx]
            if isinstance(tile, Door) and not tile.closed:
                tile.close()
                text.append("You close the open door")
                self.calculate_fov()
                break
        else:
            text.append("You must stay next (cardinal directions) to an open door")
        return text

    def climb_up(self):
        Game.turn_number += 1
        # climb up stairs to previous level (if standing on stairs)
        hero = self.player
        text = []
        if isinstance(Game.dungeon[hero.z][hero.y][hero.x], StairUp):
            hero.z -= 1  # deeper down -> bigger z
            Game.effects = {}  # clear all effects
            text.append("You climb one level up")
            # self.make_empty_effect_map()
            self.calculate_fov()

        else:
            text.append("You must stay on a stair up to use this command")
        return text

    def climb_down(self):
        Game.turn_number += 1
        # climb down stairs to next level (if standing on stairs)
        hero = self.player
        text = []
        if isinstance(Game.dungeon[hero.z][hero.y][hero.x], StairDown):
            hero.z += 1  # deeper down -> bigger z
            Game.effects = {}  # clear all effects
            text.append("You climb one level down")
            # self.make_empty_effect_map()
            self.calculate_fov()
        else:
            text.append("You must stay on a stair down to use this command")
        return text

    def eat(self):
        food = [i for i in Game.items.values() if isinstance(i, Food) and i.backpack]
        if len(food) == 0:
            return ["you have no food in your backpack"]
        # we have food :-)
        myfood = food[0]
        quality = myfood.food_value  # 1,2 or 3
        self.player.hp += myfood.food_value
        del Game.items[myfood.number]
        return [f"you eat food and regain {quality} hp"]

    def turn(self, dx, dy):
        """the player makes a new turn (including move command)"""
        Game.turn_number += 1
        text = []
        hero = Game.player
        #hero.update()
        # tile = Game.dungeon[hero.z][hero.y][hero.x]
        # ------- update all buffs -----
        # ------ update buffs of each monster -----
        for m in [m for m in Game.zoo.values() if m.z == hero.z and m.hp >0]:
            for b in m.buffs:
                b.update()
            m.buffs = [b for b in m.buffs if b.active]
            print(m, m.buffs)
        # --------- move the hero --------------
        text.extend(self.move(hero, dx, dy))  # test if move is legal and move
        # found stair?
        tile = Game.dungeon[hero.z][hero.y][hero.x]
        if isinstance(tile, StairDown):
            text.append(
                "You found a stair down. You can use the 'climb down' command [>] now"
            )
        if isinstance(tile, StairUp):
            text.append(
                "You found a stair up. You can use the 'climb up' [<] command now"
            )
        # give hint when next to a door (all 8 directions)
        for (nx, ny) in (
            (0, -1),
            (1, -1),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
        ):
            tile2 = Game.dungeon[hero.z][hero.y + ny][hero.x + nx]
            if isinstance(tile2, Door) and not tile2.closed:
                text.append(
                    "You found an open door. You can press [c] to close it (re-opening possible without key)"
                )
            # ---- detecting nearby traps ----
            for t in [
                t
                for t in Game.items.values()
                if t.z == hero.z
                and isinstance(t, Trap)
                and t.x == hero.x + nx
                and t.y == hero.y + ny
            ]:
                if not t.detected:
                    if t.calculate_detect():
                        t.detected = True
                        t.effect_detected()
        # ------- checking of standing south of a terminal -----
        if hero.y > 0:
            north = Game.dungeon[hero.z][hero.y - 1][hero.x]
            if isinstance(north, Terminal):
                text.append("press e to activate the terminal")
        # ------------- iterating over (damage) effects at player position ------
        # for e in [e for e in Game.effects.values() if e.tx == hero.x and e.ty == hero.y]:
        #    text.append(f"You suffer {e.damage} {e.__class__.__name__} damage")
        #    Flytext(tx=e.tx, ty=e.ty, text = f"- {e.damage} hp", color=(222,0,0), fontsize=32)

        # triggering a trap (traps are items) or
        # (auto)picking up item at current position
        # items = [
        #    i
        #    for i in Game.items.values()
        #    if i.z == hero.z and i.x == hero.x and i.y == hero.y and not i.backpack
        # ]#

        # ------------ iterate over items at player position --------------------
        for i in [
            i
            for i in Game.items.values()
            if i.z == hero.z and i.x == hero.x and i.y == hero.y and not i.backpack
        ]:
            #  ----------------- trap ------------------------
            if isinstance(i, Trap):
                damage = i.calculate_damage()
                hero.hp -= damage
                i.detected = True
                text.append(f"You trigger a trap and loose {damage} hp.")
                i.effect_trigger(
                    damage
                )  # skull and bones effect from trap, -hp flysprite
                # delete trap?
                if i.calculate_destroy():
                    text.append("the trap is destroyed")
                    del Game.items[i.number]
                else:
                    text.append("the trap is still active! Move away from here!")

            else:
                # ---------------- non-trap, item to pickup ------------------
                text.append(f"you pick up: {type(i).__name__}")
                i.backpack = True
                ## create Bubble effect here
                i.pickupeffect()

        # move the Monsters (and let monsters shoot at player)
        for m in [
            m
            for m in Game.zoo.values()
            if m.number != hero.number and m.z == hero.z and m.hp > 0
        ]:
            dxm, dym = m.ai()
            text.extend(self.move(m, dxm, dym))

        # ---- calculate if player suffer from monster shooting ----
        # ------------- iterating over (damage) effects at player position ------
        for e in [
            e for e in Game.effects.values() if e.tx == hero.x and e.ty == hero.y
        ]:
            damage = e.damage
            text.append(f"You suffer {damage} {e.__class__.__name__} damage")
            e.text_effect(damage)
            hero.hp -= e.damage
        # cleanup code, remove dead monsters:
        for m in [m for m in Game.zoo.values() if m.hp <= 0]:
            if m.number == hero.number:
                # draw(hero.z)  # one last time draw the dungeon
                # c.print("You are dead")
                text.append("You are dead")
                Game.running = False
                return text
            del Game.zoo[m.number]

        # ------- burning oil -------
        # create flames from burning oil
        for y, line in enumerate(Game.dungeon[hero.z]):
            for x, t in enumerate(line):
                if isinstance(t, Oil) and t.burning:
                    Fire(tx=x, ty=y, max_age=1)

        # spread fire to other oil
        for y, line in enumerate(Game.dungeon[hero.z]):
            for x, t in enumerate(line):
                if isinstance(t, Oil) and t.burning:
                    for dx, dy in [
                        (0, -1),
                        (1, -1),
                        (1, 0),
                        (1, 1),
                        (0, 1),
                        (-1, 1),
                        (-1, 0),
                        (-1, -1),
                    ]:
                        try:
                            t2 = Game.dungeon[hero.z][y + dy][x + dx]
                        except IndexError:
                            continue
                        if isinstance(t2, Oil) and not t2.burning:
                            t2.burning = True

        # ---- Fire on Oil makes Oil burning
        for e in Game.effects.values():
            if isinstance(e, Fire):
                t = Game.dungeon[hero.z][e.ty][e.tx]
                if isinstance(t, Oil) and not t.burning:
                    if random.random() < 0.2:  # chance to ignite
                        t.burning = True

        # ---------------------------
        self.calculate_fov()
        return text


class Effect:
    """a temporary effect (Smoke, Fire, Water, Wind, Oil, etc)
    can not be  picked up, and needs an underlaying dungoen structure
    (usually floor).
    Effects have no z coordinate. instead everytime when hero climb up or down stairs
    a new empty dictionary Game.effects={} is created
    Therefore, effects are not persistent when the player change levels by stairs
    Unlike Monsters, Effects do not block the players movement,
    but usually cause harm (hp loss) when player enters a tile with an active effect
    Effects may be temporary (lifetime only a couple of turns)
    Effects may spawn other effects ( big flame spawn little flame after some turn )
    Effects may be swawned by emittors ( automatic fireball/dart thrower etc).
    Effects interchange with each other: (fire+Water->Steam)
    Effects influence Field of View (fov) -> Smoke blocks sight, Wind blocks shooting etc.
    Effects may genearte a Sprite with the same effectnumber for reference
    """

    pictures = []  # for animation
    anim_cycle = 6  # how many pictures per second the animation should display
    wobble = False  # if effect dances around center of tile each frame some pixel. can be False or Tuple(x,y)
    damage = 0  # fixed damage, overwrite by child classes

    @classmethod
    def create_pictures(cls):
        pass

    def __init__(self, tx, ty, age=0, max_age=None, dx=0, dy=0):
        self.number = Game.effectnumber
        Game.effectnumber += 1
        Game.effects[self.number] = self
        self.background = pygame.Surface(
            (Viewer.gridsize[0], Viewer.gridsize[1])
        )  # background rect from Viewer
        self.tx = tx  # tile x
        self.ty = ty  # tile y
        self.px, self.py = 0, 0  # pixel coordinate of topleft corner
        self.fov = False
        self.dx, self.dy = dx, dy  # delta movement in tiles per turn
        # self.born = Game.turn_number + age         # effect appears as soon as age reach 0
        # self.age = Game.turn_number - self.born   #
        self.age = age  # age in turns
        self.seconds = 0  # age in seconds
        self.max_age = max_age  # effect disappears when age reaches max_age +1
        self.destroy = False
        self.kill_on_contact_with_wall = (
            True  # when effects wanders around and hit a wall-Destroy
        )
        # self.char = "?"
        # self.text = "unknown effect"
        # self.fgcolor = (25,25,25)
        self.light_radius = (
            0  # if > 0 then the effect itself emits light (flame, fireball etc)
        )

    def next_turn(self):
        # self.age = Game.turn_number - self.born
        self.age += 1
        # if self.max_age is not None and self.age > self.max_age:
        if self.max_age is not None and self.age > self.max_age:
            self.destroy = True
        self.tx += self.dx
        self.ty += self.dy
        # kill when effects leave level limit
        # print("level:", len(Game.dungeon[Game.player.z][0]), "x", len(Game.dungeon[Game.player.z]) )
        if self.tx < 0 or self.tx >= len(Game.dungeon[Game.player.z][0]):
            self.destroy = True
        if self.ty < 0 or self.ty >= len(Game.dungeon[Game.player.z]):
            self.destroy = True
        # kill when effect reaches a wall
        if self.kill_on_contact_with_wall:
            try:
                in_wall = isinstance(
                    Game.dungeon[Game.player.z][self.ty][self.tx], Wall
                )
            except IndexError:
                in_wall = True
            if in_wall:
                self.destroy = True

    def fovpicture(self, delta_t):
        """like sprite update -> expect time pased since last frame in seconds
        returns one of the pictures in self.pictures to update the animation"""
        pics = len(
            self.pictures
        )  # bacuase of scope, this works for classvariables of subclasses
        if pics == 0:
            return None
        self.seconds += delta_t
        i = int(self.seconds / (1 / self.anim_cycle) % pics)  #
        return self.pictures[i]

    def text_effect(self, damage):
        Flytext(
            tx=self.tx,
            ty=self.ty,
            text=f"{self.__class__.__name__}: -{damage} hp",
            color=(222, 0, 0),
            fontsize=32,
        )


class Fire(Effect):
    pictures = []
    char = "\U0001F525"  # Flames "*"
    # char = "\u2668" # hot springs
    wobble = (1, 1)
    # text = "Fire"
    fgcolor = (255, 0, 0)  # for panelinfo
    damage = 4

    @classmethod
    def create_pictures(cls):
        """star changes color wildley between red and yellow"""
        colorvalues = list(range(128, 256, 16))
        random.shuffle(colorvalues)
        for c in colorvalues:
            Fire.pictures.append(make_text(Fire.char, (255, c, 0), font=Viewer.font2))


class Water(Effect):
    pictures = []
    wobble = (1, 1)
    char = "\U0001F30A"  # "#"\u2248"  # double wave instead of "~"
    fgcolor = (0, 0, 255)
    anim_cycle = 4
    damage = 3

    @classmethod
    def create_pictures(cls):
        colorvalues = list(range(64, 256, 32))
        colorvalues.extend(list(range(255, 63, -32)))
        for c in colorvalues:
            pic = make_text(Water.char, (0, 0, c))
            # if c % 2 == 0:  # the first half values (ascending)
            Water.pictures.append(pic)
            # else:  # the second half (descending)            x     y
            #    Water.pictures.append(pygame.transform.flip(pic, False, True))


class Flash(Effect):
    pictures = []  # necessary!
    char = "\u26A1"
    fgcolor = (0, 200, 200)  # cyan
    anim_cycle = 25  # so many pictures per second
    damage = 2

    @classmethod
    def create_pictures(cls):
        """create a spiderweb of withe-blue lines, cracling from the center of tile to it's edge"""
        pic1 = make_text("\u26A1", (0, 0, 255))
        pic2 = make_text("\u26A1", (220, 220, 255))
        pic3 = pygame.transform.flip(pic1, True, False)
        pic4 = pygame.transform.flip(pic2, True, False)
        cls.pictures = [pic1, pic2, pic3, pic4]
        # return


class Structure:
    """a structrue can not move and can not be picked up
    structures do not have a x,y,z coordinate because they
    exist only in the dungeon array. the position inside
    the array equals to x,y. See Wall class docstring for detecting neighbors
    expcets create_pictures to be called with list of neighboring tiles as arguments
    """

    fgcolor = (0, 150, 0)
    block_sight = False
    block_movement = False
    block_shooting = False
    nesw_tile = None  # if this is a char, fill self.nesw with True for north, east, south, west neigbors
    exploredpic = None  # will be overwritten by create_pictures
    fovpic = None  # will be overwritten by create_pictures
    char = "?"  # simple char to use for rendering if nothing else is given in create_pictures

    # @classmethod
    # def create_pictures(cls, neighbor_list):
    #    cls.exploredpic = make_text(cls.char, Viewer.explored_fgcolor)
    #    cls.fovpic = make_text(cls.char, cls.fgcolor)

    # def exploredpicture(self):
    #    return self.exploredpic

    # def fovpicture(self):
    #    return self.fovpic

    def __init__(self):
        self.explored = False  # stay visible on map, but with fog of war
        self.fov = False  # currently in field of view of player?
        # self.char = None  # for textual representation btw for make_text(char)
        # self.nesw = nesw  # neighboring tiles of the same structure, . tuple of 4 boools: north, east, south, west

    def create_pictures(self, neighborlist=None, fontsize=48, mono=False):
        self.exploredpic = make_text(
            self.char, Viewer.explored_fgcolor, fontsize=fontsize, mono=mono
        )
        self.fovpic = make_text(self.char, self.fgcolor, fontsize=fontsize, mono=mono)


class Wall(Structure):
    """walls have a specail char depending on neighboring walls
    Viewer.load_images calls once Wall.create_pictures()
    Wall.create_pictures fill the exploredpictures and fovpictures dicts with the correct bitmaps
    by calculating the picture according to its neighboring tiles
    to get the correct bitmap to blit
    """

    # use font instead of freetype so that bloxdrawing chars are better centered (no need to calculate center for each box tile)
    fgcolor = (0, 150, 0)
    block_sight = True
    block_movement = True
    block_shooting = True
    char = "#"
    # nesw_tile = "#"  # wall
    # exploredpictures = {}
    # fovpictures = {}
    lookup = {
        (True, False, True, False): "\u2551",  # vertical
        (False, True, False, True): "\u2550",  # horizontal
        (False, True, True, False): "\u2554",  # L east-south
        (False, False, True, True): "\u2557",  # L south-west
        (True, True, False, False): "\u255A",  # L north-east
        (True, False, False, True): "\u255D",  # L north-west
        (True, True, True, False): "\u2560",  # T without west
        (True, False, True, True): "\u2563",  # T without east
        (False, True, True, True): "\u2566",  # T without north
        (True, True, False, True): "\u2569",  # T without south
        (True, True, True, True): "\u256C",  # crossing
        (False, False, False, False): "\u25A3",  # no neighbors
        (False, False, True, False): "\u2551",  # "\u2565",  # terminate from south
        (False, False, False, True): "\u2550",  # "\u2561",  # terminate from west
        (False, True, False, False): "\u2550",  # "\u255E",  # terminate from east
        (True, False, False, False): "\u2551",  # "\u2568",  # terminate from north
    }

    def create_pictures(self, list_of_neighbors):
        # list contains 8 neighbors, but only north, east, south, west are used for lookup
        # check how many of them are Wall:
        # walls = [False, False, False, False]
        # for i in (0,2,4,6):
        #    try:
        #        n = list_of_neighbors[i]
        #    except IndexError:
        #        continue
        #    if isinstance(n, Wall):
        #        walls[i//2] = True

        # walls = tuple(
        #    [True if isinstance(e, Wall) else False for e in list_of_neighbors]
        # )  # convert list into tuple for better lookup
        walls = [False, False, False, False]
        for i in (0, 1, 2, 3):
            if list_of_neighbors[i] is None:
                continue
            for stru in [Wall, Door, Glass]:
                if isinstance(list_of_neighbors[i], stru):
                    walls[i] = True
        walls = tuple(walls)
        # print(list_of_neighbors, "->", walls)
        self.char = self.lookup[walls]
        super().create_pictures(fontsize=Viewer.wallfontsize, mono=True)
        # self.exploredpic = make_text(self.char, Viewer.explored_fgcolor)
        # self.fovpicture = make_text(self.char, self.fgcolor)


class Floor(Structure):
    char = " "


class Oil(Structure):
    char = ":"
    fgcolor = (87, 71, 31)  # brown
    block_sight = False
    block_movement = False
    block_shooting = False

    def __init__(self):
        super().__init__()
        self.burning = False


class Terminal(Structure):
    char = "\U0001F4BB"
    fgcolor = (100, 100, 100)  # grey
    block_sight = False
    block_movement = True
    block_shooting = False

    def create_pictures(self, neighbors):
        super().create_pictures(fontsize=Viewer.fontsize)

    def effect_download(self):
        # Game.player.downloads += 1
        d = Download(Game.player.x, Game.player.y, Game.player.z)
        d.backpack = True
        zerostring = list("010101010101010101010")
        for t in range(0, -12, -1):
            random.shuffle(zerostring)
            Flytext(
                tx=Game.player.x,
                ty=Game.player.y - 1,
                text="".join(zerostring),
                color=(0, 200, 0),
                bgcolor=(1, 1, 1),
                age=t * 0.3,
                max_age=5,
                alpha_start=255,
                alpha_end=64,
                fontsize=32,
                move=pygame.math.Vector2(0, -75),
            )


class Door(Structure):
    """locked doors can be opened by keys.
    doors can be closed again by player, but not locked again.
    by default, doors are locked"""

    # USE font instead of freetype so that doors get not expanded (ugly)
    fgcolor = (140, 100, 0)
    nesw_tile = "#"  # wall. a door can only be between walls

    def __init__(self):
        super().__init__()
        # if nesw[0] and nesw[2]:  # wall north and south
        #    self.char = "|" #2502
        # elif nesw[1] and nesw[3]:  # wall east and west
        #    self.char = "-" #2500
        self.closed = True
        self.block_sight = True
        self.block_movement = True
        self.block_shooting = True  # set false for grille door etc.
        self.locked = True  # key is needed to open
        self.vertical = False
        self.horizontal = False

    def create_pictures(self, list_of_neighbors):
        # self.list_of_neighbors = list_of_neighbors
        # doors can be vertical or horizontal, depending on neighboring tiles
        # only nesw neigbors are used for calculation
        # assumes that a door has either north-south walls / doors or east / west
        # assumes that a door is not a corner door -> no diagonal movement
        walls = [False, False, False, False]
        for i in (0, 1, 2, 3):
            if list_of_neighbors[i] is None:
                continue
            for struc in [Wall, Door, Glass]:
                if isinstance(list_of_neighbors[i], struc):
                    walls[i] = True
        if walls[0] and walls[2]:
            self.vertical = True  # north and south neighbor is wall/ other door
        elif walls[1] and walls[3]:
            self.horizontal = True  # west and east neighbor is wall / other door
        elif walls[0] or walls[2]:
            self.vertical = True
        elif walls[1] or walls[3]:
            self.horizontal = True
        else:
            raise ValueError("strange position of Door", list_of_neighbors)
        if self.horizontal:
            self.char = "\u2500"  # ""-"
        elif self.vertical:
            self.char = "\u2502"  # "|"
        super().create_pictures(fontsize=Viewer.fontsize)

    def open(self):
        self.closed = False
        self.char = "."
        self.block_sight = False
        self.block_movement = False
        self.block_shooting = False
        self.locked = False
        super().create_pictures(fontsize=Viewer.fontsize)

    def close(self):
        # if self.nesw[0] and self.nesw[2]:  # wall north and south
        #    self.char = "|"
        # elif self.nesw[1] and self.nesw[3]:  # wall east and west
        #    self.char = "-"
        self.closed = True
        self.locked = False  # key is not needed again
        self.block_sight = True
        self.block_movement = True
        self.block_shooting = True  # set false for grille door etc.
        if self.horizontal:
            self.char = "\u2500"  # ""-"
        elif self.vertical:
            self.char = "\u2502"  # "|"
        super().create_pictures(fontsize=Viewer.fontsize)


class Glass(Structure):
    """looking through is possible, shooting and walking is not"""

    # USE font instead of freetype so that doors get not expanded (ugly)
    fgcolor = (200, 255, 250)  # cyan-white
    # nesw_tile = "#"  # wall neighbor tile
    block_sight = False
    block_movement = True
    block_shooting = True  # set false for grille door etc.

    def __init__(self):
        super().__init__()
        # calculate orintation of glass wall depending on north-east-south-west wall neighbors
        # if nesw[0] and nesw[2]:  # wall north and south
        #    self.char = "\u2502" #"|" # vertical
        # elif nesw[1] and nesw[3]:  # wall east and west
        #    self.char = "\u2500"  # horizontal
        # elif nesw[0] or nesw[2]:  # wall north or south
        #    self.char = "\u2502" #w"|"  # vertical
        # elif nesw[1] or nesw[3]:  # wall east or west
        #    self.char = "\u2500" # horizontal
        # else:
        #    self.char = "+"  # strange neighbors
        # self.closed = True
        self.vertical = False
        self.horizontal = False

    def create_pictures(self, list_of_neighbors):
        # only nesw neighbors are used for orientation of glass
        walls = [False, False, False, False]
        for i in (0, 1, 2, 3):
            if list_of_neighbors[i] is None:
                continue
            for stru in [Wall, Door, Glass]:
                if isinstance(list_of_neighbors[i], stru):
                    walls[i] = True

        if walls[0] and walls[2]:
            self.vertical = True  # north and south neighbor is wall/ other door
            self.char = "\u2502"  # ""|"
        elif walls[1] and walls[3]:
            self.horizontal = True  # west and east neighbor is wall / other door
            self.char = "\u2500"  # ""-"
        else:
            self.char = "+"
        super().create_pictures(fontsize=Viewer.fontsize)

    # @classmethod
    # def create_pictures(cls):
    #    cls.exploredpicture_v = make_text("\u2502", Viewer.explored_fgcolor, font=Viewer.font)
    #    cls.exploredpicture_h = make_text("\u2500", Viewer.explored_fgcolor, font=Viewer.font)
    #    cls.exploredpicture_cross = make_text("+", Viewer.explored_fgcolor, font=Viewer.font)
    #    cls.fovpicture_v = make_text("\u2502", cls.fgcolor, font=Viewer.font)
    #    cls.fovpicture_h = make_text("\u2500", cls.fgcolor, font=Viewer.font)
    #    cls.fovpicture_cross = make_text("+", cls.fgcolor, font=Viewer.font)


class StairDown(Structure):
    fgcolor = (150, 50, 90)  # dark pink
    char = "\u21F2"  # "\u21A7"  # downwards arrow from bar


class StairUp(Structure):
    fgcolor = (60, 200, 200)  # cyan
    char = "\u21F1"  # "# "\u21A5"  # upwards arrow from bar


class Item:
    """Items can be picked up by the player
    if carried by player, the items x,y,z attributes are meaningless
    and the items backpack attribute must be set to True"""

    pictures = []
    char = "?"  # for panelinfo
    fgcolor = (0, 255, 0)  # for panelinfo
    font = 2

    @classmethod
    def create_pictures(cls):  # make the char into a picture
        if cls.font == 2:
            font = Viewer.font2
        elif cls.font == 1:
            font = Viewer.font
        cls.pictures.append(make_text(cls.char, cls.fgcolor, font=font))

    def __init__(self, x, y, z):
        self.number = Game.itemnumber
        Game.itemnumber += 1
        Game.items[self.number] = self
        self.backpack = False  # carried in players backpack?
        self.x = x  # if not carried by player
        self.y = y
        self.z = z

    def flytext_and_bubbles(self, ftext=None, number_of_bubbles=None):
        if ftext is None:
            ftext = self.__class__.__name__
        if number_of_bubbles is None:
            number_of_bubbles = 5
        px, py = Viewer.tile_to_pixel((self.x, self.y))
        posvector = pygame.math.Vector2(px, py)
        yspeed = random.randint(-20, -5)
        yacc = 1.0 + random.random() * 0.15
        Flytext(
            pos=posvector,
            move=pygame.math.Vector2(0, yspeed),
            acceleration_factor=yacc,
            text=ftext,
            color=self.fgcolor,
            fontsize=32,
        )
        for _ in range(number_of_bubbles):
            posvector = pygame.math.Vector2(
                px, py
            )  # its necessary. comment out this line for funny effect
            m = pygame.math.Vector2(random.random() * 20 + 25)  # speed
            m.rotate_ip(random.randint(0, 360))
            # x,y = Viewer.tile_to_pixel((self.x,self.y))
            Bubble(pos=posvector, color=self.fgcolor, move=m)

    def pickupeffect(self):
        self.flytext_and_bubbles()

    def fovpicture(self):
        return self.pictures[0]


class Coin(Item):
    pictures = []
    char = "\U0001F4B0"  # bag of money "#  "$"
    fgcolor = (255, 255, 0)  # yellow

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.value = random.choice((1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 5, 5, 10))

    def pickupeffect(self):
        self.flytext_and_bubbles(
            ftext=f"found {self.value} gold!", number_of_bubbles=self.value * 5
        )


class Key(Item):
    pictures = []
    fgcolor = (255, 255, 0)
    char = "\U0001F511"  # key #"k"


class Download(Item):
    pictures = []
    fgcolor = (0, 128, 0)
    char = "\U0001F4BE"  # diskette


class Arrow(Item):
    pictures = []
    fgcolor = (160, 80, 40)  # brown
    char = "\u27B3"
    font = 1  # symbola


class Trap(Item):
    pictures = []
    fgcolor = (128, 128, 128)
    char = "\U0001F4A3"  # bomb # 2620"  # skull and bones

    @classmethod
    def create_pictures(cls):  # make the char into a picture
        cls.pictures.append(make_text(cls.char, cls.fgcolor, font=Viewer.font2))

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.damage = (
            "2d4"  # 2 x 4-sided dice without re-roll -> result between 4 and 8
        )
        self.name = "spike trap"
        self.detected = False
        self.disarmed = False
        self.chance_to_destroy = 0.4
        self.chance_to_detect = 0.33

    def calculate_destroy(self):
        return random.random() < self.chance_to_destroy

    def calculate_detect(self):
        return random.random() < self.chance_to_detect

    def calculate_damage(self):
        """damage the traps inflicts on player (or Monster)"""
        if self.disarmed:
            return 0
        return throw_dice(*dice_from_string(self.damage))
        # return       #random.randint(1, 6)

    def effect_detected(self):
        Flytext(tx=self.x, ty=self.y, text="trap detected")

    def effect_trigger(self, damage):
        px, py = Viewer.tile_to_pixel((self.x, self.y))
        # white skull on black ground, fading out
        Flytext(
            pos=pygame.math.Vector2(px, py),
            move=pygame.math.Vector2(0, -1),
            text="\u2620",
            color=(255, 255, 255),
            bgcolor=(2, 2, 2),
            fontsize=100,
            acceleration_factor=1.01,
            max_age=0.5,
            alpha_start=255,
            alpha_end=0,
        )
        # red hp, flying up
        Flytext(
            pos=pygame.math.Vector2(px, py),
            move=pygame.math.Vector2(0, -20),
            text=f"Trap: -{damage} hp",
            color=(200, 0, 0),
            fontsize=32,
            acceleration_factor=1.00,
            max_age=1,
        )


class Food(Item):
    pictures = []
    char = "\U0001F35C"  # steam soup   # coffe cup:"\u2615"
    fgcolor = (200, 0, 200)

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.food_value = random.randint(1, 3)

    def pickupeffect(self):
        lookup = {1: "edible food", 2: "good food", 3: "fantastic food"}
        self.flytext_and_bubbles(lookup[self.food_value], self.food_value * 5)


class Buff:
    """stat-changing (de)buff that apply to Player or Monster"""

    pictures = []
    fgcolor = (0, 200, 0)
    number = 0
    max_age = 4
    mana_cost = 0   # initial cost
    mana_upkeep = 0 # cost per turn
    hp_change = 0
    unique = False
    char = "?"

    def __init__(self, monsternumber  ):
        if self.unique:
            Game.zoo[monsternumber].buffs = [
                b for b in Game.zoo[monsternumber].buffs
                if not isinstance(b, self.__class__)
            ]


        self.number = Buff.number  # unique number
        self.monsternumber = monsternumber
        Buff.number += 1
        self.age = 0
        Game.zoo[self.monsternumber].buffs.append(self)
        self.active = True

    @classmethod
    def create_pictures(cls):
        pic = make_text(text=cls.char, fgcolor=cls.fgcolor,
                        font=Viewer.font2)
        pic = pygame.transform.scale(pic,
                                     (Viewer.gridsize[0]//2,
                                      Viewer.gridsize[1]//2))
        cls.pictures.append(pic)

    def update(self):
        """check if buff cancel itself by lack of mana / or reaching max_age"""
        # check if monster is still in zoo? not necessary?
        m = Game.zoo[self.monsternumber]
        # ----- aging ----
        self.age += 1
        if self.age >= self.max_age:
            self.active = False
        if self.mana_upkeep > Game.zoo[self.monsternumber].mana:
            self.active = False
        m.mana -= self.mana_upkeep
        m.hp += self.hp_change
        if self.hp_change != 0:
            Flytext(tx=m.x, ty=m.y, fontsize=12,
                    text=f"{self.__class__.__name__} {self.hp_change} hp")

class Burning(Buff):
    pictures = []
    fgcolor = (255, 75, 0)
    mana_upkeep = False
    hp_change = -1
    max_age = 4
    unique = False
    char = "\U0001F525"



class Monster:
    """Monsters can move around"""

    pictures = []
    fgcolor = (255, 0, 0)  # red
    char = "\U0001F620"  # angry blob  "\U0001F608"  # angry emoticon
    ai_dx = (0, 0, 0, 1, -1)
    ai_dy = (0, 0, 0, 1, -1)

    @classmethod
    def create_pictures(cls):
        pic = make_text(cls.char, cls.fgcolor, font=Viewer.font2)
        cls.pictures.append(pic)

    @classmethod
    def ai(cls):
        return random.choice(cls.ai_dx), random.choice(cls.ai_dy)

    def __init__(self, x, y, z):
        self.number = Game.monsternumber  # get unique monsternumber
        Game.monsternumber += 1  # increase global monsternumber
        Game.zoo[self.number] = self  # store monster into zoo
        self.x = x
        self.y = y
        self.z = z
        self.buffs = []
        self.hp = 10  # this MUST be an instance attribute because each monster has individual hp
        # self.fgcolor = (255,0,0)# "red"
        self.friendly = False  # friendly towards player?
        # self.char = "M"  # Monster

    def update(self):
        """called once per game-turn for each monster"""
        pass

    def fovpicture(self):
        # print("returning fovpicture of", self.__class__.__name__)
        return self.pictures[0]


class Snake(Monster):
    pictures = []
    fgcolor = (23, 255, 0)  # light green
    char = "\U0001F40D"  # snake "#"\u046E"
    ai_dx = (0, 1, -1)
    ai_dy = (0, 1, -1)


class FireDragon(Monster):
    pictures = []
    fgcolor = (255, 90, 0)  # orange
    char = "\U0001F409"
    p_shoot = 0.2  # probabiltiy to shoot at player
    p_hunt = 0.8  # probability to move towards player

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.friendly = False  # friendly towards player?

    def ai(self):
        # ---fire spitting---
        if Game.dungeon[self.z][self.y][self.x].fov:  # visible?
            # print("FireDragon spitting...")
            if random.random() < self.p_shoot:
                # print("Fire spit!...")
                # spit fire if line-of-shight for shooting is True (can shoot)
                if calculate_line(
                    (self.x, self.y),
                    (Game.player.x, Game.player.y),
                    Game.player.z,
                    modus="shoot",
                ):
                    # print("feuerspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:6]:
                        Fire(f[0], f[1], max_age=1)
        # else:
        # print("firedragon not in fov")

        dx = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        dy = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        return dx, dy


class SkyDragon(Monster):
    pictures = []
    fgcolor = (0, 0, 200)  # cyan
    char = "\U0001F479"  # japanese ogre "#"W" #char = "S"

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.friendly = False  # friendly towards player?

    def oldai(self):
        # ---fire spitting---
        if Game.dungeon[self.z][self.y][self.x]:  # visible?
            if random.random() < 0.1:
                can_shoot = calculate_line(
                    (self.x, self.y),
                    (Game.player.x, Game.player.y),
                    Game.player.z,
                    modus="shoot",
                )
                if can_shoot:
                    # print("feuerspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:10]:
                        Flash(f[0], f[1], max_age=1)

        dx = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        dy = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        return dx, dy


class WaterDragon(Monster):
    pictures = []
    fgcolor = (0, 0, 255)  # blue
    char = "\U0001F419"  # octopus "#"W"

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 25
        self.friendly = False  # friendly towards player?

    def oldai(self):
        # ---water spitting---
        if Game.dungeon[self.z][self.y][self.x]:  # visible?
            if random.random() < 0.5:
                can_shoot = calculate_line(
                    (self.x, self.y),
                    (Game.player.x, Game.player.y),
                    Game.player.z,
                    modus="shoot",
                )
                if can_shoot:
                    # print("wasserspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:6]:
                        Water(f[0], f[1], max_age=3)

        dx = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        dy = random.choice(
            (
                0,
                0,
                0,
                1,
                -1,
            )
        )
        return dx, dy


class Player(Monster):
    pictures = []
    char = "\u263A"  # "\u263A"  #heart: "\u2665" # music:"\u266B"  # sun "\u2609" #thunderstorm: "\u2608" #lighting: "\u2607" # double wave: "\u2248"  # sum: "\u2211" 3stars:  "\u2042" # "@"
    fgcolor = (0, 0, 255)
    shield_upkeep = 1  # 1 mana per turn
    mana_regeneration = 0.1
    stamina_regeneration = 0.25
    shield_cost = 15  # mana cost to activate shield

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.hp_full = 50
        self.mana = 100
        self.mana_full = 100
        self.stamina = 100
        self.stamina_full = 100
        self.level = 1
        self.xp = 0
        self.xp_full = 100
        # self.mana_regeneration = 0.1
        self.friendly = True
        self.downloads = 0
        self.shield = False
        self.range_bonus = 1  # the higher, the better hit chance at big distance
        # self.backpack = [] # container for transported items

    def update(self):
        """called once per game turn"""
        if self.shield:
            self.mana -= self.shield_upkeep
            if self.mana < 1:
                Flytext(tx=self.x, ty=self.y, text="not enough mana for shield")
                self.shield = False
        # --- mana regeneration ----
        self.mana += self.mana_regeneration
        self.mana = between(self.mana, 0, 100)

    def arrow_damage(self):
        return throw_dice(*dice_from_string("2d6+2"))

    def arrow_hit_chance(self, distance):
        return "{:.1f}%".format((1 / distance * self.range_bonus) * 100)

    def arrow_hit(self, distance):
        p = 1 / distance * self.range_bonus
        roll = random.random()
        print("to hit chance:", p, "roll:", roll)
        return roll < p

    def shoot_arrow(self, target_tx, target_ty):
        """player want to shoot an arrow from his tile to tx,ty
        check if player has an arrow"""
        arrows = [i for i in Game.items.values() if isinstance(i, Arrow) and i.backpack]
        if len(arrows) == 0:
            # if not arrows:
            Flytext(tx=self.x, ty=self.y, text="No arrow!", fontsize=12)
            print("no arrow")
            return
        # Flytext(tx=self.x, ty=self.y, text="arrow!", color=(222, 0, 0))
        # ---- shoot the actual arrow ---
        # -------- shoot blue circles into each square until cursor-------
        # hier weitermachen
        points = get_line((self.x, self.y), (target_tx, target_ty))
        max_distance = (
            (self.x - points[-1][0]) ** 2 + (self.y - points[-1][1]) ** 2
        ) ** 0.5
        max_time = 1.0
        for point in points[1:]:
            ok = calculate_line((self.x, self.y), point, self.z, "shoot")
            if not ok:
                break
            distance = ((self.x - point[0]) ** 2 + (self.y - point[1]) ** 2) ** 0.5
            delay = distance / max_distance * max_time
            if ok:
                victims = [
                    v
                    for v in Game.zoo.values()
                    if v.z == self.z and v.x == point[0] and v.y == point[1]
                ]
                for v in victims:
                    if self.arrow_hit(distance):
                        damage = self.arrow_damage()
                        v.hp -= damage
                        Flytext(
                            tx=v.x,
                            ty=v.y,
                            text=f"dmg: -{damage}hp",
                            age=-delay,
                            fontsize=12,
                        )
                        print("arrow damage")
                    else:
                        Flytext(tx=v.x, ty=v.y, text="miss", age=-delay, fontsize=12)
                        print("miss")
                    # for _ in range(10):
                    # px, py = self.tile_to_pixel((point[0], point[1]))
                    # p = pygame.math.Vector2(px, py)
                    # Bubble(pos=p, age=-0.5)
        # ----- fly arrow from player to point! because flight-path may be blocked
        if point != points[1]:
            FlyingObject(
                start_tile=points[0], end_tile=point, picture=Arrow.pictures[0]
            )
            # ---- destroy arrow ----
            del Game.items[arrows[0].number]

    def toggle_shield(self):
        if self.shield:  # turn shield off
            self.shield = False
            Flytext(tx=self.x, ty=self.y, text="shield deactivated")
            return
        # turn shield on if enoug mana
        if self.mana <= 15:
            Flytext(tx=self.x, ty=self.y, text="not enough mana!")
            return
        # activate shield
        self.mana -= self.shield_cost
        self.shield = True
        Flytext(tx=self.x, ty=self.y, text="shield activated!")


class Viewer:
    width = 0
    height = 0
    midscreen = (0, 0)
    gridsize = (1, 1)
    panelwidth = 0
    logheight = 0
    hudheight = 0  # height of hud on top of screen, for displaying hitpoints etc
    fontsize = 0
    font = None
    monofont = None
    allgroup = None  # pygame sprite Group for all sprites
    explored_fgcolor = (0, 100, 0)
    explored_bgcolor = (10, 10, 10)
    panelcolor = (128, 128, 64)
    # tile coordinate of topleft corner of currently visible tile on screen
    toplefttile = [
        0,
        0,
    ]
    # tile coordinate of bottomright corner of currently visible tile on screen
    bottomrighttile = [
        0,
        0,
    ]
    images = {}
    radardot = [1, 1]

    # playergroup = None # pygame sprite Group only for players

    def __init__(
        self,
        width=800,
        height=600,
        gridsize=(48, 48),
        panelwidth=200,
        logheight=100,
        fontsize=128,
        wallfontsize=72,
        max_tiles_x=200,
        max_tiles_y=200,
    ):

        Viewer.width = width
        Viewer.height = height
        Viewer.gridsize = gridsize
        Viewer.panelwidth = panelwidth
        self.midradar = (Viewer.panelwidth // 2, Viewer.panelwidth // 2)
        Viewer.logheight = logheight
        Viewer.midscreen = (
            (width - panelwidth) // 2,
            (height - logheight - Viewer.hudheight) // 2,
        )
        Viewer.fontsize = fontsize
        Viewer.wallfontsize = wallfontsize
        Game.max_tiles_x = max_tiles_x
        Game.max_tiles_y = max_tiles_y

        # ---- pygame init
        pygame.init()
        # Viewer.font = pygame.font.Font(os.path.join("data", "FreeMonoBold.otf"),26)
        # fontfile = os.path.join("data", "fonts", "DejaVuSans.ttf")
        fontfile = os.path.join("data", "fonts", "Symbola605.ttf")
        fontfile2 = os.path.join("data", "fonts", "NotoEmoji-Regular.ttf")
        # fontfile = os.path.join("data", "fonts", "NotoEmoji-Regular.ttf")
        Viewer.monofontfilename = os.path.join("data", "fonts", "FreeMonoBold.otf")
        Viewer.font = pygame.freetype.Font(fontfile)  # Symbola605
        Viewer.font2 = pygame.freetype.Font(fontfile2)  # NotoEmoji-Regular
        # Viewer.monofont = pygame.freetype.Font(monofontfile)
        # Viewer.monofont = pygame.font.Font(monofontfile)

        # ------ joysticks init ----
        pygame.joystick.init()
        self.joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        for j in self.joysticks:
            j.init()
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.playtime = 0.0
        self.cursormode = False

        # ------ background images ------
        self.backgroundfilenames = []  # every .jpg or .jpeg file in the folder 'data'
        self.make_background()
        self.load_images()
        self.panelscreen = pygame.Surface(
            (Viewer.panelwidth, Viewer.height - Viewer.panelwidth)
        )
        self.radarscreen = pygame.Surface(
            (Viewer.panelwidth, Viewer.panelwidth)
        )  # square in topright corner
        self.logscreen = pygame.Surface(
            (Viewer.width, Viewer.height - Viewer.logheight)
        )
        self.loglines = []
        self.prepare_sprites()
        # ------ need Game instance ----
        self.g = Game()
        self.make_panel()
        self.make_radar()
        self.make_log()
        self.run()

    def load_images(self):
        """load image files once from data subdirectory and store them inside Viewer.images dictionary"""
        # ---- image map from stone soup dungeon crawl -----
        Viewer.images["main"] = pygame.image.load(
            os.path.join("data", "from_stone_soup", "main.png")
        ).convert_alpha()
        Viewer.images["bow"] = pygame.image.load(
            os.path.join("data", "skill_bow.png")
        ).convert_alpha()
        Viewer.images["bow"] = pygame.transform.scale(
            Viewer.images["bow"], Viewer.gridsize
        )
        Viewer.images["bow_no"] = Viewer.images["bow"].copy()
        pygame.draw.line(
            Viewer.images["bow_no"], (255, 0, 0), (0, 0), Viewer.gridsize, 5
        )
        pygame.draw.line(
            Viewer.images["bow_no"], (255,0,0), (Viewer.gridsize[0],0),(0, Viewer.gridsize[1]), 5
        )

        # --- sub-images from main.png:
        # tmp = pygame.Surface.subsurface(
        #    Viewer.images["main"], (808, 224, 22, 7)
        # )  # arrow
        # Viewer.images["arrow"] = pygame.transform.scale(tmp, (35, 8))

        # tmp = pygame.Surface.subsurface(
        #    Viewer.images["main"], (22, 840, 16, 16)
        # )  # flame1
        # Viewer.images["flame1"] = pygame.transform.scale(tmp, (32, 32))
        # tmp = pygame.Surface.subsurface(
        #    Viewer.images["main"], (40, 840, 16, 16)
        # )  # flame2
        # Viewer.images["flame2"] = pygame.transform.scale(tmp, (32, 32))
        # tmp = pygame.Surface.subsurface(
        #    Viewer.images["main"], (56, 840, 16, 16)
        # )  # flame3
        # Viewer.images["flame3"] = pygame.transform.scale(tmp, (32, 32))
        # ---- direct images ---
        # tmp = pygame.image.load(os.path.join("data", "goldchest.png")).convert_alpha()
        # Viewer.images["gold"] = pygame.transform.scale(tmp, (35, 35))

        # tmp = pygame.image.load(os.path.join("data", "old_key.png")).convert_alpha()
        # Viewer.images["key"] = pygame.transform.scale(tmp, (35, 35))

        # tmp = pygame.image.load(os.path.join("data", "food1.png")).convert_alpha()
        # Viewer.images["food"] = pygame.transform.scale(tmp, (35, 35))

        # image for structure tiles ( wall ) -> iterate over all subclasses of Structure and call cls.create_pictures()
        # for sc in Structure.__subclasses__():
        #    sc.create_pictures()
        # image creation for Effects:
        # print("creating effect pictures..")
        for sc in Effect.__subclasses__():
            # print(sc)
            sc.create_pictures()

        for sc in Item.__subclasses__():
            sc.create_pictures()
        for sc in Monster.__subclasses__():
            sc.create_pictures()
        for sc in Buff.__subclasses__():
            sc.create_pictures()

        Monster.create_pictures()  # twice??

    def make_radar(self):
        self.radarscreen.fill((0, 0, 0))  # fill black
        hero = Game.player
        midx = self.midradar[0] - int(Viewer.radardot[0] // 2)
        midy = self.midradar[1] - int(Viewer.radardot[1] // 2)
        for y, line in enumerate(Game.dungeon[hero.z]):
            for x, tile in enumerate(Game.dungeon[hero.z][y]):
                if not tile.explored:
                    continue
                elif isinstance(tile, Floor):
                    color = (50, 50, 50)
                elif isinstance(tile, Wall):
                    color = (0, 128, 0)  # mid green
                elif isinstance(tile, StairUp):
                    color = (0, 128, 128)
                elif isinstance(tile, StairDown):
                    color = (128, 0, 128)
                elif isinstance(tile, Door):
                    color = (0, 64, 0)
                else:
                    color = (255, 255, 0)  # alarm for unknow tile
                pygame.draw.rect(
                    self.radarscreen,
                    color,
                    (
                        midx - Viewer.radardot[0] * (-x + hero.x),
                        midy - Viewer.radardot[1] * (-y + hero.y),
                        Viewer.radardot[0],
                        Viewer.radardot[1],
                    ),
                )
        # -- monster
        for m in Game.zoo.values():
            # print("dungeonxy: ", len(Game.dungeon[hero.z][0]),len(Game.dungeon[hero.z]) )
            # print("mxyz", m.x, m.y, m.z, m)
            # print("dungeon line0", Game.dungeon[hero.z][0])
            # print("dungeon line1", Game.dungeon[hero.z][1])
            # print("len1", len(Game.dungeon[hero.z][1]))
            if m.hp > 0 and m.z == hero.z and Game.dungeon[hero.z][m.y][m.x].fov:
                pygame.draw.rect(
                    self.radarscreen,
                    m.fgcolor,
                    (
                        midx - Viewer.radardot[0] * (-m.x + hero.x),
                        midy - Viewer.radardot[1] * (-m.y + hero.y),
                        Viewer.radardot[0],
                        Viewer.radardot[1],
                    ),
                )

    def make_background(self):
        """scans the subfolder 'data' for .jpg files, randomly selects
        one of those as background image. If no files are found, makes a
        white screen"""
        try:
            for root, dirs, files in os.walk("data"):
                for file in files:
                    if file[-4:].lower() == ".jpg" or file[-5:].lower() == ".jpeg":
                        self.backgroundfilenames.append(os.path.join(root, file))
            random.shuffle(self.backgroundfilenames)  # remix sort order
            self.background = pygame.image.load(self.backgroundfilenames[0])

        except:
            print("no folder 'data' or no jpg files in it")
            self.background = pygame.Surface(self.screen.get_size()).convert()
            self.background.fill((255, 255, 255))  # fill background white

        self.background = pygame.transform.scale(
            self.background, (Viewer.width, Viewer.height)
        )
        self.background.convert()

    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        Viewer.allgroup = pygame.sprite.LayeredUpdates()  # for drawing with layers
        Viewer.visiblegroup = pygame.sprite.LayeredUpdates()
        # Viewer.allgroup = pygame.sprite.LayeredDirty()  # for drawing with layers
        Viewer.playergroup = (
            pygame.sprite.OrderedUpdates()
        )  # a group maintaining order in list
        Viewer.cursorgroup = pygame.sprite.Group()
        Viewer.bluegroup = pygame.sprite.Group()
        Viewer.flygroup = pygame.sprite.Group()
        # Viewer.effectgroup = pygame.sprite.Group() # dirtygroup?
        # self.bulletgroup = pygame.sprite.Group() # simple group for collision testing only
        # self.tracergroup = pygame.sprite.Group()
        # self.mousegroup = pygame.sprite.Group()
        # self.explosiongroup = pygame.sprite.Group()
        self.flytextgroup = pygame.sprite.Group()
        self.fxgroup = pygame.sprite.Group()  # for special effects

        # Mouse.groups = self.allgroup, self.mousegroup
        # Player.groups = self.allgroup, self.playergroup
        # Beam.groups = self.allgroup, self.bulletgroup
        TileCursor.groups = self.cursorgroup
        BlueTile.groups = self.bluegroup, self.allgroup
        VectorSprite.groups = self.allgroup
        # SpriteEffect.groups =  self.effectgroup
        Bubble.groups = self.allgroup, self.fxgroup  # special effects
        Flytext.groups = self.allgroup, self.flytextgroup, self.flygroup
        FlyingObject.groups = self.allgroup, self.flygroup
        # Explosion.groups = self.allgroup, self.explosiongroup
        # -------- create necessary sprites -----
        self.cursor = TileCursor()
        # self.cursor.visible = False

    def make_panel(self):
        # in topright corner of screen is the radarscreen: panelwidth  x panelwidth
        # the height of panelscreen is therefore Viewer.height - panelwidth
        self.panelscreen.fill(Viewer.panelcolor)
        write(
            self.panelscreen,
            "panel \u2566\u2569",
            5,
            0,
            color=(0, 0, 255),
            font_size=32,
            origin="topleft",
        )
        z = Game.player.z
        tiles_x = len(Game.dungeon[z][0])  # z y x
        tiles_y = len(Game.dungeon[z])
        # --- player stats ----
        keys = len(
            [i for i in Game.items.values() if isinstance(i, Key) and i.backpack]
        )
        gold = sum(
            [i.value for i in Game.items.values() if isinstance(i, Coin) and i.backpack]
        )
        food = len(
            [i for i in Game.items.values() if isinstance(i, Food) and i.backpack]
        )
        downloads = len(
            [i for i in Game.items.values() if isinstance(i, Download) and i.backpack]
        )
        # text = "{}   :{}    :{}".format(keys, gold, food)
        # --------- x,y,z,-------------
        text = f"turn {Game.turn_number} x:{Game.player.x} y:{Game.player.y} z:{z + 1} {tiles_x}x{tiles_y} "
        write(self.panelscreen, text, 5, 35, font_size=15)
        pygame.draw.line(
            self.panelscreen, (0, 0, 255), (0, 50), (Viewer.panelwidth, 50), 1
        )
        # ---------- status bars -------------
        # ----- red hp bar  ---------------------
        y = 55
        # write(self.panelscreen, "\u2665",5,170, color=(255, 0, 0),font_size=25, font=Viewer.font2)
        # write(self.panelscreen, "{:>3}".format(Game.player.hp), 25, 170, font_size=25, )
        pixelwidth = int(Game.player.hp / Game.player.hp_full * Viewer.panelwidth)
        pygame.draw.rect(
            self.panelscreen, Viewer.panelcolor, (0, y, Viewer.panelwidth, 25)
        )
        pygame.draw.rect(
            self.panelscreen, (222, 0, 0), (0, y, Viewer.panelwidth, 25), 2
        )
        pygame.draw.rect(self.panelscreen, (222, 0, 0), (0, y, pixelwidth, 25))
        write(
            self.panelscreen,
            f"hp: {Game.player.hp} / {Game.player.hp_full}",
            5,
            y + 2,
            font_size=20,
            color=(255, 255, 255),
        )
        # ------ blue mana bar --------------
        y = 80
        pixelwidth = int(Game.player.mana / Game.player.mana_full * Viewer.panelwidth)
        pygame.draw.rect(
            self.panelscreen, Viewer.panelcolor, (0, y, Viewer.panelwidth, 25)
        )
        pygame.draw.rect(
            self.panelscreen, (0, 0, 222), (0, y, Viewer.panelwidth, 25), 2
        )
        pygame.draw.rect(self.panelscreen, (0, 0, 222), (0, y, pixelwidth, 25))
        text = "mana: {} / {}".format(int(Game.player.mana), int(Game.player.mana_full))
        write(self.panelscreen, text, 5, y + 2, font_size=20, color=(255, 255, 255))
        # ----- yellow stamina bar --------
        y = 105
        pixelwidth = int(
            Game.player.stamina / Game.player.stamina_full * Viewer.panelwidth
        )
        pygame.draw.rect(
            self.panelscreen, Viewer.panelcolor, (0, y, Viewer.panelwidth, 25)
        )
        pygame.draw.rect(
            self.panelscreen, (222, 222, 0), (0, y, Viewer.panelwidth, 25), 2
        )
        pygame.draw.rect(self.panelscreen, (222, 222, 0), (0, y, pixelwidth, 25))
        text = "stamina: {} / {}".format(
            int(Game.player.stamina), int(Game.player.stamina_full)
        )
        write(self.panelscreen, text, 5, y + 2, font_size=20, color=(0, 0, 0))
        # --------white xp bar ---------------
        y = 130
        pixelwidth = int(Game.player.xp / Game.player.xp_full * Viewer.panelwidth)
        pygame.draw.rect(
            self.panelscreen, Viewer.panelcolor, (0, y, Viewer.panelwidth, 25)
        )
        pygame.draw.rect(
            self.panelscreen, (255, 255, 255), (0, y, Viewer.panelwidth, 25), 2
        )
        pygame.draw.rect(self.panelscreen, (255, 255, 255), (0, y, pixelwidth, 25))
        text = "lvl: {} xp: {} / {}".format(
            Game.player.level, Game.player.xp, Game.player.xp_full
        )
        write(self.panelscreen, text, 5, y + 2, font_size=20, color=(0, 0, 0))

        # ---------------------quick inventory with symbols and amount-----------------
        # ---- key, keys ---------------------------------
        # self.panelscreen.blit(Viewer.images["key"], (-5, 200))
        write(self.panelscreen, "\U0001F511", 5, 170, font_size=25, font=Viewer.font2)
        write(
            self.panelscreen,
            "{:>3}".format(keys),
            25,
            170,
            font_size=25,
        )
        # ---- gold sack, gold -----------------
        # self.panelscreen.blit(Viewer.images["gold"], (90, 170))  # gold chest
        write(self.panelscreen, "\U0001F4B0", 90, 170, font_size=25, font=Viewer.font2)
        write(
            self.panelscreen,
            "{:>3}".format(gold),
            130,
            170,
            font_size=25,
        )
        # --------------disk icon, downloads ----------------
        # self.panelscreen.blit(make_text("\U0001F4BE", fontsize=32), (-15, 220))
        write(
            self.panelscreen,
            "\U0001F4BE",
            5,
            200,
            font_size=25,
            color=(0, 64, 0),
            font=Viewer.font2,
        )
        write(
            self.panelscreen,
            "{:>3}".format(downloads),
            25,
            200,
            font_size=25,
        )
        # --- food symbol, food ---------------------------
        # self.panelscreen.blit(Viewer.images["food"], (90, 200))
        write(
            self.panelscreen,
            "\U0001F35C",
            90,
            200,
            color=(255, 0, 255),
            font_size=25,
            font=Viewer.font2,
        )
        write(
            self.panelscreen,
            "{:>3}".format(food),
            130,
            200,
            font_size=25,
        )
        # ------arrow icon, arrows ------------------------------
        arrows = len(
            [i for i in Game.items.values() if isinstance(i, Arrow) and i.backpack]
        )
        write(self.panelscreen, "\u27B3", 5, 235, font_size=30)
        write(self.panelscreen, "{:>3}".format(arrows), 25, 235, font_size=25)

    def make_log(self):
        # self.logscreen = pygame.Surface((Viewer.width, Viewer.height - Viewer.logheight))
        self.logscreen.fill((64, 64, 64))
        for y in range(-1, -16, -1):  # write the last 15 lines
            try:
                line = self.loglines[y]
            except IndexError:
                continue
            i = len(self.loglines) + y + 1
            # c = i%5
            write(
                self.logscreen,
                f"{i}: {self.loglines[y]}",
                5,
                Viewer.logheight - y * -24,
                (0, 0, 50 + i % 5 * 40),
                24,
                origin="topleft",
            )

    @staticmethod
    def tile_to_pixel(tile_coordinates, center=True):
        """get a tile coordinate (x,y) and returns pixel (x,y) of tile
        if center is True, returns the center of the tile,
        if center is False, returns the upper left corner of the tile"""
        tx, ty = tile_coordinates
        x2 = Viewer.midscreen[0] + (tx - Game.player.x) * Viewer.gridsize[0]
        y2 = Viewer.midscreen[1] + (ty - Game.player.y) * Viewer.gridsize[1]
        if center:
            x2 += Viewer.gridsize[0] // 2
            y2 += Viewer.gridsize[1] // 2
        return x2, y2

    @staticmethod
    def pixel_to_tile(pixelcoordinates, relative=False):
        """transform pixelcoordinate xy, to tile coordinate xy.
        returns  distance to player in in tiles (if relative is True)
        or absolute tile coordinates (if relative is False"""
        px, py = pixelcoordinates
        hero = Game.player
        dtpx = (px - Viewer.midscreen[0]) // Viewer.gridsize[0]
        dtpy = (py - Viewer.midscreen[1]) // Viewer.gridsize[1]
        if relative:
            return (dtpx, dtpy)  # can be everywhere, even outside of dungeon
        else:  # calculate absolute position of tile
            dtpx += hero.x
            dtpy += hero.y
            # print("bevore between:", dtpx, dtpy, end="")
            # print("len y", len(Game.dungeon[hero.z][0])-1)
            # print("len y", len(Game.dungeon[hero.z])-1)
            dtpx = between(dtpx, Viewer.toplefttile[0], Viewer.bottomrighttile[0])
            dtpy = between(dtpy, Viewer.toplefttile[1], Viewer.bottomrighttile[1])
            # print("after between:", dtpx, dtpy)
            return (dtpx, dtpy)

    def paint_tiles(self):
        # print("effecs:", Game.effects) # destroyed effects are removed in calculate_fov -> process_effects
        for e in Game.effects.values():
            e.fov = False  # clear old fov information
        z = Game.player.z
        dungeon = Game.dungeon[z]
        tiles_x = len(Game.dungeon[0][0])  # z y x
        tiles_y = len(Game.dungeon[0])
        # exploredfg = Viewer.explored_fgcolor  # (0,100,0)
        exploredbg = Viewer.explored_bgcolor  # (10,10,10)
        Viewer.toplefttile = [tiles_x, tiles_y]  # start with absurd values
        Viewer.bottomrighttile = [-1, -1]
        for ty, line in enumerate(dungeon):
            for tx, tile in enumerate(line):
                # -------------- process each tile ----------------------
                x, y = Viewer.tile_to_pixel((tx, ty))
                if (
                    y < 0
                    or y
                    > Viewer.height
                    - Viewer.logheight
                    - Viewer.hudheight
                    - Viewer.gridsize[1]
                ):
                    break  # tile does not exist / is outside visible area -> continue with next ty
                if x < 0 or x > Viewer.width - Viewer.panelwidth - Viewer.gridsize[0]:
                    continue  # next tx
                # update visible tiles on screen information -> shrink rect of visible tiles
                Viewer.toplefttile[0] = min(tx, Viewer.toplefttile[0])
                Viewer.bottomrighttile[0] = max(tx, Viewer.bottomrighttile[0])
                Viewer.toplefttile[1] = min(ty, Viewer.toplefttile[1])
                Viewer.bottomrighttile[1] = max(ty, Viewer.bottomrighttile[1])
                # correction for center (necessary because drawing/blitting from topleft center)
                x -= Viewer.gridsize[0] // 2
                y -= Viewer.gridsize[1] // 2
                # paint on tile on the pygame sreen surface
                if not tile.fov:
                    # --------------- outside fov ----- not in players field of view
                    if (
                        tile.explored
                    ):  # known from previous encounter. paint only structure
                        pygame.draw.rect(
                            self.screen,
                            exploredbg,
                            (x, y, Viewer.gridsize[0], Viewer.gridsize[1]),
                        )  # fill with exploredbackgroundcolor
                        pic = tile.exploredpic
                        if pic is not None:
                            self.screen.blit(pic, (x, y))  # blit from topleft corner
                    else:  # invisible, black on black
                        pygame.draw.rect(
                            self.screen,
                            (0, 0, 0),
                            (x, y, Viewer.gridsize[0], Viewer.gridsize[1]),
                        )  # fill
                else:
                    # ---------------------------- inside fov ----- , --> tile.bgcolor for background
                    # --------- from ground to sky -> top is always drawn over (and partly blocking) bottom
                    #  ----- background color ----
                    pygame.draw.rect(
                        self.screen,
                        tile.bgcolor,
                        (x, y, Viewer.gridsize[0], Viewer.gridsize[1]),
                    )
                    # ------- structure --------
                    pic = tile.fovpic
                    ##print("structure:", tile, " pic=", pic, x, y)
                    if pic is not None:
                        self.screen.blit(pic, (x, y))  # blit from topleft corner
                    # ------------- items (without traps) ----------
                    items = [
                        i
                        for i in Game.items.values()
                        if i.z == z
                        and i.y == ty
                        and i.x == tx
                        and not i.backpack
                        and not isinstance(i, Trap)
                    ]
                    # ---------- traps (detected) ---------------
                    traps = [
                        i
                        for i in Game.items.values()
                        if i.z == z
                        and i.y == ty
                        and i.x == tx
                        and not i.backpack
                        and isinstance(i, Trap)
                        and i.detected
                    ]
                    items.extend(traps)
                    # ---- paint items and detected traps ---
                    itemcounter = len(items)
                    if itemcounter > 1:
                        # blit 'infinite' symbol if more than one items are at one tile
                        char = make_text("\u221E", (255, 200, 50))  # infinity sign
                        self.screen.blit(char, (x, y))  # blit from topleft corner
                    elif itemcounter == 1:
                        self.screen.blit(items[0].fovpicture(), (x, y))

                    # --------  monster -------------
                    monsters = [
                        m
                        for m in Game.zoo.values()
                        if m.z == z and m.y == ty and m.x == tx and m.hp > 0
                    ]
                    # monstercounter = len(monsters)
                    for m in monsters:
                        self.screen.blit(m.fovpicture(), (x, y))
                        # ----display up to 4 active effects in each corner of monster
                        for nr, b in enumerate(m.buffs):
                            self.screen.blit(b.pictures[0], (x+Viewer.gridsize[0]//2 * nr,y))



                        if (
                            isinstance(m, Player) and m.shield
                        ):  # umbrella: "\u2614", rectangle (smartphone): "\U0001F581"  # triangle: "\U0001F53B",  mushroom: \U0001F344"
                            self.screen.blit(
                                make_text(
                                    "\U0001F53B",
                                    fgcolor=(0, 0, 255),
                                    alpha=200,
                                ),
                                (x, y),
                            )

                    # ------------- effects --------------
                    for e in [
                        e
                        for e in Game.effects.values()
                        if e.tx == tx and e.ty == ty and e.age >= 0
                    ]:
                        e.fov = True
                        e.px, e.py = x, y

                    # ----- seve effect srceenrect to background (otherwise effects have black background? )

                    for e in [
                        e
                        for e in Game.effects.values()
                        if e.tx == tx and e.ty == ty and e.age >= 0
                    ]:
                        # where to blit ( what to blit, (where on dest topleftxy), (rect-area of source to blit )
                        e.background.blit(
                            self.screen,
                            (0, 0),
                            (e.px, e.py, Viewer.gridsize[0], Viewer.gridsize[1]),
                        )
                    # ------------ grid --------------
                    pygame.draw.rect(
                        self.screen,
                        (128, 128, 128),
                        (x, y, Viewer.gridsize[0], Viewer.gridsize[1]),
                        1,
                    )

                #     # ----------------------------------------------------------------------
                #     # effect is blocking items, but not monsters
                #     monstercounter = 0
                #     monsters = [
                #         m
                #         for m in Game.zoo.values()
                #         if m.z == z and m.y == ty and m.x == tx and m.hp > 0
                #     ]
                #     monstercounter = len(monsters)
                #     for m in monsters:
                #         # char = make_text(monster.char, font_color=monster.fgcolor, font_size=48, max_gridsize=Viewer.gridsize)
                #         # self.screen.blit(char, (x, y))  # blit from topleft corner
                #         self.screen.blit(m.fovpicture(), (x, y))
                #         # break # no more than one monster per tile
                #     monstercounter = len(monsters)
                #     # always paint effect, if necessary paint effect OVER monster
                #     # calculate effect animation coordinates and fov ( effect will be painted in Viewer.run
                #
                #     for e in [
                #         e
                #         for e in Game.effects.values()
                #         if e.tx == tx and e.ty == ty and e.age >= 0
                #     ]:
                #         e.fov = True
                #         e.px, e.py = x, y
                #         # no break because multiple effects per tile are possible
                #         # blitting of effect will be done in Viewer.paint_animation because all effects have animations
                #     if monstercounter == 0:
                #         # monster is blocking items
                #         itemcounter = 0
                #         items = [
                #             i
                #             for i in Game.items.values()
                #             if i.z == z and i.y == ty and i.x == tx and not i.backpack
                #         ]
                #         itemcounter = len(items)
                #         if itemcounter > 1:
                #             # blit 'infinite' symbol if more than one items are at one tile
                #             char = make_text("\u221E", (255, 200, 50))  # infinity sign
                #             self.screen.blit(char, (x, y))  # blit from topleft corner
                #         elif itemcounter == 1:
                #             # self.screen.blit(char, (x, y))  # blit from topleft corner
                #             self.screen.blit(items[0].fovpicture(), (x, y))
                #         elif itemcounter == 0:
                #             # paint the structure pic
                #             pic = tile.fovpicture()
                #             if pic is not None:
                #                 self.screen.blit(
                #                     pic, (x, y)
                #                 )  # blit from topleft corner
                #
                #     # save screenrect background for effect at this place
                #     for e in [
                #         e
                #         for e in Game.effects.values()
                #         if e.tx == tx and e.ty == ty and e.age >= 0
                #     ]:
                #         # where to blit ( what to blit, (where on dest topleftxy), (rect-area of source to blit )
                #         e.background.blit(
                #             self.screen,
                #             (0, 0),
                #             (e.px, e.py, Viewer.gridsize[0], Viewer.gridsize[1]),
                #         )
                # # -------------- paint grid rect ---------------
                # pygame.draw.rect(
                #     self.screen,
                #     (128, 128, 128),
                #     (x, y, Viewer.gridsize[0], Viewer.gridsize[1]),
                #     1,
                # )

    def paint_animation(self, seconds):
        """update animated tiles (effects) between player turns
        all visible effects have .fov set to True (done by self.paint_tiles)
        and all visible effects have already .px and .py for topleft corner in pixel (also by self.paint_tiles)
        seconds is time passed since last frame (from Viewer.run)
        """
        for e in [e for e in Game.effects.values() if e.fov]:
            # blit first backup screen from last frame (without sprites/effects)
            # self.screen.blit(self.screen_backup, (e.px, e.py), (0,0,Viewer.gridsize[0], Viewer.gridsize[1]))

            self.screen.blit(e.background, (e.px, e.py))
            # blit effect picture on top
            if e.wobble:  # e.wobble is either False or a xy tuple
                wobble_x = random.randint(-e.wobble[0], e.wobble[0])
                wobble_y = random.randint(-e.wobble[1], e.wobble[1])
            else:
                wobble_x = 0
                wobble_y = 0
            self.screen.blit(e.fovpicture(seconds), (e.px + wobble_x, e.py + wobble_y))

    def panelinfo(self):
        """overwrites a piece of the panel with info about the objects currently under the cursor"""
        tx, ty = self.cursor.tx, self.cursor.ty
        # print("from cursor:", tx, ty)
        hero = Game.player
        try:
            tile = Game.dungeon[hero.z][ty][tx]
        except IndexError:
            return
        items = []
        monsters = []
        effects = []
        text = "?"
        if not tile.fov:
            if not tile.explored:
                text = "Structure: unexplored tile"
            else:
                if isinstance(tile, Door):
                    text = "Structure: {} door".format(
                        "a locked"
                        if tile.locked
                        else "a closed"
                        if tile.closed
                        else "an open"
                    )
                else:
                    text = "Structure: " + tile.__class__.__name__
        else:
            text = "Structure: " + tile.__class__.__name__
            for e in [
                e
                for e in Game.effects.values()
                if e.tx == tx and e.ty == ty and e.age >= 0
            ]:
                effects.append(e)
            for i in [
                i
                for i in Game.items.values()
                if (
                    not i.backpack
                    and i.z == hero.z
                    and i.x == tx
                    and i.y == ty
                    and not (isinstance(i, Trap) and not i.detected)
                )
            ]:
                items.append(i)
            for m in [
                m
                for m in Game.zoo.values()
                if m.hp > 0 and m.z == hero.z and m.x == tx and m.y == ty
            ]:
                monsters.append(m)
        # ---- print to panel
        y = 400
        pygame.draw.line(self.panelscreen, (0, 0, 0), (0, y), (Viewer.panelwidth, y), 3)
        pygame.draw.rect(
            self.panelscreen,
            Viewer.panelcolor,
            (0, y, Viewer.panelwidth, Viewer.height - y),
        )
        y += 5
        write(self.panelscreen, text, 5, y, (0, 0, 0), font_size=14)  # structure
        for e in effects:
            y += 15
            text = e.__class__.__base__.__name__ + ": " + e.__class__.__name__
            # write(self.panelscreen, e.char, 0, y, e.fgcolor, font_size=20)
            write(self.panelscreen, text, 5, y, (0, 0, 0), font_size=14)
        for m in monsters:
            y += 15
            text = m.__class__.__base__.__name__ + ": " + m.__class__.__name__
            # write(self.panelscreen, m.char, 0, y, m.fgcolor, font_size=20)
            write(self.panelscreen, text, 5, y, (0, 0, 0), font_size=14)
        for i in items:
            y += 15
            text = i.__class__.__base__.__name__ + ": " + i.__class__.__name__
            # write(self.panelscreen, i.char, 0, y, i.fgcolor, font_size=20)
            write(
                self.panelscreen,
                text,
                5,
                y,
                (0, 0, 0),
                font_size=14,
            )

    def repaint_screen(self, panel_has_changed=False, dungeon_has_changed=False):
        """called 60 times per second from Viewer.run"""
        # -------------------------delete everything on screen--------------------------------------
        # pygame.display.set_caption(str(cursormode))
        # repaint = True
        while True:
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            # ---- calculate fps ----
            fps_text = "pipe_roge ({}x{}) FPS: {:8.3}".format(
                Viewer.width, Viewer.height, self.clock.get_fps()
            )
            # pygame.display.set_caption("pipe_rogue version:".format(version))
            pygame.display.set_caption(fps_text)
            repaint = False
            # or len(self.flytextgroup) > 0
            if self.cursormode or len(self.flygroup) > 0 or len(self.fxgroup):
                repaint = True
            if dungeon_has_changed:
                ## kill old sprites of effects:
                # for n in [sprite for sprite in self.effectgroup]:
                #    print("iterating over effects", n)

                self.screen.blit(self.background, (0, 0))
                self.paint_tiles()
                self.make_radar()
                self.make_panel()
                self.make_log()
                ##pygame.display.flip() # bad idea
                self.screen.blit(
                    self.radarscreen, (Viewer.width - Viewer.panelwidth, 0)
                )
                self.screen.blit(self.logscreen, (0, Viewer.height - Viewer.logheight))
                self.screen_backup = self.screen.copy()
                # testing...
                # for x, i in enumerate(Flash.pictures):
                #    self.screen.blit(i, (x * Viewer.gridsize[0], 20))
                #    #input("...")
            if repaint:
                self.screen.blit(self.screen_backup, (0, 0))

            self.cursorgroup.clear(self.screen, self.screen_backup)
            if panel_has_changed:
                self.make_panel()
            self.screen.blit(
                self.panelscreen, (Viewer.width - Viewer.panelwidth, Viewer.panelwidth)
            )

            # ---- clear old effect, paint new effects ----
            self.paint_animation(seconds)
            # ---- update panel with help for tile on cursor -----
            if not self.cursormode:
                self.panelinfo()
            # ---- update -----------------
            self.allgroup.update(seconds)
            self.cursorgroup.update(seconds)
            # ----------- draw  -----------------
            self.allgroup.draw(self.screen)
            # self.visiblegroup.empty()
            self.visiblegroup = self.allgroup.copy()
            for s in self.visiblegroup:
                if not s.visible:
                    s.rect.centery = -500
            # for s in self.allgroup:
            #    if s.visible:
            #        self.visiblegroup.add(s)
            # visiblegroup = [s for s in self.allgroup if s.visible]
            self.visiblegroup.draw(self.screen)
            self.cursorgroup.draw(self.screen)
            if self.cursormode:
                self.screen.blit(Viewer.images["bow_no"], pygame.mouse.get_pos())
            pygame.display.flip()
            # repaint = False
            if len(self.flygroup) > 0:
                continue
            break
        return

    def run(self):
        """The mainloop"""
        running = True
        panel_has_changed = True
        dungeon_has_changed = True
        text = []
        self.cursormode = False
        selection = None
        hero = Game.player
        # pygame.mouse.set_visible(False)
        oldleft, oldmiddle, oldright = False, False, False

        # Bubble(pos=pygame.math.Vector2(200, 200), age=-1)
        Flytext(
            pos=pygame.math.Vector2(Viewer.width // 2, Viewer.height // 2),
            move=pygame.math.Vector2(0, -15),
            text="Enjoy pipe_rogue!",
            fontsize=64,
            max_age=2.0,
            age=-0,
            bgcolor=None,
            alpha_start=255,
            alpha_end=0,
            width_start=None,
            width_end=None,
            height_start=None,
            height_end=None,
            rotate_start=0,
            rotate_end=0,
        )
        # Flytext(text="press h for help", age=-2)
        # self.screen_backup = self.screen.copy()
        # self.repaint_screen(True, True) # force painting of screen
        while running:
            dx, dy, dz = None, None, None  # player movement -> new Game.turn!
            # print(pygame.mouse.get_pos(), Viewer.pixel_to_tile(pygame.mouse.get_pos()))
            # print(self.playergroup[0].pos, self.playergroup[0].cannon_angle)

            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if self.cursormode:
                        # ----------------- in cursormode ----------------------------
                        if event.key == pygame.K_ESCAPE:
                            self.cursormode = False
                            # self.cursor.visible = False
                        if (
                            event.key == pygame.K_RETURN
                            or event.key == pygame.K_KP_ENTER
                        ):
                            selection = self.pixel_to_tile(pygame.mouse.get_pos())
                            # print("selected: ", selection)
                            self.cursormode = False
                    else:
                        # -------------- not in cursormode --------------
                        # if event.key == pygame.K_1:
                        #    # testing bluegroup
                        #    cell = self.pixel_to_tile(pygame.mouse.get_pos())
                        #    px,py = self.tile_to_pixel(cell)
                        #    BlueTile(pos=pygame.math.Vector2(px,py))

                        if event.key == pygame.K_ESCAPE:
                            running = False
                        if event.key == pygame.K_f:
                            # start selection with cursor (mouse)
                            self.cursormode = True
                            selection = None  # clear old selection
                            # self.cursor.visible=True
                        if event.key == pygame.K_PLUS:
                            Viewer.radardot = [
                                min(Viewer.panelwidth // 4, i * 2)
                                for i in Viewer.radardot
                            ]
                            self.make_radar()
                            self.screen.blit(
                                self.radarscreen, (Viewer.width - Viewer.panelwidth, 0)
                            )
                            # dungeon_has_changed = True
                        if event.key == pygame.K_MINUS:
                            Viewer.radardot = [max(1, i // 2) for i in Viewer.radardot]
                            self.make_radar()
                            self.screen.blit(
                                self.radarscreen, (Viewer.width - Viewer.panelwidth, 0)
                            )
                        if event.key == pygame.K_w:
                            dx, dy = 0, -1
                            self.loglines.extend(self.g.turn(0, -1))
                            dungeon_has_changed = True
                        if event.key == pygame.K_s:
                            dx, dy = 0, 1
                            self.loglines.extend(self.g.turn(0, 1))
                            dungeon_has_changed = True
                        if event.key == pygame.K_a:
                            dx, dy = -1, 0
                            self.loglines.extend(self.g.turn(-1, 0))
                            dungeon_has_changed = True
                        if event.key == pygame.K_d:
                            dx, dy = 1, 0
                            self.loglines.extend(self.g.turn(1, 0))
                            dungeon_has_changed = True
                        if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                            dx, dy = 0, 0
                            self.loglines.extend(self.g.turn(0, 0))
                            dungeon_has_changed = True
                        if event.key == pygame.K_p:
                            Game.player.toggle_shield()
                            panel_has_changed = True
                        if event.key == pygame.K_c:
                            # close door
                            dx, dy = 0, 0
                            self.loglines.extend(self.g.close_door())
                            dungeon_has_changed = True
                        if event.key == pygame.K_t:
                            # ----------- testing key -------
                            # testing the buring buff
                            Burning(monsternumber=hero.number)
                            Flytext(tx=hero.x, ty=hero.y,
                                    text="Burning starts")
                        if event.key == pygame.K_e:
                            # if south of terminal -> activate download,
                            # otherwise -> eat food
                            if hero.y > 0 and isinstance(
                                Game.dungeon[hero.z][hero.y - 1][hero.x], Terminal
                            ):
                                Game.dungeon[hero.z][hero.y - 1][
                                    hero.x
                                ].effect_download()
                            else:
                                self.loglines.extend(self.g.eat())
                            panel_has_changed = True
                            dx, dy = 0, 0

                        # ---------- on german keyboard, K_GREATER key is the same as SHIFT and K_LESS
                        # ------------ climb up/down -----------------
                        if event.key == pygame.K_LESS or event.key == pygame.K_GREATER:
                            # depending on tile, climb up or down
                            mytile = Game.dungeon[hero.z][hero.y][hero.x]
                            if isinstance(mytile, StairDown):
                                self.loglines.extend(self.g.climb_down())
                                dungeon_has_changed = True
                            elif isinstance(mytile, StairUp):
                                self.loglines.extend(self.g.climb_up())
                                dungeon_has_changed = True
                            else:
                                self.loglines.append("You must find a stair")

            # ------------ pressed keys ------
            # pressed_keys = pygame.key.get_pressed()

            # ------ mouse handler ------
            left, middle, right = pygame.mouse.get_pressed()
            if not oldleft and left and self.cursormode:
                selection = self.pixel_to_tile(pygame.mouse.get_pos())
                # print("selected: ", selection)
                self.cursormode = False

            oldleft, oldmiddle, oldright = left, middle, right

            # -------------- special effect after cursormode selection -------
            if selection is not None:
                hero.shoot_arrow(*selection)
                selection = None
                self.repaint_screen(panel_has_changed, dungeon_has_changed)  # finish
                self.loglines.extend(self.g.turn(0, 0))  # waste a turn for shooting
                panel_has_changed = True

            self.repaint_screen(panel_has_changed, dungeon_has_changed)
            repaint = False
            dungeon_has_changed = False
            # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()


## -------------------- functions --------------------------------


def pulse(age_in_seconds, min_value=1, max_value=6, values_per_second=1):
    """Generate a pulsating value generated from age_in_seconds.

    Parameters
    ----------
    age_in_seconds : float
        seed value for calculation, usually the .age attribute of a VectorSprite
    min_value : int
        Minumum output value
    max_value: int
        Maximum output value. Must be lesser than min_value
    values_per_second: float
        Can not be zero. How many pulse values should be generated in the interval of one second.
        Only meaningful if age_in_seconds is a .age attribute of a Sprite and the function is called
         several times per second.

    Returns
    -------
    int
        The pulsating value, oscillating between min_value and max_value

    Examples
    --------
    >>> print([pulse(i,1,6,1) for i in range(15)])
    [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5]
    """
    if not isinstance(min_value, int):
        raise ValueError(f"min_value {min_value} must be integer")
    if not isinstance(max_value, int):
        raise ValueError(f"max_value {max_value} must be integer")
    if min_value >= max_value:
        raise ValueError(
            f"min_value {min_value} must be lesser than max_value {max_value}"
        )
    if values_per_second == 0:
        raise ValueError(f"0 is not allowed for values_per_second")
    amount = (max_value - min_value) * 2
    half = amount / 2
    a = age_in_seconds * values_per_second  # 1 / values_per_second
    i = int(a % amount)

    if i > half:
        return int(half - (i - half)) + min_value
    else:
        return int(i) + min_value


def get_line(start, end):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
    source: http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python
    see also: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

    #>>> points1 = get_line((0, 0), (3, 4))
    # >>> points2 = get_line((3, 4), (0, 0))
    #>>> assert(set(points1) == set(points2))
    #>>> print points1
    #[(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    #>>> print points2
    #[(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


def calculate_line(start, end, z, modus="all"):
    """calculates if a line in Game.dungeon[z]
    from startpoint(x,y) to endpoint(x,y) is free (not blocked)
    by a Structure tile for sight, shooting, moving.
    Includes both endpoints
    modus can be:   "all" -> returns bool, bool, bool
                    "sight" -> returns bool
                    "shoot" -> returns bool
                    "move"  -> returns bool
    """
    # print("calculating line in dungeon", z, "from", start, "to", end, "for", modus)
    points = get_line(start, end)
    # create copy
    sight_ok = True
    shoot_ok = True
    move_ok = True
    for point in points:
        x, y = point[0], point[1]
        tile = Game.dungeon[z][y][x]
        if tile.block_sight:
            if modus == "sight":
                return False
            sight_ok = False
        if tile.block_movement:
            if modus == "move":
                return False
            move_ok = False
        if tile.block_shooting:
            if modus == "shoot":
                return False
            shoot_ok = False
    if modus == "all":
        return sight_ok, shoot_ok, move_ok
    return True  # all other modi would have returned False way before


# ----------------


def make_text(
    text="@",
    fgcolor=(0, 128, 0),
    bgcolor=None,
    rotation=0,
    style=pygame.freetype.STYLE_DEFAULT,
    size=None,
    mono=False,
    alpha=None,
    font=Viewer.font,
    fontsize=None,
    colorkey=(0, 0, 0),
):
    """returns pygame surface (Viewer.gridsize[0] x Viewer.gridsize[1]) with text blitted on it.
    The text is centered on the surface. Font_size = Viewer.fontsize
    You still need to blit the surface.
    Use pygame.rect methods to get width and height of the new surface

    :param str text: the text to render into the surface
    :param (int, int, int) fgcolor: text color
    :param (int, int, int) bgcolor: background color or None for transparent background
    :param float rotation: render rotation for text (does not work with mono)
    :param int style: constant for text style (does not work with mono). See pygame.freetype
    :param (int,int) size: size of Surface in pixel. If None, takes (Viewer.fontsize x Viewer.fontsize)
    :param bool mono: if True, use pygame.font.Font to render (better for non-proportional chars like wall-tiles)
    :param int alpha: alpha value for the whole Surface, if set to None the color (0,0,0) will be used as colorkey
    :param font: font object. If mono, -> pygame.font.Font(fontobject. If not mono: pygame.freetype.Font(fontobject)
    :param int fontsize: size of font
    :param (int,int,int) colorkey: colorkey, can be set to None
    :return: pygame.Surface
    """
    if size is None:
        size = (Viewer.fontsize, Viewer.fontsize)
    if not isinstance(size, tuple) and not isinstance(size, list):
        size = (size, size)
    if fontsize is None:
        fontsize = Viewer.fontsize
    surf = pygame.Surface(Viewer.gridsize)

    midx = Viewer.gridsize[0] // 2
    midy = Viewer.gridsize[1] // 2

    if mono:
        if font is None:
            font = Viewer.monofontfilename
        # myfont = Viewer.monofontfilename
        # oldfont = pg.font.Font(os.path.join(fontdir, "..", "data", "fonts", "FreeMonoBold.otf"), fontsize)
        myfont = pygame.font.Font(font, fontsize)
        # pic = oldfont.render(chars[char_index], True, (255, 64, 64))
        # rect = pic.get_rect()
        text1 = myfont.render(text, True, fgcolor)
        rect1 = text1.get_rect()
        # midtx = rect1.width // 2
        # midty = rect1.height // 2
        # surf.blit(text1, (midx - midtx, midy - midty))
    else:
        if font is None:
            font = Viewer.font
        font.origin = False  # make sure to blit from topleft corner
        # rect1 = font.get_rect(text, style, rotation, fontsize)
        # midtx = rect1.width // 2
        # midty = rect1.height // 2
        # rect2  = font.render_to(surf, (midx-midtx,midy-midty), text, fgcolor, bgcolor, style, rotation, fontsize)
        text1, rect1 = font.render(text, fgcolor, bgcolor, style, rotation, fontsize)
    # finally
    midtx = rect1.width // 2
    midty = rect1.height // 2
    surf.blit(text1, (midx - midtx, midy - midty))
    # ---- alpha -----
    if colorkey is not None:
        surf.set_colorkey(colorkey)
    if alpha is not None:
        # surf.set_colorkey((0, 0, 0))
        # else:
        surf.set_alpha(alpha)
    surf.convert_alpha()
    return surf


def throw_dice(dice=1, reroll=True, sides=6, correction=0):
    """returns the sum of dice throws, the sides begin with number 1
    if a 6 (or hightest side number) is rolled AND reroll==True,
    then sides-1 is counted and another roll is made and added
    (can be repeated if another 6 is rolled).
    example:
    roll 5 -> 5
    roll 6, reroll 1 -> 5+1 = 6
    roll 6, reroll 6, reroll 3 -> 5 + 5 + 3 = 13
    correction is added (subtracted) to the end sum, after all rerolls
    important:
    expecting random module imported in this module
    ##expect rng = np.random.default_rng() declared before call
    calculate from string using:
    result = throw_dice(*dice_from_string(a.attack))
    """
    total = 0
    for d in range(dice):
        # roll = rng.integers(1,sides,1, endpoint=True)
        roll = random.randint(1, sides)
        ##print(roll)
        if not reroll:
            ##total += roll[0]
            total += roll
        elif roll < sides:
            ##total+=roll[0]
            total += roll
        else:
            # print("re-rolling...")
            total += sides - 1
            total += throw_dice(1, reroll, sides)  # + correction already here??
    return total + correction


def dice_from_string(dicestring="1d6+0"):
    """expecting a dicestring in the format:
    {dice}d{sides}+{correction}
    examples:
    1d6+0 ... one 6 sided die without re-roll
    2D6+0 ... two 6-sided dice with reroll
    1d20+1 ... one 20-sided die, correction value +1
    3D6-2 ... three 6-sided dice with reroll, sum has correction value of -2
    where:
    d........means dice without re-roll
    D........means dice with re-roll (1D6 count as 5 + the reroll value)
    {dice} ...means number of dice throws, 2d means 2 dice etc. the sum of all throws is returned. must be integer
    {sides} ...means mumber of sides per die dice. d20 means 20-sided dice etc. must be integer
    {correction}.......means correction value that is added (subtracted) to the sum of all throws. must be integer

    returns [dice, recroll, sides, correction]
    """
    # checking if string is correct
    dicestring = dicestring.strip()  # remove leading and trailing blanks
    if dicestring.lower().count("d") != 1:
        raise ValueError("none or more than one d (or D) found in: " + dicestring)
    dpos = dicestring.lower().find("d")
    reroll = True if dicestring[dpos] == "D" else False
    # try:
    dice = int(dicestring[:dpos])
    # except ValueError:
    # return [None,None,None,None], "integer value before d is missing in: " + dicestring
    rest = dicestring[dpos + 1 :]
    seperator = "+" if "+" in rest else ("-" if "-" in rest else None)
    if seperator is not None:
        # try:
        sides = int(rest[: rest.find(seperator)])
        # except ValueError:
        #    return [None,None,None,None], "integer value after d is missing in: " + dicestring
        # try:
        correction = int(rest[rest.find(seperator) :])
        # except ValueError:
        #    return [None,None,None,None], "integer value afer + (or -) is missing in: " + dicestring
    else:
        # try:
        sides = int(rest)
        # except ValueError:
        #    return [None, None, None, None], "integer value after d is missing in: " + dicestring
        correction = 0
    # print("dice {} sides {} correction {}".format(dice, sides, correction))
    return [dice, reroll, sides, correction]


def fight(a, b):
    """dummy function, does nothing yet"""
    text = []
    text.append("Strike! {} attacks {}".format(type(a).__name__, type(b).__name__))
    damage = random.randint(1, 6)
    b.hp -= damage
    impact_bubbles(a, b)
    return text


def impact_bubbles(a, b):
    """bubbles because monster a strikes v.s monster b"""
    victimcolor = b.fgcolor
    bx, by = Viewer.tile_to_pixel((b.x, b.y))
    # ax, ay = Viewer.tile_to_pixel((a.x,a.y))
    m = pygame.math.Vector2(b.x, b.y) - pygame.math.Vector2(a.x, a.y)
    m.normalize_ip()
    # impact point
    impactpoint = pygame.math.Vector2(bx, by) - m * Viewer.gridsize[0] // 2
    Flytext(
        tx=b.x,
        ty=b.y,
        color=a.fgcolor,
        text="\u2694",
        fontsize=64,
        move=pygame.math.Vector2(0, -5),
        width_start=Viewer.gridsize[0],
        width_end=Viewer.gridsize[0] * 2,
    )  # crossed Swords
    for _ in range(15):
        po = pygame.math.Vector2(impactpoint.x, impactpoint.y)
        mo = pygame.math.Vector2(m.x, m.y)
        mo.rotate_ip(random.randint(-60, 60))
        mo *= random.random() * 25 + 25
        Bubble(pos=po, color=b.fgcolor, move=-mo, max_age=0.3)


def between(value, min=0, max=255):
    """makes sure a (color) value stays between a minimum and a maximum ( 0 and 255 ) """
    return 0 if value < min else max if value > max else value


# generic pygame functions


def write(
    background,
    text,
    x=50,
    y=150,
    color=(0, 0, 0),
    font_size=None,
    font=None,
    origin="topleft",
    mono=False,
    rotation=0,
    style=pygame.freetype.STYLE_STRONG,
):
    """blit text on a given pygame surface (given as 'background')

    :param  background:  A pygame Surface
    :param str text:    The text to blit
    :param int x:  x-position of text (see origin)
    :param int y:  y-postiont of text (see origin)
    :param (int, int, int) color: text color
    :param int font_size: size of font
    :param font: font object
    :param str origin: can be one of those values: 'center', 'centercenter', 'topleft', 'topcenter', 'topright', 'centerleft', 'centerright',
    'bottomleft', 'bottomcenter', 'bottomright'
    :param bool mono: DOES NOT WORK ! if True, use Viewer.monofont instead of Viewer.font
    :param int rotation: text rotation
    :param int style: text style, see pygame.freetype
    """
    if font_size is None:
        font_size = 24
    #
    if font is None:
        font = Viewer.font  # pygame.font.SysFont(font_name, font_size, bold)

    if mono:
        font = Viewer.monofont

    # else:
    #    font = Viewer.font
    surface, rrect = font.render(
        text, color, rotation=rotation, size=font_size, style=style
    )
    width, height = rrect.width, rrect.height
    # surface = font.render(text, True, color)

    if origin == "center" or origin == "centercenter":
        background.blit(surface, (x - width // 2, y - height // 2))
    elif origin == "topleft":
        background.blit(surface, (x, y))
    elif origin == "topcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "topright":
        background.blit(surface, (x - width, y))
    elif origin == "centerleft":
        background.blit(surface, (x, y - height // 2))
    elif origin == "centerright":
        background.blit(surface, (x - width, y - height // 2))
    elif origin == "bottomleft":
        background.blit(surface, (x, y - height))
    elif origin == "bottomcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "bottomright":
        background.blit(surface, (x - width, y - height))


## -------------- code at module level -----------------------------

# use those chars to create tiles, monsters, items etc in level maps. Values are class names, not Strings!:
legend = {
    "#": Wall,
    ".": Floor,
    ">": StairDown,
    "<": StairUp,
    "d": Door,
    "g": Glass,
    "@": Player,
    "M": Monster,
    "F": FireDragon,
    "W": WaterDragon,
    "S": SkyDragon,
    "k": Key,
    "$": Coin,
    "f": Food,
    "ß": Snake,
    "T": Trap,
    "t": Terminal,
    ":": Oil,
    "a": Arrow,
}
level1 = """
######################################
#@kdMMMMMMM..........TTT....$.....M..#
#>a########gd#.....#...t....#...#....#
##a#.##f..#gd#.#...#.......###.......#
#.$$.M....gß.g.#...#...ff..#...$...k.#
######################################"""

# insert in level2: W for WaterDragon, S for Skydragon

level2 = """
#################################################################
#..<............................................................#
#>...........kkkk...............................................#
#...............................................................#
#..................................................:::::::::::::#
#...............##d##g##......:::::::...............::::::::::::#
#...............#.W....#......:::::::..............:::::::::::::#
#...............#..S...d......:::::::..............:::::::::::::#
#...............g......g......:::::::...........................#
#...............#.F....d........................................#
#.kk.k.k........d..F...#...............................kk.......#
#...............###d#g##........................................#
#......................................::::::::::::::::...###d###
#......................................::::::::::::::::...d.FFF.#
#......................................::::::::::::::::...#.FFF.#
#################################################################"""

level3 = """
################################
#..............................#
#<.............................#
#..............................#
################################"""

if __name__ == "__main__":
    # g = Game()
    Viewer(
        width=1200,
        height=960,
        gridsize=(64, 64),
        panelwidth=200,
        logheight=100,
        fontsize=48,
        wallfontsize=105,
        max_tiles_x=200,
        max_tiles_y=200,
    )
