from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.graphics import Line, Ellipse, Rectangle, Color as KivyColor
import math
import random

# Game constants
FIELD_WIDTH = 800
FIELD_HEIGHT = 600
BALL_RADIUS = 10
PLAYER_SIZE = 25
NET_HEIGHT = 80
NET_WIDTH = 20

class Vector2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def normalize(self):
        mag = math.sqrt(self.x ** 2 + self.y ** 2)
        if mag > 0:
            self.x /= mag
            self.y /= mag
        return self
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

class Ball:
    def __init__(self):
        self.pos = Vector2(FIELD_WIDTH / 2, FIELD_HEIGHT / 2)
        self.vel = Vector2(0, 0)
        self.radius = BALL_RADIUS
        self.friction = 0.97
    
    def update(self):
        # Apply friction
        self.vel.x *= self.friction
        self.vel.y *= self.friction
        
        # Update position
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y
        
        # Bounce off top/bottom walls
        if self.pos.y - self.radius <= 0:
            self.pos.y = self.radius
            self.vel.y = -self.vel.y * 0.8
        elif self.pos.y + self.radius >= FIELD_HEIGHT:
            self.pos.y = FIELD_HEIGHT - self.radius
            self.vel.y = -self.vel.y * 0.8
        
        # Keep within left/right bounds
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > FIELD_WIDTH:
            self.pos.x = FIELD_WIDTH
    
    def kick(self, direction_x, direction_y, power):
        magnitude = math.sqrt(direction_x ** 2 + direction_y ** 2)
        if magnitude > 0:
            direction_x /= magnitude
            direction_y /= magnitude
        
        self.vel.x = direction_x * power
        self.vel.y = direction_y * power

class Player:
    def __init__(self, x, y, team, is_human=False, is_goalkeeper=False):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.team = team  # 0 = Team A (Player), 1 = Team B (Computer)
        self.is_human = is_human
        self.is_goalkeeper = is_goalkeeper
        self.radius = PLAYER_SIZE / 2
        self.speed = 2
        self.color = self._get_color()
    
    def _get_color(self):
        if self.is_human:
            return (1, 1, 0, 1)  # Yellow
        elif self.is_goalkeeper:
            return (1, 0, 0, 1)  # Red
        elif self.team == 0:
            return (0, 0, 1, 1)  # Blue
        else:
            return (0, 1, 1, 1)  # Cyan
    
    def move(self, dx, dy):
        self.pos.x += dx * self.speed
        self.pos.y += dy * self.speed
        
        # Keep within bounds
        self.pos.x = max(self.radius, min(self.pos.x, FIELD_WIDTH - self.radius))
        self.pos.y = max(self.radius, min(self.pos.y, FIELD_HEIGHT - self.radius))
    
    def distance_to(self, other):
        return self.pos.distance_to(other.pos)

class SoccerGame(Widget):
    score_team_a = NumericProperty(0)
    score_team_b = NumericProperty(0)
    game_status = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.canvas.clear()
        
        # Initialize game objects
        self.ball = Ball()
        self.players = []
        self.touch_pos = Vector2(FIELD_WIDTH / 2, FIELD_HEIGHT / 2)
        self.game_over = False
        self.winner = ""
        self.frame = 0
        
        # Create players
        self._init_players()
        
        # Schedule game updates
        Clock.schedule_interval(self.update_game, 1.0 / 60.0)
        Clock.schedule_interval(self.draw_game, 1.0 / 60.0)
    
    def _init_players(self):
        """Initialize all players"""
        # Team A (Player's team - left side, Blue)
        self.player = Player(100, FIELD_HEIGHT / 2, team=0, is_human=True)
        self.players.append(self.player)
        
        # Team A midfielders
        self.players.append(Player(250, 100, team=0))
        self.players.append(Player(250, FIELD_HEIGHT - 100, team=0))
        
        # Team A goalkeeper
        self.goalkeeper_a = Player(50, FIELD_HEIGHT / 2, team=0, is_goalkeeper=True)
        self.players.append(self.goalkeeper_a)
        
        # Team B (Computer - right side, Cyan)
        self.players.append(Player(FIELD_WIDTH - 100, FIELD_HEIGHT / 2, team=1))
        
        # Team B midfielders
        self.players.append(Player(FIELD_WIDTH - 250, 100, team=1))
        self.players.append(Player(FIELD_WIDTH - 250, FIELD_HEIGHT - 100, team=1))
        
        # Team B goalkeeper
        self.goalkeeper_b = Player(FIELD_WIDTH - 50, FIELD_HEIGHT / 2, team=1, is_goalkeeper=True)
        self.players.append(self.goalkeeper_b)
    
    def update_game(self, dt):
        """Update game logic"""
        if self.game_over:
            return
        
        self.frame += 1
        
        # Update ball
        self.ball.update()
        
        # Update AI players
        self._update_ai()
        
        # Check collisions
        self._check_collisions()
        
        # Check goals
        self._check_goals()
        
        # Update player position based on touch
        if self.player.distance_to(self.ball) < 50:
            # Auto-kick towards goal if near ball
            if self.frame % 10 == 0:
                direction = Vector2(FIELD_WIDTH - self.ball.pos.x, 
                                  FIELD_HEIGHT / 2 - self.ball.pos.y)
                self.ball.kick(direction.x, direction.y, 3)
    
    def _update_ai(self):
        """Update computer AI players"""
        for player in self.players:
            if player.is_human or player.is_goalkeeper:
                continue
            
            # Move towards ball
            dx = self.ball.pos.x - player.pos.x
            dy = self.ball.pos.y - player.pos.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > 0:
                dx /= distance
                dy /= distance
                player.move(dx * 0.5, dy * 0.5)
            
            # Kick if close to ball
            if distance < 40:
                if player.team == 1:
                    target_x = 0
                else:
                    target_x = FIELD_WIDTH
                
                kick_dir = Vector2(target_x - self.ball.pos.x,
                                 FIELD_HEIGHT / 2 - self.ball.pos.y)
                self.ball.kick(kick_dir.x, kick_dir.y, 3)
        
        # Update goalkeepers
        self._update_goalkeeper(self.goalkeeper_a)
        self._update_goalkeeper(self.goalkeeper_b)
    
    def _update_goalkeeper(self, goalkeeper):
        """Update goalkeeper AI"""
        target_y = self.ball.pos.y
        min_y = max(goalkeeper.radius, FIELD_HEIGHT / 2 - NET_HEIGHT / 2)
        max_y = min(FIELD_HEIGHT - goalkeeper.radius, FIELD_HEIGHT / 2 + NET_HEIGHT / 2)
        
        if goalkeeper.pos.y < target_y - 5:
            goalkeeper.move(0, 1)
        elif goalkeeper.pos.y > target_y + 5:
            goalkeeper.move(0, -1)
        
        goalkeeper.pos.y = max(min_y, min(goalkeeper.pos.y, max_y))
    
    def _check_collisions(self):
        """Check ball-player collisions"""
        for player in self.players:
            distance = player.distance_to(self.ball)
            min_distance = player.radius + self.ball.radius
            
            if distance < min_distance:
                if distance > 0:
                    dx = self.ball.pos.x - player.pos.x
                    dy = self.ball.pos.y - player.pos.y
                    magnitude = math.sqrt(dx ** 2 + dy ** 2)
                    
                    dx /= magnitude
                    dy /= magnitude
                    
                    bounce_power = 4
                    self.ball.vel.x = dx * bounce_power
                    self.ball.vel.y = dy * bounce_power
    
    def _check_goals(self):
        """Check if goal is scored"""
        goal_min_y = FIELD_HEIGHT / 2 - NET_HEIGHT / 2
        goal_max_y = FIELD_HEIGHT / 2 + NET_HEIGHT / 2
        
        # Goal for Team A (right goal)
        if self.ball.pos.x > FIELD_WIDTH - 20 and goal_min_y <= self.ball.pos.y <= goal_max_y:
            self.score_team_a += 1
            self._reset_ball()
            if self.score_team_a >= 5:
                self.game_over = True
                self.winner = "TEAM A (YOU) WINS!"
        
        # Goal for Team B (left goal)
        if self.ball.pos.x < 20 and goal_min_y <= self.ball.pos.y <= goal_max_y:
            self.score_team_b += 1
            self._reset_ball()
            if self.score_team_b >= 5:
                self.game_over = True
                self.winner = "TEAM B (COMPUTER) WINS!"
        
        # Reset if ball goes out of bounds
        if self.ball.pos.x < 0 or self.ball.pos.x > FIELD_WIDTH:
            self._reset_ball()
    
    def _reset_ball(self):
        """Reset ball to center"""
        self.ball.pos = Vector2(FIELD_WIDTH / 2, FIELD_HEIGHT / 2)
        self.ball.vel = Vector2(0, 0)
    
    def draw_game(self, dt):
        """Draw the game"""
        self.canvas.clear()
        
        with self.canvas:
            # Field background
            KivyColor(0.1, 0.4, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Scale for different screen sizes
            scale_x = self.width / FIELD_WIDTH
            scale_y = self.height / FIELD_HEIGHT
            
            # Field lines
            KivyColor(1, 1, 1, 0.3)
            # Center line
            Line(points=[self.x + self.width / 2, self.y,
                        self.x + self.width / 2, self.y + self.height], width=2)
            
            # Center circle
            center_x = self.x + self.width / 2
            center_y = self.y + self.height / 2
            Line(circle=(center_x, center_y, 40 * scale_x), width=2)
            
            # Goals (nets)
            KivyColor(1, 0, 0, 0.5)
            goal_height = NET_HEIGHT * scale_y
            # Left goal
            Line(points=[self.x, self.y + self.height / 2 - goal_height / 2,
                        self.x, self.y + self.height / 2 + goal_height / 2], width=3)
            # Right goal
            Line(points=[self.x + self.width, self.y + self.height / 2 - goal_height / 2,
                        self.x + self.width, self.y + self.height / 2 + goal_height / 2], width=3)
            
            # Draw ball
            KivyColor(1, 1, 0, 1)
            ball_x = self.x + self.ball.pos.x * scale_x
            ball_y = self.y + self.ball.pos.y * scale_y
            Ellipse(pos=(ball_x - 8, ball_y - 8), size=(16, 16))
            
            # Draw players
            for player in self.players:
                KivyColor(*player.color)
                player_x = self.x + player.pos.x * scale_x
                player_y = self.y + player.pos.y * scale_y
                size = PLAYER_SIZE * scale_x
                Ellipse(pos=(player_x - size / 2, player_y - size / 2), size=(size, size))
                
                # Highlight human player
                if player.is_human:
                    KivyColor(1, 1, 0, 0.3)
                    Line(circle=(player_x, player_y, size / 2 + 5), width=2)
    
    def on_touch_move(self, touch):
        """Handle touch move"""
        # Map touch to player movement
        touch_x = touch.x
        
        # Move player towards touch x position
        target_y = touch.y / self.height * FIELD_HEIGHT;
        
        # Move player smoothly towards touch
        diff_y = target_y - self.player.pos.y
        if abs(diff_y) > 5:
            self.player.move(0, 1 if diff_y > 0 else -1)
        
        return True
    
    def on_touch_down(self, touch):
        """Handle touch down - kick ball"""
        # Move player towards touch position
        return self.on_touch_move(touch)

class SoccerGameApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Score display
        self.score_label = Label(text='Team A: 0 - 0 :Team B', size_hint_y=0.1)
        layout.add_widget(self.score_label)
        
        # Game widget
        self.game = SoccerGame()
        layout.add_widget(self.game)
        
        # Update score label
        Clock.schedule_interval(self._update_score, 0.1)
        
        return layout
    
    def _update_score(self, dt):
        self.score_label.text = f'Team A (You): {int(self.game.score_team_a)} - {int(self.game.score_team_b)} :Team B (Computer)'
        if self.game.game_over:
            self.score_label.text += f' | {self.game.winner}'

if __name__ == '__main__':
    SoccerGameApp().run()