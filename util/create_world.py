from django.contrib.auth.models import User
from adventure.models import Player
import random
size = ["Tiny", "Small", "Skinny", "Long", "Big", "Huge", "Volumous"]
adj = ["Fiery", "Cold", "Scary", "Burning", "Broken", "Boring", "Fastidious"]
movies = ["Airplane!", "Rugrats", "Lord of the Rings", "Jeepers Creepers"]
room_type = [
    ["Hallway", "It's a hallways - pretty self-explanatory, really."],
    ["Dining Room", "A large table, filled with plates of food. Who was eating here? You want to take a bite..."],
    ["Torture Chamber", "Lots of spooky contraptions and hot pokers. Get the heck out of here!"],
    ["Garden", "The trees and flowers look very pretty - unfortunately they are also trying to eat you."],
    ["Bathroom", "This place is pretty spooky, but hey, you've really got to go..."],
    ["Storage Closet", "A broom, dustpan, and you, are in this room. Why are you in this room?"],
    ["Kitten Room", "A room randomly filled with hundred of loveable kittens! You play with them for a bit before heading out."],
    ["Veranda", "You can see for miles and miles and miles and..."],
    ["Art Room", "Paintings on every wall! They would be beautiful if they weren't all so gruesome. Eep!"],
    ["Top Secret Labs Team Headquarters", "Shhhh, it's a secret! You shrug and move on."],
    ["Abyss", "You fall into an endless abyss! ...luckily you were just dreaming. Better move on."],
    ["Dirtmouth", "A desolate town of bugs, with a creepy well. You don't like platformers though, so time to leave."],
    ["Theatre", f"Movies and popcorn! You kick back and watch {movies[random.randint(0, 3)]} before continuing on your journey"],
    ["Cave", "You enter a cave. It's cold and damp. You don't like that."]
]

class Room:
    def __init__(self, id, name, description, x, y):
        self.id = id
        self.name = name
        self.description = description
        self.n_to = None
        self.s_to = None
        self.e_to = None
        self.w_to = None
        self.x = x
        self.y = y
    def __repr__(self):
        if self.e_to is not None:
            return f"({self.x}, {self.y}) -> ({self.e_to.x}, {self.e_to.y})"
        return f"({self.x}, {self.y})"
    def connect_rooms(self, connecting_room, direction):
        '''
        Connect two rooms in the given n/s/e/w direction
        '''
        reverse_dirs = {"n": "s", "s": "n", "e": "w", "w": "e"}
        reverse_dir = reverse_dirs[direction]
        setattr(self, f"{direction}_to", connecting_room)
        setattr(connecting_room, f"{reverse_dir}_to", self)
    def get_room_in_direction(self, direction):
        '''
        Connect two rooms in the given n/s/e/w direction
        '''
        return getattr(self, f"{direction}_to")

Room.objects.all().delete()
class World:
    def __init__(self):
        self.grid = None
        self.width = 0
        self.height = 0
        self.rooms_created = 0
    def generate_rooms(self, size_x, size_y, num_rooms):
        # Initialize the grid
        self.grid = [None] * size_y
        self.width = size_x
        self.height = size_y
        for i in range( len(self.grid) ):
            self.grid[i] = [None] * size_x
        # Start making rooms at the centerpoint of the map
        x = round((size_x-1)/2)
        y = round((size_y-1)/2)
        new_rooms_to_process = []
        rooms_with_space_nearby = []
        direction_options = ["n","e","s","w"]
        # Create the very first room right in the center as the "seed"
        self.grid[y][x] = Room(1, "Starting Room", "This is a generic room.", x, y)
        self.rooms_created = 1
        new_rooms_to_process.append(self.grid[y][x])
        # While there are rooms to be created...
        while self.rooms_created < num_rooms:
            # If there are new rooms that haven't yet had random branches calculated, get the first from queue
            if len(new_rooms_to_process) > 0:
                # Grab the first room from the list
                current_room = new_rooms_to_process.pop()
                # Randomly choose a number of directions to branch in
                num_dir = random.randint(0,4)
                # Randomly choose the appropriate number of directions
                dirs = random.sample(direction_options, num_dir)
                # If it's not going to branch in all directions, then add to the list of rooms that have space nearby
                if len(dirs) < 4:
                    rooms_with_space_nearby.append(current_room)
            # If there aren't any new rooms left, start searching among the previously created rooms
            # and branch off in all directions still available
            else:
                current_room = None
                while current_room is None and len(rooms_with_space_nearby) > 0:
                    # Grab the first room from the list
                    room = rooms_with_space_nearby.pop()
                    # Init the directions to branch in
                    dirs = []
                    # Add directions if no existing room in that direction and it's not out of bounds
                    if room.x+1 < self.width and self.grid[room.y][room.x+1] is None:
                        dirs.append("e")
                    if room.x-1 >= 0 and self.grid[room.y][room.x-1] is None:
                        dirs.append("w")
                    if room.y-1 >= 0 and self.grid[room.y][room.y-1] is None:
                        dirs.append("n")
                    if room.y+1 < self.height and self.grid[room.y][room.y+1] is None:
                        dirs.append("w")
                    # If there are valid directions to go in, we can pick this room and proceed with branching
                    if len(dirs) > 0:
                        current_room = room
            # For each provided direction try to make a room there
            for direction in dirs:
                new_room = self.add_room(current_room, direction)
                if new_room is not None:
                    # If a new room was created, add it to the queue for branching
                    new_rooms_to_process.append(new_room)
    # Try to add a new room
    #   prev_room: a Room that the new room is adjacent to
    #   direction: the direction from the prev_room that the new room should be created
    def add_room(self, prev_room, direction):
        x = prev_room.x
        y = prev_room.y
        # Determine coords of potential new room
        if direction == "e" and x + 1 < self.width:
            x += 1
        elif direction == "w" and x - 1 >= 0:
            x -= 1
        elif direction == "s" and y - 1 >= 0:
            y -= 1
        elif direction == "n" and y + 1 < self.height:
            y += 1
        else:
            # abort if new room would be outside of map bounds
            return None
        # Deal with an existing room at the location
        if (self.grid[y][x] is not None):
            # Use 1/3 chance to connect that existing adjoining room
            if random.randint(0,2) is 0:
                # Connect the existing rooms together
                prev_room.connect_rooms(self.grid[y][x], direction)
            return None
        # Create a new room otherwise
        else:
            random_room = random.choice(room_type)
            title_input = f"{random.choice(size)} {random.choice(adj)} {random_room[0]}"
            new_room = Room(self.rooms_created + 1, title_input, random_room[1], x, y)
            # Note that in Django, you'll need to save the room after you create it
            # Save the room in the World grid
            self.grid[y][x] = new_room
            # Connect the room to the previous room
            prev_room.connect_rooms(new_room, direction)
            # Increment the number of rooms created so far
            self.rooms_created += 1
            new_room.save()
            return new_room
    def print_rooms(self):
        '''
        Print the rooms in room_grid in ascii characters.
        '''
        # Add top border
        str = "# " * ((3 + self.width * 5) // 2) + "\n"
        # The console prints top to bottom but our array is arranged
        # bottom to top.
        #
        # We reverse it so it draws in the right direction.
        reverse_grid = list(self.grid) # make a copy of the list
        reverse_grid.reverse()
        for row in reverse_grid:
            # PRINT NORTH CONNECTION ROW
            str += "#"
            for room in row:
                if room is not None and room.n_to is not None:
                    str += "  |  "
                else:
                    str += "     "
            str += "#\n"
            # PRINT ROOM ROW
            str += "#"
            for room in row:
                if room is not None and room.w_to is not None:
                    str += "-"
                else:
                    str += " "
                if room is not None:
                    str += f"{room.id}".zfill(3)
                else:
                    str += "   "
                if room is not None and room.e_to is not None:
                    str += "-"
                else:
                    str += " "
            str += "#\n"
            # PRINT SOUTH CONNECTION ROW
            str += "#"
            for room in row:
                if room is not None and room.s_to is not None:
                    str += "  |  "
                else:
                    str += "     "
            str += "#\n"
        # Add bottom border
        str += "# " * ((3 + self.width * 5) // 2) + "\n"
        # Print string
        print(str)


w = World()
num_rooms = 500
width = 25
height = 25
w.generate_rooms(width, height, num_rooms)
players=Player.objects.all()
for p in players:
    p.currentRoom=1
    p.save()

# print(f"\n\nWorld\n  height: {height}\n  width: {width},\n  num_rooms: {num_rooms}\n")

  # r_outside = Room(title="Outside Cave Entrance",
#                description="North of you, the cave mount beckons", x=0, y=0)
# r_foyer = Room(title="Foyer", description="""Dim light filters in from the south. Dusty
# passages run north and east.""", x=0, y=1)
# r_overlook = Room(title="Grand Overlook", description="""A steep cliff appears before you, falling
# into the darkness. Ahead to the north, a light flickers in
# the distance, but there is no way across the chasm.""", x=0, y=2)
# r_narrow = Room(title="Narrow Passage", description="""The narrow passage bends here from west
# to north. The smell of gold permeates the air.""", x=1, y=1)
# r_treasure = Room(title="Treasure Chamber", description="""You've found the long-lost treasure
# chamber! Sadly, it has already been completely emptied by
# earlier adventurers. The only exit is to the south.""", x=1, y=2)
# r_outside.save()
# r_foyer.save()
# r_overlook.save()
# r_narrow.save()
# r_treasure.save()

# # Link rooms together
# r_outside.connectRooms(r_foyer, "n")
# r_foyer.connectRooms(r_outside, "s")
# r_foyer.connectRooms(r_overlook, "n")
# r_overlook.connectRooms(r_foyer, "s")
# r_foyer.connectRooms(r_narrow, "e")
# r_narrow.connectRooms(r_foyer, "w")
# r_narrow.connectRooms(r_treasure, "n")
# r_treasure.connectRooms(r_narrow, "s")

