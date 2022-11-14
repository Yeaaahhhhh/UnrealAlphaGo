# Cmput 455 sample code
# go2d.py - sketch of Go board 
# implemented as a list of lists in Python
# Written by Martin Mueller

EMPTY = 0
BLACK = 1
WHITE = 2   
MAXSIZE = 7

board = [[EMPTY for x in range(MAXSIZE)] 
                for y in range(MAXSIZE)]
print(board)
board[3][4] = BLACK
print(board)
