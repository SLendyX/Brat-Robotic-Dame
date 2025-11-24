import socket
import threading
import time
from draughts import Board, Move, WHITE, BLACK
from draughts.engine import HubEngine, Limit

#threading
run_event = threading.Event()

#draughts
board = Board(variant="standard", fen="startpos")

#"startpos"

#engine
engine = HubEngine(["kr_hub.exe", "hub"])
engine.init()
limit = Limit(time=10)

HOST = '127.0.0.3'  # Localhost
PORT = 1234         # Match robot's remote port


def getKings(board):
    splited = board.fen.split("K")
    kings = []
    if len(splited) > 1:
        for i in range(1, len(splited)):
            if splited[i].split(sep=":", maxsplit=1)[0].isdigit():
                kings.append(int(splited[i].split(sep=":", maxsplit=1)[0]))
            elif splited[i].split(sep=",", maxsplit=1)[0].isdigit():
                kings.append(int(splited[i].split(sep=",", maxsplit=1)[0]))
    return kings



def game_loop(board, engine, conn, choice):
    kingLen = 0
    oldKings = []
    if choice == 1:
        while not board.is_over():
            run_event.wait()  
            
            # Simulate calculating a move
            hasPromoted = 0
            engine_move = engine.play(board, limit, ponder=False)
            board.push(engine_move.move)

            kings = getKings(board=board)
        
            if kingLen < len(kings):
                hasPromoted = 1

            kingLen = len(kings)

            next_move = f'{engine_move.move.pdn_move},{engine_move.move.captures},{board.turn},{oldKings},{hasPromoted}'

            oldKings = kings
            # next_move = f'{42}x{48},[5,2],2,[2, 4],0'

            # Send response
            conn.sendall(next_move.encode())

            while True:
                # Suspend here until robot sends a message
                data = conn.recv(1024)  # Blocks until data is received
                if not data:
                    break  # Connection closed

                message = data.decode().strip().lower()
                print("Received:", message)

                if message == "done":
                    print("Robot finished. Proceeding...")
                    break  # or continue with next logic
            time.sleep(1)
    else:
        choice = int(get_choice("Choose a colour:\n1)black\n2)white", lambda c: not c.isnumeric() or int(c) < 1 or int(c) > 2))

        if choice == -1:
            return

        while not board.is_over():            
            # Simulate calculating a move
            hasPromoted = 0
            #player

            pdn_move = ""
            captures = []

            if board.turn == choice:
                while True:
                    legal_moves = [element.pdn_move  for element in board.legal_moves()]

                    print(board)
                    print("This are your legal moves:\n")
                    [print(f"{i+1}) {legal_moves[i]}") for i in range(0, len(legal_moves))]     

                    move_index = int(get_choice("", lambda c: not c.isnumeric() or int(c) < 1 or int(c) > len(legal_moves)))-1

                    if move_index == -2:
                        return

                    new_move = Move(board=board, pdn_move=legal_moves[move_index])

                    print(board.push(new_move))

                    answer = get_choice("This your move, are you sure you want to proceed?(Y/N)", lambda c: c != "y" and c != "n")

                    if answer == -1:
                        return

                    if answer == "y":
                        pdn_move = new_move.pdn_move
                        captures = new_move.captures    
                        break
                    else:
                        board.pop()

                    
            else:           
                engine_move = engine.play(board, limit, ponder=False)
                board.push(engine_move.move)
                pdn_move = engine_move.move.pdn_move
                captures = engine_move.move.captures

            kings = kings = getKings(board=board)
        
            if kingLen < len(kings):
                hasPromoted = 1

            kingLen = len(kings)


            next_move = f'{pdn_move},{captures},{board.turn},{oldKings},{hasPromoted}'

            oldKings = kings
            # next_move = f'{42}x{48},[5,2],2,[2, 4],0'

            # Send response
            conn.sendall(next_move.encode())



            while True:
                # Suspend here until robot sends a message
                data = conn.recv(1024)  # Blocks until data is received
                if not data:
                    break  # Connection closed

                message = data.decode().strip().lower()
                print("Received:", message)

                if message == "done":
                    print("Robot finished. Proceeding...")
                    break  # or continue with next logic
            time.sleep(1)
    
    print("Game Over")
    print(board.winner())

        
    


def console_control():
    while True:
        cmd = input("Type start/stop: ").strip().lower()
        if cmd == "start":
            run_event.set()
            print("Resumed.")
        elif cmd == "stop":
            run_event.clear()
            print("Paused.")
        elif cmd == "exit":
            run_event.clear()
            print("Exiting...")
            break
        

def get_choice(choice_text, condition_fn):
    print(choice_text)
    choice = input().lower()

    if choice == "exit":
        return -1

    while condition_fn(choice):
        print("Invalid choice, please try again: ")
        choice = input().lower()
        if choice == "exit":
            return -1
  
    return choice   



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print("Python TCP server is running... Waiting for robot connection.")
    
    

    conn, addr = s.accept()
    with conn:        
        print('Connected by', addr)
    
        data = conn.recv(1024)
        robot_signal = data.decode().strip().lower()

        print(f"Robot signal received: {robot_signal}")      

        if robot_signal == "ready":              
    
            choice = int(get_choice("Please choose:\n1)Ai vs Ai\n2)Player vs Ai", lambda c: not c.isnumeric() or int(c) < 1 or int(c) > 2))

            if choice == 1:
            # Start the game loop in a background thread
                threading.Thread(target=game_loop, args=(board, engine, conn, choice), daemon=True).start()
            # Keep control in the main thread
                run_event.set()
                console_control()
            elif choice == 2:
                game_loop(board, engine, conn, choice)


            conn.sendall("exit".encode())

        engine.quit()
        engine.kill_process()
                
        

