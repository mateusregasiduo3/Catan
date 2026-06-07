import sys
import types
from pathlib import Path

# Add project root to Python path so tests can import components, models, etc.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Minimal fake pygame module for test environment (avoid requiring pygame install)
pygame = types.ModuleType('pygame')
pygame.init = lambda *a, **k: None
pygame.quit = lambda *a, **k: None
pygame.SYSTEM_CURSOR_ARROW = 0
pygame.SYSTEM_CURSOR_HAND = 1
pygame.SRCALPHA = 1
pygame.BLEND_RGBA_MULT = 2
pygame.MOUSEMOTION = 1
pygame.MOUSEBUTTONDOWN = 2
pygame.MOUSEBUTTONUP = 3
pygame.KEYDOWN = 4
pygame.QUIT = 5
pygame.K_d = 100
pygame.K_ESCAPE = 101
pygame.FULLSCREEN = 1

class DummyFont:
    def __init__(self, *a, **k):
        pass

    def render(self, *a, **k):
        return DummySurface((max(8, len(str(a[0])) * 8) if a else 24, 18))


pygame.font = types.SimpleNamespace(Font=lambda *a, **k: DummyFont(), SysFont=lambda *a, **k: DummyFont())

class DummyRect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self._left = x
        self._top = y
        self.width = w
        self.height = h

    def _sync(self):
        return None

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value):
        self._left = value

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, value):
        self._top = value

    @property
    def right(self):
        return self._left + self.width

    @right.setter
    def right(self, value):
        self._left = value - self.width

    @property
    def bottom(self):
        return self._top + self.height

    @bottom.setter
    def bottom(self, value):
        self._top = value - self.height

    @property
    def centerx(self):
        return self._left + self.width // 2

    @centerx.setter
    def centerx(self, value):
        self._left = value - self.width // 2

    @property
    def centery(self):
        return self._top + self.height // 2

    @centery.setter
    def centery(self, value):
        self._top = value - self.height // 2

    @property
    def x(self):
        return self._left

    @x.setter
    def x(self, value):
        self._left = value

    @property
    def y(self):
        return self._top

    @y.setter
    def y(self, value):
        self._top = value

    @property
    def w(self):
        return self.width

    @w.setter
    def w(self, value):
        self.width = value

    @property
    def h(self):
        return self.height

    @h.setter
    def h(self, value):
        self.height = value

    def collidepoint(self, *pos):
        if len(pos) == 1:
            pos = pos[0]
        try:
            px, py = pos
        except Exception:
            return False
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def get_rect(self, *args, **kwargs):
        rect = DummyRect(self.left, self.top, self.width, self.height)
        if args:
            arg = args[0]
            if isinstance(arg, dict):
                kwargs.update(arg)
        for key, value in kwargs.items():
            if key == "center":
                rect.centerx, rect.centery = value
                rect.left = rect.centerx - rect.width // 2
                rect.top = rect.centery - rect.height // 2
            elif key == "centerx":
                rect.centerx = value
                rect.left = rect.centerx - rect.width // 2
            elif key == "centery":
                rect.centery = value
                rect.top = rect.centery - rect.height // 2
            elif key == "top":
                rect.top = value
            elif key == "bottom":
                rect.bottom = value
                rect.top = rect.bottom - rect.height
            elif key == "left":
                rect.left = value
            elif key == "right":
                rect.right = value
                rect.left = rect.right - rect.width
        return rect

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def center(self):
        return (self.centerx, self.centery)

    @center.setter
    def center(self, value):
        self.centerx, self.centery = value
        self.left = self.centerx - self.width // 2
        self.top = self.centery - self.height // 2
        self._sync()

    @property
    def topleft(self):
        return (self.left, self.top)

    @topleft.setter
    def topleft(self, value):
        self.left, self.top = value
        self._sync()

    def copy(self):
        return DummyRect(self.left, self.top, self.width, self.height)

    def inflate(self, x, y):
        return DummyRect(self.left - x // 2, self.top - y // 2, self.width + x, self.height + y)

    def __iter__(self):
        return iter((self.left, self.top, self.width, self.height))

class DummySound:
    def __init__(self, *a, **k):
        self.volume = 1.0
        self.played = False
        self.stopped = False

    def play(self, *a, **k):
        self.played = True

    def stop(self, *a, **k):
        self.stopped = True

    def set_volume(self, volume):
        self.volume = volume

class DummyMusic:
    def __init__(self):
        self.loaded = None
        self.volume = 1.0
        self.play_args = None
        self.stopped = False

    def load(self, filepath):
        self.loaded = filepath

    def set_volume(self, volume):
        self.volume = volume

    def play(self, *a, **k):
        self.play_args = (a, k)

    def stop(self):
        self.stopped = True

class DrawCalls:
    def __init__(self):
        self.calls = []

    def rect(self, *a, **k):
        self.calls.append(("rect", a, k))

    def circle(self, *a, **k):
        self.calls.append(("circle", a, k))

    def polygon(self, *a, **k):
        self.calls.append(("polygon", a, k))

    def line(self, *a, **k):
        self.calls.append(("line", a, k))

    def ellipse(self, *a, **k):
        self.calls.append(("ellipse", a, k))

pygame.draw = DrawCalls()

pygame.mixer = types.SimpleNamespace(
    init=lambda *a, **k: None,
    Sound=lambda *a, **k: DummySound(),
    stop=lambda *a, **k: None,
    music=DummyMusic(),
)

class DummySurface:
    def __init__(self, size=(0, 0), flags=None):
        self._size = size

    def convert_alpha(self):
        return self

    def get_size(self):
        return self._size

    def copy(self):
        return DummySurface(self._size)

    def fill(self, *a, **k):
        return None

    def blit(self, *a, **k):
        return None

    def get_rect(self, *args, **kwargs):
        return DummyRect(0, 0, self._size[0], self._size[1]).get_rect(*args, **kwargs)

    def get_width(self):
        return self._size[0]

    def get_height(self):
        return self._size[1]

pygame.Surface = lambda size, flags=None: DummySurface(size)
pygame.Rect = DummyRect
pygame.mouse = types.SimpleNamespace(get_pos=lambda: (0, 0), set_cursor=lambda *a, **k: None)
class Event:
    def __init__(self, type=None, **kwargs):
        self.type = type
        for key, value in kwargs.items():
            setattr(self, key, value)

pygame.event = types.SimpleNamespace(Event=Event, post=lambda *a, **k: None, get=lambda: [])
pygame.image = types.SimpleNamespace(load=lambda path: DummySurface((64, 64)))
pygame.error = Exception
pygame.transform = types.SimpleNamespace(smoothscale=lambda surf, size: DummySurface(size), rotate=lambda base, ang: base)
pygame.display = types.SimpleNamespace(
    Info=lambda: types.SimpleNamespace(current_w=800, current_h=600),
    set_mode=lambda *a, **k: DummySurface((800, 600)),
    set_caption=lambda *a, **k: None,
    flip=lambda *a, **k: None,
)
pygame.time = types.SimpleNamespace(Clock=lambda: types.SimpleNamespace(tick=lambda fps: 16))

sys.modules['pygame'] = pygame
