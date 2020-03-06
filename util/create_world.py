from django.contrib.auth.models import User
from adventure.models import Player, Room
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
    ["Top Secret Labs Team HQ", "Shhhh, it's a secret! You shrug and move on."],
    ["Abyss", "You fall into an endless abyss! ...luckily you were just dreaming. Better move on."],
    ["Dirtmouth", "A desolate town of bugs, with a creepy well. You don't like platformers though, so time to leave."],
    ["Theatre", f"Movies and popcorn! You kick back and watch {movies[random.randint(0, 3)]} before continuing on your journey"],
    ["Cave", "You enter a cave. It's cold and damp. You don't like that."]
]

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
        new_room_ids_to_process = []
        room_ids_with_space_nearby = []
        direction_options = ["n","e","s","w"]
        # Create the very first room right in the center as the "seed"
        seed_room = Room(title="Starting Room", description="Enjoy your adventure!", x=x, y=y)
        seed_room.save()
        self.grid[y][x] = seed_room.id
        self.rooms_created = 1
        new_room_ids_to_process.append(seed_room.id)
        # start the players in the seed room
        players = Player.objects.all()
        for p in players:
            p.currentRoom=seed_room.id
            p.save()
        # While there are rooms to be created...
        while self.rooms_created < num_rooms:
            # If there are new rooms that haven't yet had random branches calculated, get the first from queue
            if len(new_room_ids_to_process) > 0:
                # Grab the first room from the list
                current_room_id = new_room_ids_to_process.pop()
                # Randomly choose a number of directions to branch in
                num_dir = random.randint(0,4)
                # Randomly choose the appropriate number of directions
                dirs = random.sample(direction_options, num_dir)
                # If it's not going to branch in all directions, then add to the list of rooms that have space nearby
                if len(dirs) < 4:
                    room_ids_with_space_nearby.append(current_room_id)
            # If there aren't any new rooms left, start searching among the previously created rooms
            # and branch off in all directions still available
            else:
                current_room_id = None
                while current_room_id is None and len(room_ids_with_space_nearby) > 0:
                    # Grab the first room from the list
                    room = Room.objects.get(id=room_ids_with_space_nearby.pop())
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
                        current_room_id = room.id
            # For each provided direction try to make a room there
            for direction in dirs:
                new_room = self.add_room(current_room_id, direction)
                if new_room is not None:
                    # If a new room was created, add it to the queue for branching
                    new_room_ids_to_process.append(new_room)
    # Try to add a new room
    #   prev_room: a Room that the new room is adjacent to
    #   direction: the direction from the prev_room that the new room should be created
    def add_room(self, prev_room_id, direction):
        prev_room = Room.objects.get(id=prev_room_id)
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
                prev_room.connectRooms(Room.objects.get(id=self.grid[y][x]), direction)
            return None
        # Create a new room otherwise
        else:
            random_room = random.choice(room_type)
            title_input = f"{random.choice(size)} {random.choice(adj)} {random_room[0]}"
            new_room = Room(title=title_input, description=random_room[1], x=x, y=y)
            new_room.save()
            # Note that in Django, you'll need to save the room after you create it
            # Save the room in the World grid
            self.grid[y][x] = new_room.id
            # Connect the room to the previous room
            prev_room.connectRooms(Room.objects.get(id=new_room.id), direction)
            # Increment the number of rooms created so far
            self.rooms_created += 1
            return new_room.id

num_rooms = 500
width = 25
height = 25
World().generate_rooms(width, height, num_rooms)