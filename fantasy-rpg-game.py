import pygame
import random
import sys
import math
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 64
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fantasy 8-bit RPG")
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont("monospace", 24)
small_font = pygame.font.SysFont("monospace", 18)

# Load assets function
def load_image(name, scale=1):
    """Load an image and return the scaled surface."""
    try:
        image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        image.fill(get_color_for_entity(name))
        return image
    except pygame.error as e:
        print(f"Could not load image: {e}")
        return pygame.Surface((TILE_SIZE, TILE_SIZE))

def get_color_for_entity(name):
    """Return a color based on entity type for placeholder graphics."""
    colors = {
        "player": (0, 0, 255),  # Blue
        "knight": (0, 100, 200),  # Light blue
        "dwarf": (150, 75, 0),  # Brown
        "dragon": (255, 0, 0),  # Red
        "sword": (192, 192, 192),  # Silver
        "potion": (255, 0, 255),  # Purple
        "grass": (0, 128, 0),  # Green
        "wall": (128, 128, 128),  # Gray
        "chest": (255, 215, 0),  # Gold
    }
    return colors.get(name, (0, 0, 0))  # Default to black

# Play sound function
def play_sound(sound_name):
    """Play a sound effect."""
    # Dictionary mapping sound names to note frequencies
    sound_frequencies = {
        "attack": 440,  # A4
        "hit": 880,  # A5
        "pickup": 660,  # E5
        "gameover": 220,  # A3
        "levelup": 587.33,  # D5
        "victory": 523.25,  # C5
    }
    
    if sound_name in sound_frequencies:
        freq = sound_frequencies[sound_name]
        duration = 200  # milliseconds
        
        # Generate a simple beep sound
        pygame.mixer.Sound(pygame.sndarray.make_sound(
            pygame.sndarray.array(
                [4096 * math.sin(2.0 * math.pi * freq * t / 22050) 
                 for t in range(int(22050 * duration / 1000))],
                dtype=pygame.int16
            )
        )).play()

# Entity classes
class Entity:
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.entity_type = entity_type
        self.image = load_image(entity_type)
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    
    def draw(self, surface, offset_x=0, offset_y=0):
        surface.blit(self.image, (self.x * TILE_SIZE - offset_x, self.y * TILE_SIZE - offset_y))
    
    def update(self):
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE

class Character(Entity):
    def __init__(self, x, y, entity_type, health, attack, defense):
        super().__init__(x, y, entity_type)
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.experience = 0
        self.level = 1
        self.inventory = []
    
    def move(self, dx, dy, obstacles):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check for collision with obstacles
        for obstacle in obstacles:
            if obstacle.x == new_x and obstacle.y == new_y:
                return False
        
        self.x = new_x
        self.y = new_y
        self.update()
        return True
    
    def attack_entity(self, target):
        damage = max(1, self.attack - target.defense)
        target.health -= damage
        play_sound("hit")
        return damage
    
    def is_alive(self):
        return self.health > 0
    
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
    
    def gain_experience(self, amount):
        self.experience += amount
        exp_needed = 100 * self.level
        if self.experience >= exp_needed:
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        self.experience = 0
        play_sound("levelup")

class Player(Character):
    def __init__(self, x, y):
        super().__init__(x, y, "player", 100, 10, 5)
        self.gold = 0
    
    def pickup_item(self, item):
        if item.entity_type == "potion":
            self.heal(20)
            play_sound("pickup")
            return True
        elif item.entity_type == "sword":
            self.attack += 5
            play_sound("pickup")
            return True
        elif item.entity_type == "chest":
            self.gold += random.randint(10, 30)
            play_sound("pickup")
            return True
        return False

class Enemy(Character):
    def __init__(self, x, y, enemy_type):
        if enemy_type == "knight":
            super().__init__(x, y, enemy_type, 30, 8, 3)
            self.exp_value = 20
            self.gold_value = random.randint(5, 15)
        elif enemy_type == "dwarf":
            super().__init__(x, y, enemy_type, 40, 6, 5)
            self.exp_value = 25
            self.gold_value = random.randint(10, 20)
        elif enemy_type == "dragon":
            super().__init__(x, y, enemy_type, 100, 15, 10)
            self.exp_value = 100
            self.gold_value = random.randint(50, 100)
    
    def move_towards(self, target, obstacles):
        dx = 0
        dy = 0
        
        if self.x < target.x:
            dx = 1
        elif self.x > target.x:
            dx = -1
        elif self.y < target.y:
            dy = 1
        elif self.y > target.y:
            dy = -1
        
        if dx != 0 or dy != 0:
            self.move(dx, dy, obstacles)

class Item(Entity):
    def __init__(self, x, y, item_type):
        super().__init__(x, y, item_type)

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[0 for _ in range(width)] for _ in range(height)]
        self.entities = []
        self.player = None
        self.enemies = []
        self.items = []
        self.obstacles = []
    
    def generate_map(self):
        # Simple map generation
        for y in range(self.height):
            for x in range(self.width):
                # Create walls at the borders
                if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    self.tiles[y][x] = 1
                    wall = Entity(x, y, "wall")
                    self.entities.append(wall)
                    self.obstacles.append(wall)
                else:
                    self.tiles[y][x] = 0
                    # 5% chance to spawn a wall
                    if random.random() < 0.05:
                        self.tiles[y][x] = 1
                        wall = Entity(x, y, "wall")
                        self.entities.append(wall)
                        self.obstacles.append(wall)
    
    def add_player(self, x, y):
        self.player = Player(x, y)
        self.entities.append(self.player)
    
    def add_enemy(self, x, y, enemy_type):
        enemy = Enemy(x, y, enemy_type)
        self.enemies.append(enemy)
        self.entities.append(enemy)
    
    def add_item(self, x, y, item_type):
        item = Item(x, y, item_type)
        self.items.append(item)
        self.entities.append(item)
    
    def is_position_valid(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        if self.tiles[y][x] == 1:
            return False
        return True
    
    def get_random_valid_position(self):
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if self.is_position_valid(x, y):
                is_occupied = False
                for entity in self.entities:
                    if entity.x == x and entity.y == y:
                        is_occupied = True
                        break
                if not is_occupied:
                    return x, y
    
    def populate(self, num_knights, num_dwarfs, num_dragons, num_swords, num_potions, num_chests):
        # Add enemies
        for _ in range(num_knights):
            x, y = self.get_random_valid_position()
            self.add_enemy(x, y, "knight")
        
        for _ in range(num_dwarfs):
            x, y = self.get_random_valid_position()
            self.add_enemy(x, y, "dwarf")
        
        for _ in range(num_dragons):
            x, y = self.get_random_valid_position()
            self.add_enemy(x, y, "dragon")
        
        # Add items
        for _ in range(num_swords):
            x, y = self.get_random_valid_position()
            self.add_item(x, y, "sword")
        
        for _ in range(num_potions):
            x, y = self.get_random_valid_position()
            self.add_item(x, y, "potion")
        
        for _ in range(num_chests):
            x, y = self.get_random_valid_position()
            self.add_item(x, y, "chest")
    
    def draw(self, surface, camera_x, camera_y):
        for y in range(self.height):
            for x in range(self.width):
                # Draw background
                color = GREEN if self.tiles[y][x] == 0 else BLUE
                pygame.draw.rect(surface, color, (x * TILE_SIZE - camera_x, y * TILE_SIZE - camera_y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surface, BLACK, (x * TILE_SIZE - camera_x, y * TILE_SIZE - camera_y, TILE_SIZE, TILE_SIZE), 1)
        
        # Draw entities
        for entity in self.entities:
            entity.draw(surface, camera_x, camera_y)
    
    def update(self):
        # Update all entities
        for entity in self.entities:
            if hasattr(entity, 'update'):
                entity.update()
        
        # Check for player-item collisions
        items_to_remove = []
        for item in self.items:
            if self.player.x == item.x and self.player.y == item.y:
                if self.player.pickup_item(item):
                    items_to_remove.append(item)
        
        # Remove collected items
        for item in items_to_remove:
            self.items.remove(item)
            self.entities.remove(item)
        
        # Move enemies
        for enemy in self.enemies:
            if enemy.is_alive():
                # If enemy is close to player, move towards player
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if distance <= 5:
                    enemy.move_towards(self.player, self.obstacles + [self.player])
        
        # Check for player-enemy collisions (combat)
        combat_results = []
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            
            # If player is adjacent to enemy, attack
            if (abs(self.player.x - enemy.x) <= 1 and self.player.y == enemy.y) or \
               (abs(self.player.y - enemy.y) <= 1 and self.player.x == enemy.x):
                # Player attacks enemy
                damage_dealt = self.player.attack_entity(enemy)
                combat_results.append(f"You hit {enemy.entity_type} for {damage_dealt} damage!")
                
                # If enemy dies
                if not enemy.is_alive():
                    combat_results.append(f"You defeated the {enemy.entity_type}!")
                    self.player.gain_experience(enemy.exp_value)
                    self.player.gold += enemy.gold_value
                    combat_results.append(f"Gained {enemy.exp_value} exp and {enemy.gold_value} gold!")
                else:
                    # Enemy attacks player
                    damage_taken = enemy.attack_entity(self.player)
                    combat_results.append(f"{enemy.entity_type.capitalize()} hit you for {damage_taken} damage!")
        
        # Remove dead enemies
        enemies_to_remove = [enemy for enemy in self.enemies if not enemy.is_alive()]
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)
            self.entities.remove(enemy)
        
        return combat_results

# Game class
class Game:
    def __init__(self):
        self.running = True
        self.game_over = False
        self.victory = False
        self.map_width = 20
        self.map_height = 15
        self.game_map = Map(self.map_width, self.map_height)
        self.camera_x = 0
        self.camera_y = 0
        self.message_log = []
        self.current_level = 1
        self.max_messages = 5
        
        # Background music (simulated with notes)
        self.play_theme_music()

    def play_theme_music(self):
        # Instead of actual music, we'll just play a few notes for demonstration
        notes = [
            (392, 200),  # G4, 200ms
            (440, 200),  # A4, 200ms
            (493.88, 200),  # B4, 200ms
            (523.25, 400),  # C5, 400ms
        ]
        
        # We'll just play the first note to indicate music would be here
        pygame.mixer.Sound(pygame.sndarray.make_sound(
            pygame.sndarray.array(
                [4096 * math.sin(2.0 * math.pi * notes[0][0] * t / 22050) 
                 for t in range(int(22050 * notes[0][1] / 1000))],
                dtype=pygame.int16
            )
        )).play()
    
    def initialize_level(self):
        self.game_map = Map(self.map_width, self.map_height)
        self.game_map.generate_map()
        
        # Add player in a valid position
        player_x, player_y = self.game_map.get_random_valid_position()
        self.game_map.add_player(player_x, player_y)
        
        # Add enemies and items based on level
        knights = self.current_level * 2
        dwarfs = self.current_level
        dragons = self.current_level // 3
        
        swords = max(1, self.current_level // 2)
        potions = self.current_level * 2
        chests = self.current_level
        
        self.game_map.populate(knights, dwarfs, dragons, swords, potions, chests)
        
        self.message_log.append(f"Level {self.current_level} - Defeat all enemies!")
        
        # Center camera on player initially
        self.update_camera()
    
    def update_camera(self):
        # Center camera on player
        self.camera_x = self.game_map.player.x * TILE_SIZE - (SCREEN_WIDTH // 2)
        self.camera_y = self.game_map.player.y * TILE_SIZE - (SCREEN_HEIGHT // 2)
        
        # Clamp camera to map bounds
        self.camera_x = max(0, min(self.camera_x, self.map_width * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.map_height * TILE_SIZE - SCREEN_HEIGHT))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle keyboard input when game is active
            if not self.game_over and not self.victory:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.move_player(0, 1)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.move_player(1, 0)
                    elif event.key == pygame.K_SPACE:
                        self.player_attack()
            else:
                # Restart game if game over or victory
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()
    
    def move_player(self, dx, dy):
        if self.game_map.player.move(dx, dy, self.game_map.obstacles + self.game_map.enemies):
            combat_results = self.game_map.update()
            self.message_log.extend(combat_results)
            
            # Limit message log length
            if len(self.message_log) > self.max_messages:
                self.message_log = self.message_log[-self.max_messages:]
            
            self.update_camera()
            
            # Check if player is dead
            if not self.game_map.player.is_alive():
                self.game_over = True
                play_sound("gameover")
                self.message_log.append("Game Over! Press R to restart.")
            
            # Check if level is completed (all enemies defeated)
            if len(self.game_map.enemies) == 0:
                # If it's the final level, player wins
                if self.current_level >= 3:
                    self.victory = True
                    play_sound("victory")
                    self.message_log.append("Victory! You've completed the game!")
                    self.message_log.append("Press R to play again.")
                else:
                    self.current_level += 1
                    self.message_log.append(f"Level Complete! Advancing to level {self.current_level}...")
                    self.initialize_level()
                    play_sound("levelup")
    
    def player_attack(self):
        # Attack all adjacent enemies
        combat_results = []
        for enemy in self.game_map.enemies:
            if (abs(self.game_map.player.x - enemy.x) <= 1 and self.game_map.player.y == enemy.y) or \
               (abs(self.game_map.player.y - enemy.y) <= 1 and self.game_map.player.x == enemy.x):
                play_sound("attack")
                damage = self.game_map.player.attack_entity(enemy)
                combat_results.append(f"You attack {enemy.entity_type} for {damage} damage!")
                
                if not enemy.is_alive():
                    combat_results.append(f"You defeated the {enemy.entity_type}!")
                    self.game_map.player.gain_experience(enemy.exp_value)
                    self.game_map.player.gold += enemy.gold_value
                    combat_results.append(f"Gained {enemy.exp_value} exp and {enemy.gold_value} gold!")
        
        # Remove dead enemies
        enemies_to_remove = [enemy for enemy in self.game_map.enemies if not enemy.is_alive()]
        for enemy in enemies_to_remove:
            self.game_map.enemies.remove(enemy)
            self.game_map.entities.remove(enemy)
        
        self.message_log.extend(combat_results)
        # Limit message log length
        if len(self.message_log) > self.max_messages:
            self.message_log = self.message_log[-self.max_messages:]
        
        # Check if level is completed (all enemies defeated)
        if len(self.game_map.enemies) == 0:
            # If it's the final level, player wins
            if self.current_level >= 3:
                self.victory = True
                play_sound("victory")
                self.message_log.append("Victory! You've completed the game!")
                self.message_log.append("Press R to play again.")
            else:
                self.current_level += 1
                self.message_log.append(f"Level Complete! Advancing to level {self.current_level}...")
                self.initialize_level()
                play_sound("levelup")
    
    def reset_game(self):
        self.game_over = False
        self.victory = False
        self.current_level = 1
        self.message_log = []
        self.initialize_level()
    
    def draw_ui(self):
        # Draw player stats
        player = self.game_map.player
        
        # Background for status bar
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
        
        # Health bar
        health_text = font.render(f"HP: {player.health}/{player.max_health}", True, WHITE)
        screen.blit(health_text, (10, 10))
        
        # Level and XP
        level_text = font.render(f"Level: {player.level}", True, WHITE)
        screen.blit(level_text, (200, 10))
        
        # Gold
        gold_text = font.render(f"Gold: {player.gold}", True, YELLOW)
        screen.blit(gold_text, (350, 10))
        
        # Attack and Defense
        stats_text = font.render(f"ATK: {player.attack} DEF: {player.defense}", True, WHITE)
        screen.blit(stats_text, (500, 10))
        
        # Draw message log
        log_y = SCREEN_HEIGHT - (len(self.message_log) * 25) - 10
        pygame.draw.rect(screen, (0, 0, 0, 180), (0, log_y - 10, SCREEN_WIDTH, (len(self.message_log) * 25) + 20))
        
        for i, message in enumerate(self.message_log):
            msg_text = small_font.render(message, True, WHITE)
            screen.blit(msg_text, (10, log_y + i * 25))
        
        # Draw game over or victory message
        if self.game_over:
            self.draw_centered_message("GAME OVER! Press R to restart.", RED)
        elif self.victory:
            self.draw_centered_message("VICTORY! Press R to play again.", GREEN)
    
    def draw_centered_message(self, message, color):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
    
    def run(self):
        self.initialize_level()
        
        while self.running:
            self.handle_events()
            
            # Clear screen
            screen.fill(BLACK)
            
            # Draw map and entities
            self.game_map.draw(screen, self.camera_x, self.camera_y)
            
            # Draw UI
            self.draw_ui()
            
            # Update display
            pygame.display.flip()
            
            # Cap framerate
            clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Main game loop
if __name__ == "__main__":
    game = Game()
    game.run()
