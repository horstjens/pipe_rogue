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

# useful: 3stars: \u2042
# pycharm colorpicker: alt+enter+c

# font vs freetype: font can not render long unicode characters... render can. render can also rotate text

"""
# TODO: include pathfinding from test
# TODO: save levels to pickle, load levels when changing player.z
# TODO: dungoen generator, dungeon Viewer / Editor (pysimplegui?)
# TODO: include complex fight / strike system
# TODO: diplay unicode symbols for attack/defense rolls

# TODO: make correct docstring for make_text
# TODO: light emiiting lamps, difference fov - light, turning lamps on and off, sight_distacne <> torchradius
# TODO: big enjoy Flytext: gridcursorsprite is painted OVER flytext -> should be: first grid, than flytext on top!
# don: make bitmpap out of every maketext-char to faciliate easier replacing with images
# wontfix because using maketext:  fireeffect sprite erscheint in der linken oberen ecke -> create_image / init / update ?
# TODO: minimalspeed für Arrow, soll trotzdem am target_tile verschwinden - max_distance
# TODO: (autohiding) hint/button in panel when player at stair and up/down command is possible
# TODO: Monster movement: actualy move (sprites) instead of teleport tiles. Fixed time (0.5 sec) for all movements?
# TODO: better battle impact effects
# TODO: Monster moving toward each other when fighting
# TODO: animations of blocks / monsters when nothing happens -> animcycle
# TODO: non-player light source / additive lightmap
# TODO: drop items -> autoloot? manual pickup command?
# done: in Viewer.load_images, iterate over all subclasses of Structure automatically
# done: shießen mit F geht nicht mehr
# done: cursorsprite : Fehler -> wird ungenau je mehr man nach rechts fährt
# done: schießen mit f zeigt falschen pfad nach levelwechsel
# done: cursorsprite: Fehler -> cursor kann rechten und unteren dungeonrand verlassen -Formel?

import pygame
import pygame.freetype # not automatically loaded when importing pygame!
import random
import os
version = 0.5

class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygames sprite class"""
    number = 0
    #numbers = {} # { number, Sprite }

    def __init__(self, **kwargs):
        self._default_parameters(**kwargs)
        self._overwrite_parameters()
        pygame.sprite.Sprite.__init__(self, self.groups) #call parent class. NEVER FORGET !
        self.number = VectorSprite.number # unique number for each sprite
        VectorSprite.number += 1
        #VectorSprite.numbers[self.number] = self
        self.create_image()
        self.distance_traveled = 0 # in pixel
        #self.rect.center = (-300,-300) # avoid blinking image in topleft corner
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
        else:
            self.layer = self.layer
        if "pos" not in kwargs:
            self.pos = pygame.math.Vector2(200,200)
        if "move" not in kwargs:
            self.move = pygame.math.Vector2(0,0)
        if "angle" not in kwargs:
            self.angle = 0 # facing right?
        if "radius" not in kwargs:
            self.radius = 5
        if "width" not in kwargs:
            self.width = self.radius * 2
        if "height" not in kwargs:
            self.height = self.radius * 2
        if "color" not in kwargs:
            #self.color = None
            self.color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        if "hitpoints" not in kwargs:
            self.hitpoints = 100
        self.hitpointsfull = self.hitpoints # makes a copy


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
            if "boss" in s.__dict__:
                if s.boss == self:
                    tokill.append(s)
        for s in tokill:
            s.kill()
        #if self.number in self.numbers:
        #   del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)

    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        else:
            self.image = pygame.Surface((self.width,self.height))
            self.image.fill((self.color))
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect= self.image.get_rect()
        self.rect.center =  ( round(self.pos[0], 0), round(self.pos[1], 0) )
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
        #print("rect:", self.pos.x, self.pos.y)
        self.rect.center = ( round(self.pos.x, 0), round(self.pos.y, 0) )

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
        if self.pos.y  < Viewer.hudheight:
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
        if self.pos.x  > Viewer.width:
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
        if self.pos.y   > Viewer.height:
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
    """a text flying for a short time around, like hitpoints lost message"""
    def __init__(self, pos=pygame.math.Vector2(50,50), move=pygame.math.Vector2(0,-50),
                  text="hallo", color=(255, 0, 0), max_age=2, age=0,
                 acceleration_factor = 1.0,  fontsize=22, textrotation=0, bgcolor=None):
        """a text flying upward and for a short time and disappearing"""
        VectorSprite.__init__(self, pos=pos, move=move, text=text, color=color,
                              max_age=max_age, age=age, acceleration_factor=acceleration_factor,
                              fontsize=fontsize, textrotation=textrotation, bgcolor=bgcolor)
        self._layer = 7  # order of sprite layers (before / behind other sprites)

        #acceleration_factor  # if < 1, Text moves slower. if > 1, text moves faster.

    def create_image(self):
        myfont = Viewer.font
        text, textrect  = myfont.render(text=self.text, fgcolor=self.color, bgcolor=self.bgcolor, size=self.fontsize,
                                      rotation = self.textrotation)  # font 22
        self.image = text
        self.rect = textrect
        #self.rect.center = (-400,-400) # if you leave this out the Flytext is stuck in the left upper corner at 0,0
        self.rect.center = (self.pos.x, self.pos.y)

    def update(self, seconds):
        self.move *= self.acceleration_factor
        VectorSprite.update(self, seconds)

class BlueTile(VectorSprite):

    def _overwrite_parameters(self):
        self.color = (0,0,255) # blue

    def create_image(self):
        self.image = pygame.surface.Surface((Viewer.gridsize[0],
                                             Viewer.gridsize[1]))
        #c = random.randint(100, 250)

        pygame.draw.rect(self.image, self.color, (0, 0, Viewer.gridsize[0],
                                                 Viewer.gridsize[1]), 5)
        #self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(128)
        #self.image.convert_alpha()
        self.rect = self.image.get_rect()

class TileCursor(VectorSprite):

    def _overwrite_parameters(self):
        self.tx, self.ty = 0, 0
        self.c = 200
        self.c_min = 200
        self.c_max = 255
        self.dc = 15

    def create_image(self):
        self.image = pygame.surface.Surface((Viewer.gridsize[0],
                                             Viewer.gridsize[1]))
        #c = random.randint(100, 250)
        self.c += self.dc
        if self.c >= self.c_max:
            self.dc = -1
        if self.c <= self.c_min:
            self.dc = 1
        self.c = between(self.c, self.c_min, self.c_max)

        pygame.draw.rect(self.image, (self.c, self.c, self.c), (0, 0, Viewer.gridsize[0],
                                                 Viewer.gridsize[1]), 5)
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()

    def update(self, seconds):
        self.create_image()  # always make new image every frame with different color
        self.tx,self.ty = Viewer.pixel_to_tile(pygame.mouse.get_pos()) # for panelinfo!
        hero = Game.player
        #print("hero at ", hero.x, hero.y)
        x, y = Viewer.tile_to_pixel((self.tx , self.ty ))
        #x,y = Viewer.tile_to_pixel((self.tx-hero.x,self.ty-hero.y))
        self.pos = pygame.math.Vector2((x,y))
        super().update(seconds)


class FlyingObject(VectorSprite):
    """arrow, fireball etc: flies in a pre-defined path from one dungeon tile to another
       except arguments: start_tile, end_tile """

    def _overwrite_parameters(self):
        self.picture = Viewer.images["arrow"]
        print("arrow from", self.start_tile, "to", self.end_tile)
        self.pos = Viewer.tile_to_pixel(self.start_tile)
        if self.max_age is None:
            self.max_age = 2.0 # secs

        x1,y1 = self.start_tile
        x2,y2 = self.end_tile
        m = pygame.math.Vector2(x2,y2) - pygame.math.Vector2(x1,y1)
        dist = m.length()
        # calculate speed by dist and max_age
        speed = dist * Viewer.gridsize[0] / self.max_age
        m.normalize_ip()
        m *= speed
        self.move = m
        self.angle = -m.angle_to(pygame.math.Vector2(1,0))


class Bubble(VectorSprite):
    """a round fragment or bubble particle"""

    def _overwrite_parameters(self):
        self.speed = random.randint(10,50)
        if self.max_age is None:
            self.max_age = 0.5+random.random()*1.5
        self.kill_on_edge = True
        self.kill_with_boss = False # VERY IMPORTANT!!!
        if  self.move == pygame.math.Vector2(0,0):
            #self.move = pygame.math.Vector2(self.boss.move.x, self.boss.move.y)
            self.move = pygame.math.Vector2(1,0)
            #self.move.normalize_ip()
            self.move *= self.speed
            #a, b = 160, 200
        #else:
            a, b = 0, 360
        #    self.move = pygame.math.Vector2(self.speed, 0)
            self.move.rotate_ip(random.randint(a,b))
        #print("ich bin da", self.pos, self.move)


    def create_image(self):
        self.radius = random.randint(3,8)
        self.image = pygame.Surface((2*self.radius, 2*self.radius))
        r,g,b = self.color
        r+= random.randint(-30,30)
        g+= random.randint(-30,30)
        b+= random.randint(-30,30)
        r = between(r) # 0<-->255
        g = between(g)
        b = between(b)
        self.color = (r,g,b)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius )
        self.image.set_colorkey((0,0,0))
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
    max_tiles_x = 0  # max. dimension of an auto-generated dungeon level
    max_tiles_y = 0  # max. dimension of an auto-generated dungeon level
    effects = {} # effects for this dungeon level
    # lookup1: dx, dy -> index, start with north, then clockwise
    lookup_nesw = {(-1, 0): 0,
               (0, 1): 1,
               (1, 0): 2,
               (0, -1): 3}

    def __init__(self):
        self.create_dungeon([level1, level2])
        # extra food on2,4
        Food(2,4,0)

        ##create_dungeon([level1,])
        self.calculate_fov()
        #self.make_empty_effect_map()
        #Fire(3,2, max_age=4)  # extra effects
        #Fire(3,1, max_age=3)
        Game.turn_number = 0

    @staticmethod
    def make_empty_effect_map():
        #Game.effects = [ [None for element in line] for line in Game.dungeon[z] ]
        Game.effects = {}

    def process_effects(self):
        """next turn for each effect and remove destroyed effects"""
        for e in Game.effects.values():
            e.next_turn()
        Game.effects = {k:v for k,v in Game.effects.items() if not v.destroy} # remove destroyed effects

    @staticmethod
    def create_dungeon(list_of_raw_levels):
        for z, level in enumerate(list_of_raw_levels):
            new_level = []
            raw = [list(line) for line in level.splitlines() if len(line) > 1]
            for y, line in enumerate(raw):
                new_line = []
                for x, char in enumerate(line):
                    # wall and player need special treatment
                    if char == "@":  # Player
                        Game.player = Player(x, y, z)
                        new_line.append(Floor())  # player must stay on a tile
                    else:
                        ## if it's a Structure, calculate neighbors for nesw
                        ## otherwise, just make (Monster/Item) instance with x,y,z and add a Floor()
                        classnames = [x.__name__ for x in
                                      legend[char].mro()]  # classname.mro() displays all superclasses
                        myclass = legend[char]
                        if "Structure" in classnames:
                            #new_line.append(legend[char]())  # create new tile
                            #print("adding structure", char)
                            # find out what kind of neighbors we must look for
                            if myclass.nesw_tile is not None:
                                nesw = [False, False, False, False]  # N, E, S, W
                                for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                                    try:
                                        tile = raw[y + dy][x + dx]  # neighbor N,E,S,W ?
                                    except IndexError:
                                        continue # neighbor does not exist because outside dungeon
                                    if dy + y < 0 or dx + x < 0:
                                        continue  # python can have -1 as legal index!
                                    if tile == myclass.nesw_tile:
                                        nesw[Game.lookup_nesw[(dy, dx)]] = True
                                nesw = tuple(nesw)
                                new_line.append(myclass(nesw))
                            else:
                                new_line.append(myclass())
                        elif "Monster" in classnames:
                            new_line.append(Floor())
                            myclass(x, y, z)  # create new monster. the instance lives in Game.zoo automatically
                            #print("adding monster", char)
                        elif "Item" in classnames:
                            new_line.append(Floor())
                            myclass(x, y, z)  # create new item. the instance lives in Game.items automatically
                            #print("adding item", char)
                        else:
                            print("strange char in raw level detected... ")
                            raise ValueError("unknow char (not in legend) in level map:", char, "xyz:", x, y, z)
                new_level.append(new_line)
            Game.dungeon.append(new_level)
            #print("xy:", len(new_level), len(new_level[0]))

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
                Game.dungeon[z][y][x].fov = True  # make this tile visible and move to next point
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
            (Game.torch_radius, -Game.torch_radius, -1, 1, [(0, -1), (-1, 0), (-1, -1)]),
            (Game.torch_radius, Game.torch_radius, -1, -1, [(0, 1), (-1, 0), (-1, 1)])]:

            for x in range(px + xstart, px, xstep):
                for y in range(py + ystart, py, ystep):
                    # not even in fov?
                    try:
                        visible = Game.dungeon[pz][py][px].fov[y][x]
                    except:
                        continue
                    if visible:
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
        assumes that the dungeon is surronded by an outer wall
        hero can open a closed door if he has a spare key
        hero can strike at monster, monster can strike at hero
        """
        target = Game.dungeon[monster.z][monster.y + dy][monster.x + dx]
        legal = True  # we assume it is possible to move there
        text = []
        if isinstance(target, Wall):  # same as target.__class__.__name__
            legal = False
        if isinstance(target, Door) and target.closed:
            legal = False
            if (isinstance(monster, Player)):
                text.append("You run into a locked door")
                keys = len([i for i in Game.items.values() if i.backpack and
                            isinstance(i, Key)])
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
            for m in [m for m in Game.zoo.values() if m.z == monster.z and
                                                      m.number != monster.number and
                                                      m.friendly != monster.friendly and m.hp > 0 and
                                                      m.x == monster.x + dx and m.y == monster.y + dy]:
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
        if  isinstance(Game.dungeon[hero.z][hero.y][hero.x], StairUp):
            hero.z -= 1  # deeper down -> bigger z
            Game.effects = {} # clear all effects
            text.append("You climb one level up")
            #self.make_empty_effect_map()
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
            #self.make_empty_effect_map()
            self.calculate_fov()
        else:
            text.append("You must stay on a stair down to use this command")
        return text

    def turn(self, dx, dy):
        Game.turn_number += 1
        text = []
        hero = Game.player
        tile = Game.dungeon[hero.z][hero.y][hero.x]
        #recalc_fov = True
        # test if move is legal and move
        text.extend(self.move(hero, dx, dy))
        # ------- trigger ----
        ##if hero.z == 0 and hero.y == 4 and hero.x==1:
        ##    Flytext(text="Servus, trigger 1 getriggert")

        # found stair?
        tile = Game.dungeon[hero.z][hero.y][hero.x]
        if isinstance(tile, StairDown):
            text.append("You found a stair down. You can use the 'down' command now")
        if isinstance(tile, StairUp):
            text.append("You found a stair up. You can use the 'up' command now")
        # give hint when next to a door (all 8 directions)
        for (nx, ny) in ((0,-1), (1,-1), (1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1) ):
            tile2 = Game.dungeon[hero.z][hero.y+ny][hero.x+nx]
            if isinstance(tile2, Door) and not tile2.closed:
                text.append("You found an open door. You can press c to close it")
        # (auto)picking up item at current position
        for i in Game.items.values():
            if (i.z == hero.z and i.x == hero.x and i.y == hero.y
                    and not i.backpack):
                text.append(f"you pick up: {type(i).__name__}")
                i.backpack = True
                ## create Bubble effect here
                i.pickupeffect()

        # move the Monsters
        for m in [m for m in Game.zoo.values() if m.number != hero.number
                                                  and m.z == hero.z and m.hp > 0]:
            dxm, dym = m.ai()
            text.extend(self.move(m, dxm, dym))
        # cleanup code, remove dead monsters:
        for m in [m for m in Game.zoo.values() if m.hp <= 0]:
            if m.number == hero.number:
                #draw(hero.z)  # one last time draw the dungeon
                #c.print("You are dead")
                text.append("You are dead")
                return text
            del Game.zoo[m.number]
        self.calculate_fov()
        return text

class Effect:
    """an effect (Smoke, Fire, Water, Wind, Oil, etc) can not be
    picked up, but needs an underlaying dungoen structure
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
    pictures = [] # for animation
    anim_cycle = 6 # how many pictures per second the animation should display
    wobble = False  # if effect dances around center of tile each frame some pixel. can be False or Tuple(x,y)

    @classmethod
    def create_pictures(cls):
        pass

    def __init__(self, tx, ty, age = 0, max_age = None, dx=0, dy=0):
        self.number = Game.effectnumber
        Game.effectnumber += 1
        Game.effects[self.number] = self
        self.background = pygame.Surface((Viewer.gridsize[0], Viewer.gridsize[1])) # background rect from Viewer
        self.tx = tx # tile x
        self.ty = ty # tile y
        self.px, self.py = 0, 0 # pixel coordinate of topleft corner
        self.fov = False
        self.dx, self.dy = dx, dy # delta movement in tiles per turn
        #self.born = Game.turn_number + age         # effect appears as soon as age reach 0
        #self.age = Game.turn_number - self.born   #
        self.age = age # age in turns
        self.seconds = 0 # age in seconds
        self.max_age = max_age # effect disappears when age reaches max_age +1
        self.destroy = False
        self.kill_on_contact_with_wall = True # when effects wanders around and hit a wall-Destroy
        #self.char = "?"
        #self.text = "unknown effect"
        #self.fgcolor = (25,25,25)
        self.light_radius = 0 # if > 0 then the effect itself emits light (flame, fireball etc)

    def next_turn(self):
        #self.age = Game.turn_number - self.born
        self.age += 1
        #if self.max_age is not None and self.age > self.max_age:
        if self.max_age is not None and self.age > self.max_age:
            self.destroy = True
        self.tx += self.dx
        self.ty += self.dy
        # kill when effects leave level limit
        #print("level:", len(Game.dungeon[Game.player.z][0]), "x", len(Game.dungeon[Game.player.z]) )
        if self.tx < 0 or self.tx >= len(Game.dungeon[Game.player.z][0]):
            self.destroy = True
        if self.ty < 0 or self.ty >= len(Game.dungeon[Game.player.z]):
            self.destroy = True
        # kill when effect reaches a wall
        if self.kill_on_contact_with_wall:
            try:
                in_wall =  isinstance(Game.dungeon[Game.player.z][self.ty][self.tx], Wall)
            except IndexError:
                in_wall = True
            if in_wall:
                self.destroy = True

    def fovpicture(self, delta_t):
        """like sprite update -> expect time pased since last frame in seconds
           returns one of the pictures in self.pictures to update the animation"""
        pics = len(self.pictures)  # bacuase of scope, this works for classvariables of subclasses
        if pics == 0:
            return None
        self.seconds += delta_t
        i = int(self.seconds / (1 / self.anim_cycle) % pics) #
        return self.pictures[i]


class Fire(Effect):

    pictures =  []
    char = "*"
    wobble = (0,0)
    #text = "Fire"
    fgcolor = (255,0,0) # for panelinfo

    @classmethod
    def create_pictures(cls):
        """star changes color wildley between red and yellow"""
        colorvalues = list(range(128,256,16))
        random.shuffle(colorvalues)
        for c in colorvalues:
            #Fire.pictures.append(make_text(Fire.char, font_color=(255,c,0), font_size=64, max_gridsize=Viewer.gridsize))
            Fire.pictures.append(make_text(Fire.char,(255, c, 0)))
    #def __init__(self, tx, ty, age = 0, max_age = None, dx=0, dy=0 ):
    #    super().__init__(tx, ty, age, max_age, dx, dy)
    #    self.char = "*"
    #    self.text = "Fire"
    #    self.fgcolor = (255,0,0)



class Water(Effect):

    pictures = []
    char = "\u2248" # double wave instead of "~"
    fgcolor = (0,0,255)
    anim_cycle = 4

    @classmethod
    def create_pictures(cls):
        colorvalues = list(range(128, 256, 16))
        colorvalues.extend(list(range(255, 127, -16)))
        for c in colorvalues:
            pic = make_text(Water.char, (0,0,c))
            if c%2 == 0: #the first half values (ascending)
                Water.pictures.append(pic)
            else:        # the second half (descending)            x     y
                Water.pictures.append(pygame.transform.flip(pic, False, True))


    #def __init__(self, x, y, age=0, max_age=None, dx=0, dy=0):
    #    super().__init__(x, y, age, max_age, dx, dy )
    #    self.char = "~"
    #    self.text = "Water"
    #    self.fgcolor = (0, 0, 255)

class Flash(Effect):

    pictures = [] # necessary!
    char = "\u26A1"
    fgcolor = (0,200,200) # cyan
    anim_cycle = 25 # so many pictures per second

    @classmethod
    def create_pictures(cls):
        """create a spiderweb of withe-blue lines, cracling from the center of tile to it's edge"""
        pic1 = make_text("\u26A1", (0,0,255))
        pic2 = make_text("\u26A1", (220,220,255))
        pic3 = pygame.transform.flip(pic1, False, True)
        pic4 = pygame.transform.flip(pic2, False, True)
        cls.pictures = [pic1,pic2,pic3,pic4]
        #return


class Structure:
    """a structrue can not move and can not be picked up
       structures do not have a x,y,z coordinate because they
       exist only in the dungeon array. the position inside
       the array equals to x,y. See Wall class docstring for detecting neighbors
       """
    fgcolor = (0,150,0)
    block_sight = False
    block_movement = False
    block_shooting = False
    nesw_tile = None # if this is a char, fill self.nesw with True for north, east, south, west neigbors

    @classmethod
    def create_pictures(cls):   # will be called once from class Viewer.load_images to create fovpicture and exploredpicture
        pass

    def __init__(self, nesw=None):
        self.explored = False  # stay visible on map, but with fog of war
        self.fov = False  # currently in field of view of player?
        self.char = None # for textual representation btw for make_text(char)
        self.nesw = nesw # neighboring tiles of the same structure, . tuple of 4 boools: north, east, south, west

    def exploredpicture(self):
        return None

    def fovpicture(self):
        return None


class Floor(Structure):

    def __init__(self):
        super().__init__()
        self.char = " "


class Wall(Structure):
    """walls have a specail char depending on neighboring walls
    Viewer.load_images calls once Wall.create_pictures()
    Wall.create_pictures fill the exploredpictures and fovpictures dicts with the correct bitmaps
    When creating a wall instance, Game.create_dungeon checks nesw_tile and fills self.nesw with a tuple,
    representing other wall neigbors north, east, sout or west of this instance. (For example: (True,False,False,False)
    when the instance has one wall neighbor north of itself.
    when Viewer.paint_tiles "paint" the Structure instances, it calls wallinstance.exploredpicture() or wallinstance.fovpicture()
    to get the correct bitmap to blit
    """
    # use font instead of freetype so that bloxdrawing chars are better centered (no need to calculate center for each box tile)
    fgcolor = (0,150,0)
    block_sight = True
    block_movement = True
    block_shooting = True
    nesw_tile = "#"   # wall
    exploredpictures = {}
    fovpictures = {}
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
        (False, False, True, False): "\u2565",  # terminate from south
        (False, False, False, True): "\u2561",  # terminate from west
        (False, True, False, False): "\u255E",  # terminate from east
        (True, False, False, False): "\u2568",  # terminate from north
    }

    @classmethod
    def create_pictures2(cls):
        for k,v in cls.lookup.items():
            fontsize = 64
            #Viewer.font.origin = True
            tmp = pygame.Surface(Viewer.gridsize)
            tmp.set_colorkey((0,0,0))
            tmp.convert_alpha()
            rect = Viewer.font.get_rect(v, size=fontsize) # --> origin x,y, width of recht, height of rect
            rx,ry,rwidth,rheight = rect
            bx = Viewer.gridsize[0]//2- (rx+rwidth//2)
            by = Viewer.gridsize[1]//2- (ry-rheight//2)
            print(rect, rect.center, bx, by)


            #print(v, rect)
            ##  render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0) -> Rect
            #(rect[0],rect[1])
            rect2 = Viewer.font.render_to(tmp, (bx,by), v, fgcolor=cls.fgcolor, size=fontsize )
            #pic, rect  = Viewer.font.render(v, fgcolor=cls.fgcolor, size=24)
            cls.fovpictures[k] = tmp
            tmp2 = pygame.Surface(Viewer.gridsize)
            tmp2.set_colorkey((0, 0, 0))
            tmp2.convert_alpha()
            rect2 = Viewer.font.render_to(tmp2, (bx,by), v, fgcolor=Viewer.explored_fgcolor, size=fontsize)
            cls.exploredpictures[k] = tmp
        #input("...Enter..")


    @classmethod
    def create_pictures(cls):
        Wall.exploredpictures = { k: make_text(v,Viewer.explored_fgcolor, mono=True, size=Viewer.wallfontsize) for k,v in Wall.lookup.items()}
        Wall.fovpictures = { k: make_text(v,cls.fgcolor, mono=True, size=Viewer.wallfontsize) for k,v in Wall.lookup.items()}


    def __init__(self, nesw):
        super().__init__(nesw)
        self.char = Wall.lookup[self.nesw]

    def exploredpicture(self):
        """expecting self.nesw set by Game.create_dungeon"""
        return Wall.exploredpictures[self.nesw]

    def fovpicture(self):
        """expecting self.nesw set by Game.create_dungeon"""
        return Wall.fovpictures[self.nesw]


class Door(Structure):
    """locked doors can be opened by keys.
       doors can be closed again by player, but not locked again.
       by default, doors are locked"""
    # USE font instead of freetype so that doors get not expanded (ugly)
    fgcolor = (140,100,0)
    nesw_tile = "#" # wall. a door can only be between walls

    @classmethod
    def create_pictures(cls):
        Door.exploredpicture_closed_v = make_text("|",Viewer.explored_fgcolor)
        Door.exploredpicture_closed_h = make_text("-", Viewer.explored_fgcolor)
        Door.fovpicture_closed_v = make_text("|", cls.fgcolor)
        Door.fovpicture_closed_h = make_text("-", cls.fgcolor)
        Door.exploredpicture_open = make_text(".",Viewer.explored_fgcolor)
        Door.fovpicture_open = make_text(".", cls.fgcolor)



    def __init__(self, nesw):
        super().__init__(nesw)
        if nesw[0] and nesw[2]: # wall north and south
            self.char = "|"
        elif nesw[1] and nesw[3]: # wall east and west
            self.char = "-"
        self.closed = True
        self.block_sight = True
        self.block_movement = True
        self.block_shooting = True  # set false for grille door etc.
        self.locked = True  # key is needed to open


    def open(self):
        self.closed = False
        self.char = "."
        self.block_sight = False
        self.block_movement = False
        self.block_shooting = False
        self.locked = False

    def close(self):
        if self.nesw[0] and self.nesw[2]:  # wall north and south
            self.char = "|"
        elif self.nesw[1] and self.nesw[3]:  # wall east and west
            self.char = "-"
        self.closed = True
        self.locked = False  # key is not needed again
        self.block_sight = True
        self.block_movement = True
        self.block_shooting = True  # set false for grille door etc.

    def exploredpicture(self):
        if  self.closed:
            if self.char == "|":
                return Door.exploredpicture_closed_v
            if self.char == "-":
                return Door.exploredpicture_closed_h
        return Door.exploredpicture_open

    def fovpicture(self):
        if self.closed:
            if self.char == "|":
                return Door.fovpicture_closed_v
            if self.char == "-":
                return Door.fovpicture_closed_h
        return Door.fovpicture_open


class StairDown(Structure):

    fgcolor = (150,50,90) # dark pink

    @classmethod
    def create_pictures(cls):
        StairDown.exploredpic = make_text("\u21A7",Viewer.explored_fgcolor)
        StairDown.fovpic = make_text("\u21A7",cls.fgcolor)

    def __init__(self): # unneccesary ?
        super().__init__()
        self.char = "\u21A7"  # downwards arrow from bar

    def exploredpicture(self):
        return StairDown.exploredpic

    def fovpicture(self):
        return StairDown.fovpic


class StairUp(Structure):

    fgcolor = (60,200,200) # cyan

    @classmethod
    def create_pictures(cls):
        StairUp.exploredpic = make_text("\u21A5",Viewer.explored_fgcolor)
        StairUp.fovpic = make_text("\u21A5",cls.fgcolor)

    def __init__(self):   # unneccesary ?
        super().__init__()
        self.char = "\u21A5"  # upwards arrow from bar

    def exploredpicture(self):
        return StairUp.exploredpic

    def fovpicture(self):
        return StairUp.fovpic

class Item:
    """Items can be picked up by the player
    if carried by player, the items x,y,z attributes are meaningless
    and the items backpack attribute must be set to True"""

    pictures = []
    char = "?"  # for panelinfo
    fgcolor = (0,255,0) # for panelinfo

    @classmethod
    def create_pictures(cls):
        pass

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
        Flytext(pos=posvector,
                move=pygame.math.Vector2(0, -20), text=ftext, color=self.fgcolor, fontsize=25)
        for _ in range(number_of_bubbles):
            posvector = pygame.math.Vector2(px, py)  # its necessary. comment out this line for funny effect
            m = pygame.math.Vector2(random.random() * 20 + 25) # speed
            m.rotate_ip(random.randint(0, 360))
            # x,y = Viewer.tile_to_pixel((self.x,self.y))
            Bubble(pos=posvector, color=self.fgcolor,
                   move=m)

    def pickupeffect(self):
        self.flytext_and_bubbles()

    def fovpicture(self):
        return self.pictures[0]



class Coin(Item):

    pictures = []
    char = "$"
    fgcolor = (255,255,0) # yellow

    @classmethod
    def create_pictures(cls):        # yellow circle, inside text with $ symbol
        #pic = pygame.Surface((Viewer.gridsize[0], Viewer.gridsize[1]))
        #pic.set_colorkey((0,0,0)) # black is transparent
        #half_width = Viewer.gridsize[0]//2
        #half_height = Viewer.gridsize[1]//2
        #radius = min(half_width, half_height)
        #pygame.draw.circle(pic, cls.fgcolor, (half_width,half_height), radius)
        symbol = make_text(cls.char, (255,255,0))
        #pic.blit(symbol, (0,0))
        #pic.convert_alpha()
        #cls.pictures.append(pic)
        cls.pictures.append(symbol)


    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.value = random.choice((1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 5, 5, 10))

    def pickupeffect(self):
        self.flytext_and_bubbles(ftext=f"found {self.value} gold!", number_of_bubbles=self.value*5)


class Key(Item):

    pictures = []
    fgcolor = (255,255,255)
    char = "k"

    @classmethod
    def create_pictures(cls):
        cls.pictures.append(Viewer.images["key"])

class Food(Item):

    pictures = []
    char = "\u2615"
    fgcolor = (200,0,200)

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.food_value = random.randint(1, 3)

    @classmethod
    def create_pictures(cls):
        #cls.pictures.append(Viewer.images["food"])
        cls.pictures.append(make_text("\u2615", cls.fgcolor))

    def pickupeffect(self):
        lookup = {1: "edible food",
                  2: "good food",
                  3: "fantastic food"}
        self.flytext_and_bubbles(lookup[self.food_value], self.food_value*5)


class Monster():
    """Monsters can move around"""

    pictures = []
    fgcolor = (255,0,0) # red
    char = "\U0001F608" #"M"

    @classmethod
    def create_pictures(cls):
        pic = make_text(cls.char, cls.fgcolor)
        cls.pictures.append(pic)

    def __init__(self, x, y, z):
        self.number = Game.monsternumber  # get unique monsternumber
        Game.monsternumber += 1  # increase global monsternumber
        Game.zoo[self.number] = self  # store monster into zoo
        self.x = x
        self.y = y
        self.z = z
        self.hp = 10 # this MUST be an instance attribute because each monster has individual hp
        #self.fgcolor = (255,0,0)# "red"
        self.friendly = False  # friendly towards player?
        #self.char = "M"  # Monster

    def ai(self):
        dx = random.choice((0, 0, 0, 1, -1,))
        dy = random.choice((0, 0, 0, 1, -1,))
        return dx, dy

    def fovpicture(self):
        #print("returning fovpicture of", self.__class__.__name__)
        return self.pictures[0]


class Dragon(Monster):

    pictures =[]
    fgcolor = (255,90,0) # orange
    char = "D"

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.friendly = False  # friendly towards player?

    def ai(self):
        # ---fire spitting---
        if Game.dungeon[self.z][self.y][self.x]:  # visible?
            if random.random() < 0.2:
                can_shoot = calculate_line((self.x, self.y), (Game.player.x, Game.player.y), Game.player.z,
                                           modus="shoot")
                if can_shoot:
                    #print("feuerspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:6]:
                        Fire(f[0], f[1], max_age=3)

        dx = random.choice((0, 0, 0, 1, -1,))
        dy = random.choice((0, 0, 0, 1, -1,))
        return dx, dy


class SkyDragon(Monster):

    pictures = []
    fgcolor = (0,0,200) # cyan
    char = "S"

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.friendly = False  # friendly towards player?

    def ai(self):
        # ---fire spitting---
        if Game.dungeon[self.z][self.y][self.x]:  # visible?
            if random.random() < 0.1:
                can_shoot = calculate_line((self.x, self.y), (Game.player.x, Game.player.y), Game.player.z,
                                           modus="shoot")
                if can_shoot:
                    #print("feuerspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:10]:
                        Flash(f[0], f[1], max_age=1)

        dx = random.choice((0, 0, 0, 1, -1,))
        dy = random.choice((0, 0, 0, 1, -1,))
        return dx, dy

class Waterguy(Monster):

    pictures = []
    fgcolor = (0,0,255) # blue
    char = "W"

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 25
        self.friendly = False  # friendly towards player?

    def ai(self):
        # ---water spitting---
        if Game.dungeon[self.z][self.y][self.x]:  # visible?
            if random.random() < 0.5:
                can_shoot = calculate_line((self.x, self.y), (Game.player.x, Game.player.y), Game.player.z,
                                           modus="shoot")
                if can_shoot:
                    #print("wasserspucke")
                    points = get_line((self.x, self.y), (Game.player.x, Game.player.y))
                    for f in points[:6]:
                        Water(f[0], f[1], max_age=3)

        dx = random.choice((0, 0, 0, 0, 0, 0, 1, -1,))
        dy = random.choice((0, 0, 0, 0, 0, 0, 1, -1,))
        return dx, dy



class Player(Monster):

    pictures = []
    char =   "\u263A"#"\u263A"  #heart: "\u2665" # music:"\u266B"  # sun "\u2609" #thunderstorm: "\u2608" #lighting: "\u2607" # double wave: "\u2248"  # sum: "\u2211" 3stars:  "\u2042" # "@"
    fgcolor = (0,0,255)

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 50
        self.friendly = True
        # self.backpack = [] # container for transported items



class Viewer:
    width = 0
    height = 0
    midscreen = (0,0)
    gridsize = (1,1)
    panelwidth = 0
    logheight = 0
    hudheight = 0 # height of hud on top of screen, for displaying hitpoints etc
    fontsize = 0
    font = None
    monofont = None
    allgroup = None # pygame sprite Group for all sprites
    explored_fgcolor  = (0,100,0)
    explored_bgcolor  = (10,10,10)
    toplefttile = [0,0]      # tile coordinate of topleft corner of currently visible tile on screen
    bottomrighttile = [0, 0] # tile coordinate of bottomright corner of currently visible tile on screen
    images = {}
    radardot = [1,1]
    #playergroup = None # pygame sprite Group only for players

    def __init__(self,width=800, height=600, gridsize=(48,48), panelwidth=200, logheight=100, fontsize = 64,
                 wallfontsize= 72, max_tiles_x = 200, max_tiles_y = 200 ):

        Viewer.width = width
        Viewer.height = height
        Viewer.gridsize = gridsize
        Viewer.panelwidth = panelwidth
        self.midradar = (Viewer.panelwidth // 2, Viewer.panelwidth //2)
        Viewer.logheight = logheight
        Viewer.midscreen = ((width - panelwidth) // 2,(height-logheight-Viewer.hudheight) //2)
        Viewer.fontsize = fontsize
        Viewer.wallfontsize = wallfontsize
        Game.max_tiles_x = max_tiles_x
        Game.max_tiles_y = max_tiles_y



        # ---- pygame init
        pygame.init()
        #Viewer.font = pygame.font.Font(os.path.join("data", "FreeMonoBold.otf"),26)
        fontfile = os.path.join("data", "fonts", "DejaVuSans.ttf")
        Viewer.monofontfilename = os.path.join("data", "fonts", "FreeMonoBold.otf")
        Viewer.font = pygame.freetype.Font(fontfile)
        #Viewer.monofont = pygame.freetype.Font(monofontfile)
        #Viewer.monofont = pygame.font.Font(monofontfile)



        # ------ joysticks init ----
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for j in self.joysticks:
            j.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.playtime = 0.0





        # ------ background images ------
        self.backgroundfilenames = []  # every .jpg or .jpeg file in the folder 'data'
        self.make_background()
        self.load_images()
        self.panelscreen = pygame.Surface((Viewer.panelwidth, Viewer.height - Viewer.panelwidth))
        self.radarscreen = pygame.Surface((Viewer.panelwidth, Viewer.panelwidth))  # square in topright corner
        self.logscreen = pygame.Surface((Viewer.width, Viewer.height - Viewer.logheight))
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
        Viewer.images["main"] = pygame.image.load(os.path.join("data","from_stone_soup", "main.png")).convert_alpha()
        # --- sub-images from main.png:
        tmp = pygame.Surface.subsurface(Viewer.images["main"], (808, 224, 22, 7)) # arrow
        Viewer.images["arrow"] = pygame.transform.scale(tmp, (35,8))

        tmp = pygame.Surface.subsurface(Viewer.images["main"], (22,840,16,16)) # flame1
        Viewer.images["flame1"] = pygame.transform.scale(tmp, (32, 32))
        tmp = pygame.Surface.subsurface(Viewer.images["main"], (40, 840, 16, 16))  # flame2
        Viewer.images["flame2"] = pygame.transform.scale(tmp, (32, 32))
        tmp = pygame.Surface.subsurface(Viewer.images["main"], (56, 840, 16, 16))  # flame3
        Viewer.images["flame3"] = pygame.transform.scale(tmp, (32, 32))
        # ---- direct images ---
        tmp = pygame.image.load(os.path.join("data","goldchest.png")).convert_alpha()
        Viewer.images["gold"] = pygame.transform.scale(tmp, (35,35))

        tmp = pygame.image.load(os.path.join("data", "old_key.png")).convert_alpha()
        Viewer.images["key"] = pygame.transform.scale(tmp, (35,35))

        tmp = pygame.image.load(os.path.join("data", "food1.png")).convert_alpha()
        Viewer.images["food"] = pygame.transform.scale(tmp, (35,35))

        # image for structure tiles ( wall ) -> iterate over all subclasses of Structure and call cls.create_pictures()
        for sc in Structure.__subclasses__():
            sc.create_pictures()
        # image creation for Effects:
        #print("creating effect pictures..")
        for sc in Effect.__subclasses__():
            #print(sc)
            sc.create_pictures()

        for sc in Item.__subclasses__():
            sc.create_pictures()
        for sc in Monster.__subclasses__():
            sc.create_pictures()
        Monster.create_pictures()


    def make_radar(self):
        self.radarscreen.fill((0,0,0)) # fill black
        hero = Game.player
        midx = self.midradar[0] - int(Viewer.radardot[0]//2)
        midy = self.midradar[1] - int(Viewer.radardot[1] // 2)
        for y, line in enumerate(Game.dungeon[hero.z]):
            for x, tile in enumerate(Game.dungeon[hero.z][y]):
                if not tile.explored:
                    continue
                elif isinstance(tile, Floor):
                    color = (50,50,50)
                elif isinstance(tile, Wall):
                    color = (0,128,0) # mid green
                elif isinstance(tile, StairUp):
                    color = (0, 128,128)
                elif isinstance(tile, StairDown):
                    color = (128,0,128)
                elif isinstance(tile, Door):
                    color = (0,64,0)
                else:
                    color = (255,2550,0) # alarm for unknow tile
                pygame.draw.rect(self.radarscreen, color, (midx-Viewer.radardot[0]*(-x +hero.x),
                                                           midy-Viewer.radardot[1]*(-y +hero.y),
                                                           Viewer.radardot[0], Viewer.radardot[1])  )
        # -- monster
        for m in Game.zoo.values():
           # print("dungeonxy: ", len(Game.dungeon[hero.z][0]),len(Game.dungeon[hero.z]) )
           # print("mxyz", m.x, m.y, m.z, m)
           # print("dungeon line0", Game.dungeon[hero.z][0])
           # print("dungeon line1", Game.dungeon[hero.z][1])
           # print("len1", len(Game.dungeon[hero.z][1]))
            if m.hp > 0 and m.z == hero.z and Game.dungeon[hero.z][m.y][m.x].fov:
                pygame.draw.rect(self.radarscreen, m.fgcolor, (midx - Viewer.radardot[0] * (-m.x + hero.x),
                                                           midy - Viewer.radardot[1] * (-m.y + hero.y),
                                                           Viewer.radardot[0], Viewer.radardot[1]))




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

        self.background = pygame.transform.scale(self.background,
                                                 (Viewer.width, Viewer.height))
        self.background.convert()

    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        Viewer.allgroup = pygame.sprite.LayeredUpdates()  # for drawing with layers
        Viewer.playergroup  = pygame.sprite.OrderedUpdates() # a group maintaining order in list
        Viewer.cursorgroup = pygame.sprite.Group()
        Viewer.bluegroup = pygame.sprite.Group()
        Viewer.flygroup = pygame.sprite.Group()
        #Viewer.effectgroup = pygame.sprite.Group() # dirtygroup?
        #self.bulletgroup = pygame.sprite.Group() # simple group for collision testing only
        #self.tracergroup = pygame.sprite.Group()
        #self.mousegroup = pygame.sprite.Group()
        #self.explosiongroup = pygame.sprite.Group()
        self.flytextgroup = pygame.sprite.Group()
        self.fxgroup = pygame.sprite.Group() # for special effects

        #Mouse.groups = self.allgroup, self.mousegroup
        #Player.groups = self.allgroup, self.playergroup
        #Beam.groups = self.allgroup, self.bulletgroup
        TileCursor.groups = self.cursorgroup
        BlueTile.groups = self.bluegroup, self.allgroup
        VectorSprite.groups = self.allgroup
        #SpriteEffect.groups =  self.effectgroup
        Bubble.groups = self.allgroup, self.fxgroup # special effects
        Flytext.groups = self.allgroup, self.flytextgroup
        FlyingObject.groups = self.allgroup, self.flygroup
        #Explosion.groups = self.allgroup, self.explosiongroup
        # -------- create necessary sprites -----
        self.cursor  = TileCursor()
        #self.cursor.visible = False

    def make_panel(self):
        # in topright corner of screen is the radarscreen: panelwidth  x panelwidth
        # the height of panelscreen is therefore Viewer.height - panelwidth
        self.panelscreen.fill((200,200,0))
        write(self.panelscreen, "the panel \u2566\u2569",5,5,(0,0,255), 24, origin="topleft")
        z = Game.player.z
        tiles_x = len(Game.dungeon[z][0])  # z y x
        tiles_y = len(Game.dungeon[z])
        # --- player stats ----
        keys = len([i for i in Game.items.values()
                    if isinstance(i, Key) and i.backpack])
        gold = sum([i.value for i in Game.items.values()
                    if isinstance(i, Coin) and i.backpack])
        food = len([i for i in Game.items.values()
                    if isinstance(i, Food) and i.backpack])
        text = "{}   :{}    :{}".format(keys, gold, food)
        write(self.panelscreen, f"{Game.turn_number}: x:{Game.player.x} y:{Game.player.y} z:{z + 1} {tiles_x}x{tiles_y} ", 5, 150, font_size=13)
        # ----- hp
        write(self.panelscreen, "\u2665", 0, 165, color=(255,0,0), font_size=40,) # red heart
        write(self.panelscreen, "{:>3}".format(Game.player.hp), 25,170, font_size=32) # hp text
        # ---- gold
        self.panelscreen.blit(Viewer.images["gold"], (90, 170))  # gold chest
        write(self.panelscreen, "{:>3}".format(gold), 130, 170, font_size=32) # gold text
        # ---- keys
        self.panelscreen.blit(Viewer.images["key"], (-5, 200))
        write(self.panelscreen, "{:>3}".format(keys), 25, 200, font_size=32)  # gold text
        # --- food
        self.panelscreen.blit(Viewer.images["food"], (90, 200))
        #write(self.panelscreen, "\u2615", 90, 200, color=(255,0,255), font_size=32) # unicode sign for coffe
        write(self.panelscreen, "{:>3}".format(food), 130, 200, font_size=32)  # gold text


    def make_log(self):
        #self.logscreen = pygame.Surface((Viewer.width, Viewer.height - Viewer.logheight))
        self.logscreen.fill((64,64,64))
        for y in range(-1, -16, -1):  # write the last 15 lines
            try:
                line = self.loglines[y]
            except IndexError:
                continue
            i = len(self.loglines) + y +1
            #c = i%5
            write(self.logscreen, f"{i}: {self.loglines[y]}", 5 , Viewer.logheight - y * -24, (0,0,50 + i%5 * 40), 24, origin = "topleft")

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
            return (dtpx, dtpy) # can be everywhere, even outside of dungeon
        else: # calculate absolute position of tile
            dtpx += hero.x
            dtpy += hero.y
            #print("bevore between:", dtpx, dtpy, end="")
            #print("len y", len(Game.dungeon[hero.z][0])-1)
            #print("len y", len(Game.dungeon[hero.z])-1)
            dtpx = between(dtpx, Viewer.toplefttile[0], Viewer.bottomrighttile[0])
            dtpy = between(dtpy, Viewer.toplefttile[1], Viewer.bottomrighttile[1])
            #print("after between:", dtpx, dtpy)
            return (dtpx, dtpy)

    def paint_tiles(self):
        #print("effecs:", Game.effects) # destroyed effects are removed in calculate_fov -> process_effects
        for e in Game.effects.values():
            e.fov = False  # clear old fov information
        z = Game.player.z
        dungeon = Game.dungeon[z]
        tiles_x = len(Game.dungeon[0][0]) # z y x
        tiles_y = len(Game.dungeon[0])
        exploredfg = Viewer.explored_fgcolor # (0,100,0)
        exploredbg = Viewer.explored_bgcolor # (10,10,10)
        Viewer.toplefttile = [tiles_x,tiles_y] # start with absurd values
        Viewer.bottomrighttile = [-1,-1]
        for ty, line in enumerate(dungeon):
            for tx, tile in enumerate(line):
                x,y = Viewer.tile_to_pixel((tx,ty))
                if y < 0 or y > Viewer.height - Viewer.logheight -Viewer.hudheight - Viewer.gridsize[1]:
                    break # continue with next ty
                if x < 0 or x > Viewer.width - Viewer.panelwidth - Viewer.gridsize[0]:
                    continue # next tx
                # update visible tiles on screen information -> shrink rect of visible tiles
                Viewer.toplefttile[0] = min(tx, Viewer.toplefttile[0])
                Viewer.bottomrighttile[0] = max(tx, Viewer.bottomrighttile[0])
                Viewer.toplefttile[1] = min(ty, Viewer.toplefttile[1])
                Viewer.bottomrighttile[1] = max(ty, Viewer.bottomrighttile[1])

                # correction for center (necessary because drawing/blitting from topleft center)
                x -= Viewer.gridsize[0] // 2
                y -= Viewer.gridsize[1] // 2
                # paint on tile on the pygame sreen surface
                if not tile.fov:  # ---- outside fov ----- not in players field of view
                    if tile.explored:  # known from previous encounter
                        pygame.draw.rect(self.screen, exploredbg, (x,y,Viewer.gridsize[0], Viewer.gridsize[1])) # fill
                        #char = make_text(tile.char, font_color=exploredfg,  font_size=48, max_gridsize=Viewer.gridsize)
                        pic = tile.exploredpicture()
                        if pic is not None:
                            self.screen.blit(pic, (x, y)) # blit from topleft corner
                    else:         # invisible, black on black
                        pygame.draw.rect(self.screen, (0,0,0), (x, y, Viewer.gridsize[0], Viewer.gridsize[1]))  # fill
                else:    # ---- inside fov ----- , --> tile.gbcolor for background
                    pygame.draw.rect(self.screen, tile.bgcolor, (x,y,Viewer.gridsize[0], Viewer.gridsize[1]))
                    # effect is blocking items, but not monsters
                    monstercounter = 0
                    monsters =  [m for m in Game.zoo.values() if m.z == z and m.y == ty and m.x == tx and m.hp > 0]
                    monstercounter = len(monsters)
                    for m in monsters:
                            #char = make_text(monster.char, font_color=monster.fgcolor, font_size=48, max_gridsize=Viewer.gridsize)
                        #self.screen.blit(char, (x, y))  # blit from topleft corner
                        self.screen.blit(m.fovpicture(), (x,y))
                            #break # no more than one monster per tile
                    monstercounter = len(monsters)
                    # always paint effect, if necessary paint effect OVER monster
                    # calculate effect animation coordinates and fov ( effect will be painted in Viewer.run

                    for e in [e for e in Game.effects.values() if e.tx == tx and e.ty == ty and e.age >=0 ]:
                            e.fov = True
                            e.px, e.py = x, y
                            # no break because multiple effects per tile are possible
                            # blitting of effect will be done in Viewer.paint_animation because all effects have animations
                    if monstercounter == 0:
                        # monster is blocking items
                        itemcounter = 0
                        items = [i for i in Game.items.values() if i.z == z and i.y == ty and i.x == tx  and not i.backpack]
                        itemcounter = len(items)
                        if itemcounter > 1:
                            # blit 'infinite' symbol if more than one items are at one tile
                            char = make_text("\u221E", (255,200,50))  # infinity sign
                            self.screen.blit(char, (x, y))  # blit from topleft corner
                        elif itemcounter == 1:
                            #self.screen.blit(char, (x, y))  # blit from topleft corner
                            self.screen.blit(items[0].fovpicture(), (x,y))
                        elif itemcounter == 0:
                            # paint the structure pic
                            pic = tile.fovpicture()
                            if pic is not None:
                                self.screen.blit(pic, (x, y))  # blit from topleft corner

                    # save screenrect background for effect at this place
                    for e in [e for e in Game.effects.values() if e.tx == tx and e.ty == ty and e.age >= 0]:
                        # where to blit ( what to blit, (where on dest topleftxy), (rect-area of source to blit )
                        e.background.blit(self.screen, (0,0), (e.px,e.py,Viewer.gridsize[0], Viewer.gridsize[1]))
                # paint grid rect
                pygame.draw.rect(self.screen, (128,128,128), (x,y,Viewer.gridsize[0], Viewer.gridsize[1]),1 )

    def paint_animation(self, seconds):
        """update animated tiles (effects) between player turns
           all visible effects have .fov set to True (done by self.paint_tiles)
           and all visible effects have already .px and .py for topleft corner in pixel (also by self.paint_tiles)
           seconds is time passed since last frame (from Viewer.run)
           """
        for e in [e for e in Game.effects.values() if e.fov]:
            # blit first backup screen from last frame (without sprites/effects)
            #self.screen.blit(self.screen_backup, (e.px, e.py), (0,0,Viewer.gridsize[0], Viewer.gridsize[1]))

            self.screen.blit(e.background, (e.px, e.py))
            # blit effect picture on top
            if e.wobble:  # e.wobble is either False or a xy tuple
                wobble_x = random.randint(-e.wobble[0], e.wobble[0])
                wobble_y = random.randint(-e.wobble[1], e.wobble[1])
            else:
                wobble_x = 0
                wobble_y = 0
            self.screen.blit(e.fovpicture(seconds), (e.px+wobble_x, e.py+wobble_y))



    def panelinfo(self):
        """overwrites a piece of the panel with info about the objects currently under the cursor"""
        tx, ty = self.cursor.tx, self.cursor.ty
        #print("from cursor:", tx, ty)
        hero = Game.player
        try:
            tile = Game.dungeon[hero.z][ty][tx]
        except IndexError:
            return
        items = []
        monsters = []
        effects = []
        if not tile.explored:
            text = "unexplored tile"
        else:
            if isinstance(tile, Door):
                text = "{} door".format("a locked" if tile.locked else "a closed" if tile.closed else "an open")
            else:
                text = tile.__class__.__name__
        if tile.fov:
            for e in [e for e in Game.effects.values() if e.tx == tx and e.ty == ty and e.age >= 0]:
                effects.append(e)
            for i in [i for i in Game.items.values() if not i.backpack and i.z == hero.z and i.x == tx and i.y == ty]:
                items.append(i)
            for m in [m for m in Game.zoo.values() if m.hp > 0 and m.z == hero.z and m.x == tx and m.y == ty]:
                monsters.append(m)
        # ---- print to panel
        y = 400
        pygame.draw.rect(self.panelscreen, (150, 150, 0), (0, y, Viewer.panelwidth, Viewer.height - y))
        write(self.panelscreen, tile.char, 0, y-0, (0, 150, 0), font_size=25)
        y += 5
        write(self.panelscreen, text, 50, y, (0, 0, 0), font_size=12)
        for e in effects:
            y += 15
            write(self.panelscreen, e.char, 0, y, e.fgcolor, font_size=20)
            write(self.panelscreen, e.__class__.__name__, 50, y, (0, 0, 0), font_size=12)
        for m in monsters:
            y += 15
            write(self.panelscreen, m.char, 0, y, m.fgcolor, font_size=20)
            write(self.panelscreen, m.__class__.__name__, 50, y, (0, 0, 0), font_size=12)
        for i in items:
            y += 15
            write(self.panelscreen, i.char, 0, y, i.fgcolor, font_size=20)
            write(self.panelscreen, i.__class__.__name__, 50, y, (0, 0, 0,), font_size=12)

    def run(self):
        """The mainloop"""
        running = True
        repaint = True
        text = []
        cursormode = False
        selection = None
        hero =Game.player
        #pygame.mouse.set_visible(False)
        oldleft, oldmiddle, oldright = False, False, False
        pygame.display.set_caption("pipe_rogue version:".format(version))
        Flytext(pos=pygame.math.Vector2(Viewer.width//2,Viewer.height//2), text="Enjoy pipe_rogue!", fontsize=48,
                max_age = 3)
        #Flytext(text="press h for help", age=-2)
        #self.screen_backup = self.screen.copy()
        # --------extra effects at start of game --------------
        Fire(3,1, max_age=5)
        Fire(3,2, max_age=7)
        Fire(1,2, max_age=10)
        Water(4,1, max_age=10)
        Water(5,1, max_age=10)
        while running:
            #print(pygame.mouse.get_pos(), Viewer.pixel_to_tile(pygame.mouse.get_pos()))
            #print(self.playergroup[0].pos, self.playergroup[0].cannon_angle)
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if cursormode:
                        if event.key == pygame.K_ESCAPE:
                            cursormode = False
                            #self.cursor.visible = False
                        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                            selection = self.pixel_to_tile(pygame.mouse.get_pos())
                            print("selected: ", selection)
                            cursormode = False
                    else:
                        #if event.key == pygame.K_1:
                        #    # testing bluegroup
                        #    cell = self.pixel_to_tile(pygame.mouse.get_pos())
                        #    px,py = self.tile_to_pixel(cell)
                        #    BlueTile(pos=pygame.math.Vector2(px,py))

                        if event.key == pygame.K_ESCAPE:
                            running = False
                        if event.key == pygame.K_f: # start selection with cursor (mouse)
                            cursormode = True
                            selection = None # clear old selection
                            #self.cursor.visible=True
                        if event.key == pygame.K_PLUS:
                            Viewer.radardot = [min(Viewer.panelwidth //4 ,i * 2) for i in Viewer.radardot]
                            self.make_radar()
                        if event.key == pygame.K_MINUS:
                            Viewer.radardot = [max(1, i//2) for i in Viewer.radardot]
                            self.make_radar()
                        if event.key == pygame.K_w:
                            self.loglines.extend(self.g.turn(0,-1))
                            repaint = True
                        if event.key == pygame.K_s:
                            self.loglines.extend(self.g.turn(0,1))
                            repaint = True
                        if event.key == pygame.K_a:
                            self.loglines.extend(self.g.turn(-1,0))
                            repaint = True
                        if event.key == pygame.K_d:
                            self.loglines.extend(self.g.turn(1,0))
                            repaint = True
                        if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                            self.loglines.extend(self.g.turn(0,0))
                            repaint = True
                        if event.key == pygame.K_c: # close door
                            self.loglines.extend(self.g.close_door())
                            repaint = True
                        # ---------- on german keyboard, K_GREATER key is the same as SHIFT and K_LESS
                        if event.mod & pygame.KMOD_LSHIFT or event.mod & pygame.KMOD_RSHIFT:
                            if event.key == pygame.K_GREATER or event.key == pygame.K_LESS:
                            #if event.key == pygame.K_GREATER: # climb down
                                ##print("down key pressed")
                                self.loglines.extend(self.g.climb_down())
                                repaint = True
                        elif event.key == pygame.K_LESS: # climb up
                            self.loglines.extend(self.g.climb_up())
                            repaint = True

                        # ----------------------

            # ------------ pressed keys ------
            pressed_keys = pygame.key.get_pressed()

            # ------ mouse handler ------
            left, middle, right = pygame.mouse.get_pressed()
            if not oldleft and left and cursormode:
                selection = self.pixel_to_tile(pygame.mouse.get_pos())
                print("selected: ", selection)
                cursormode = False

            oldleft, oldmiddle, oldright = left, middle, right

            # -------------------------delete everything on screen--------------------------------------
            #pygame.display.set_caption(str(cursormode))
            #repaint = True
            if cursormode or len(self.flytextgroup) > 0 or len(self.fxgroup) >0:
                repaint = True
            if repaint:
                ## kill old sprites of effects:
                #for n in [sprite for sprite in self.effectgroup]:
                #    print("iterating over effects", n)

                self.screen.blit(self.background, (0, 0))
                self.paint_tiles()
                self.make_radar()
                self.make_panel()
                self.make_log()
                ##pygame.display.flip() # bad idea
                self.screen_backup = self.screen.copy()
                # testing...
                #for x, i in enumerate(Flash.pictures):
                #    self.screen.blit(i, (x * Viewer.gridsize[0], 20))
                #    #input("...")

            else:
                 self.cursorgroup.clear(self.screen, self.screen_backup)
            self.screen.blit(self.panelscreen, (Viewer.width - Viewer.panelwidth, Viewer.panelwidth))
            self.screen.blit(self.radarscreen, (Viewer.width - Viewer.panelwidth,0))
            self.screen.blit(self.logscreen, (0, Viewer.height - Viewer.logheight))
            # ---- clear old effect, paint new effects ----
            self.paint_animation(seconds)
            # ---- update panel with help for tile on cursor -----
            if not cursormode:
                self.panelinfo()



            # -------------- special effect after cusormode selection -------
            if selection is not None:
                # -------- shoot blue circles into each square until cursor-------
                points = get_line((hero.x, hero.y), selection)
                for point in points:
                    ok = calculate_line((hero.x, hero.y), point, hero.z, "shoot")
                    if ok:
                        for _ in range(10):
                            px, py = self.tile_to_pixel((point[0], point[1]))
                            p = pygame.math.Vector2(px,py)
                            Bubble(pos=p )
                # ----- fly arrow
                FlyingObject(start_tile = points[0], end_tile=points[-1])
                selection = None

            # ---- update -----------------
            self.allgroup.update(seconds)
            #self.effectgroup.update(seconds)
            #print("has:",self.allgroup.has(self.cursor))
            #if cursormode:
            self.cursorgroup.update(seconds)
                ##pygame.display.set_caption(pygame.mouse.get_pos(), self.cursor.tx, self.cursor.ty)

            # --------- collision detection between Player and Beam -----
            #for player  in self.playergroup:
            #    crashgroup = pygame.sprite.spritecollide(player, self.bulletgroup,
            #                 False, pygame.sprite.collide_circle) # need 'radius' attribute for both sprites
            #    for beam in crashgroup:
            #        if beam.boss == player:
            #            continue
            #        player.hitpoints -= beam.damage
            #        # explosion with bubbels
            #        if random.random() < 0.85:
            #            v = pygame.math.Vector2(beam.move.x, beam.move.y)
            #            v.normalize_ip()
            #            v *= random.randint(60,160) # speed
            #            v.rotate_ip(beam.angle + 180 + random.randint(-20,20))
            #            Bubble(pos=pygame.math.Vector2(beam.pos.x, beam.pos.y), color=beam.color,
            #                   move=v)
            #        beam.kill()
                    #beam.hitpoints = 0 # kill later
            # ----------- draw  -----------------
            self.allgroup.draw(self.screen)
            #if cursormode:
            #self.effectgroup.draw(self.screen)

            self.cursorgroup.draw(self.screen)
            # write text below sprites
            fps_text = "FPS: {:8.3}".format(self.clock.get_fps())
            write(self.screen, text=fps_text, origin="bottomright", x=Viewer.width - 5, y=Viewer.height - 5,
                  font_size=18, color=(200, 40, 40))
            # ----- hud ----
            #self.hud()
            # -------- next frame -------------
            pygame.display.flip()
            repaint = False
        # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()

## -------------------- functions --------------------------------

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
    print("calculating line in dungeon",z,"from",start,"to",end, "for", modus)
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


def make_text(text="@", fgcolor=(0,128,0), bgcolor=None, rotation=0, style=pygame.freetype.STYLE_DEFAULT, size=None, mono=False):
    """returns pygame surface (Viewer.gridsize[0] x Viewer.gridsize[1]) with text blitted on it.
       The text is centered on the surface. Font_size = Viewer.fontsize
       You still need to blit the surface.
       Use pygame.rect methods to get width and height of the new surface
    """
    if size is None:
        size = (Viewer.fontsize,Viewer.fontsize)
    if not isinstance(size, tuple) and not isinstance(size, list):
        size = (size,size)
    if mono:
        #myfont = Viewer.monofontfilename
        #oldfont = pg.font.Font(os.path.join(fontdir, "..", "data", "fonts", "FreeMonoBold.otf"), fontsize)
        myfont = pygame.font.Font(Viewer.monofontfilename, size[0])
        #pic = oldfont.render(chars[char_index], True, (255, 64, 64))
        #rect = pic.get_rect()
        text1 = myfont.render(text, True, fgcolor)
        rect1 = text1.get_rect()
    else:
        myfont = Viewer.font
        myfont.origin = False  # make sure to blit from topleft corner
        text1, rect1 = myfont.render(text, fgcolor, bgcolor, style, rotation, size)

    surf = pygame.Surface(Viewer.gridsize)
    surf.set_colorkey((0,0,0))
    surf.convert_alpha()



    midx = Viewer.gridsize[0] //2
    midy = Viewer.gridsize[1] //2
    midtx = rect1.width // 2
    midty = rect1.height // 2
    surf.blit(text1, ( midx - midtx, midy - midty  ))
    return surf


def fight(a, b):
    """dummy function, does nothing yet"""
    text = []
    text.append("Strike! {} attacks {}".format(type(a).__name__,
                                               type(b).__name__))
    damage = random.randint(1,6)
    b.hp -= damage
    impact_bubbles(a,b)
    return text

def impact_bubbles(a,b):
    """bubbles because monster a strikes v.s monster b"""
    victimcolor = b.fgcolor
    bx,by = Viewer.tile_to_pixel((b.x,b.y))
    #ax, ay = Viewer.tile_to_pixel((a.x,a.y))
    m = pygame.math.Vector2(b.x,b.y) - pygame.math.Vector2(a.x,a.y)
    m.normalize_ip()
    # impact point
    impactpoint = pygame.math.Vector2(bx,by) - m * Viewer.gridsize[0] //2
    for _ in range(25):
        po = pygame.math.Vector2(impactpoint.x, impactpoint.y)
        mo = pygame.math.Vector2(m.x, m.y)
        mo.rotate_ip(random.randint(-60,60))
        mo *= random.random()* 25 + 25
        Bubble(pos=po, color=b.fgcolor, move=-mo, max_age = 0.3 )


def between(value, min=0, max=255 ):
    """makes sure a (color) value stays between a minimum and a maximum ( 0 and 255 ) """
    return 0 if value < min else max if value > max else value

# generic pygame functions

def write(background, text, x=50, y=150, color=(0, 0, 0),
          font_size=None, origin="topleft" ,mono=True, rotation=0):
    """blit text on a given pygame surface (given as 'background')
       the origin is the alignment of the text surface
       origin can be 'center', 'centercenter', 'topleft', 'topcenter', 'topright', 'centerleft', 'centerright',
       'bottomleft', 'bottomcenter', 'bottomright'
    """
    if font_size is None:
        font_size = 24
    #font = Viewer.font # pygame.font.SysFont(font_name, font_size, bold)
    #font = pygame.font.Font(Viewer.fontfile, font_size)
    font = Viewer.font
    surface, rrect = font.render(text, color, rotation=rotation, size=font_size)
    width, height = rrect.width, rrect.height
    #surface = font.render(text, True, color)

    if origin == "center" or origin == "centercenter":
        background.blit(surface, (x - width // 2, y - height // 2))
    elif origin == "topleft":
        background.blit(surface, (x, y))
    elif origin == "topcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "topright":
        background.blit(surface, (x - width , y))
    elif origin == "centerleft":
        background.blit(surface, (x, y - height // 2))
    elif origin == "centerright":
        background.blit(surface, (x - width , y - height // 2))
    elif origin == "bottomleft":
        background.blit(surface, (x , y - height ))
    elif origin == "bottomcenter":
        background.blit(surface, (x - width // 2, y ))
    elif origin == "bottomright":
        background.blit(surface, (x - width, y - height))

## -------------- code at module level -----------------------------

# use those chars to create tiles, monsters, items etc in level maps. Values are class names, not Strings!:
legend= {
    "#":Wall,
    ".":Floor,
    ">":StairDown,
    "<":StairUp,
    "d":Door,
    "@":Player,
    "M":Monster,
    "D":Dragon,
    "W":Waterguy,
    "S":SkyDragon,
    "k":Key,
    "$":Coin,
    "f":Food,

}
level1 = """
######################################
#@#...#.k.d....#............$.....M..#
#>...#....#........#..###...#...#....#
##.#.#ff..####.#...####....###.......#
#.$$.M.......#.#....#...ff..#...$....#
######################################"""

# insert in level2: W for Waterguy, S for Skydragon

level2 = """
#################################################################
#..<............................................................#
#...............................................................#
#...............................................................#
#...............................................................#
#...............##d###..........................................#
#.....W.........#....#..........................................#
#...............#..S.d..........................................#
#...............#....##............D..................D.........#
#...............#.....#.........................................#
#.kk.k.k........d.....##........................................#
#...............###d####........................................#
#...............................................................#
#...............................................................#
#...............................................................#
#################################################################"""



if __name__ == '__main__':
    #g = Game()
    Viewer(width=1200, height=960, gridsize=(64,64),panelwidth=200, logheight=100,
           fontsize=64, wallfontsize=100, max_tiles_x=200, max_tiles_y=200)
