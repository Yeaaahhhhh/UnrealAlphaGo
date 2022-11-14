"""
board.py
board.py
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from typing import List, Tuple
import time
from board_base import (
    board_array_size,
    coord_to_point,
    is_black_white,
    is_black_white_empty,
    opponent,
    where1d,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    MAXSIZE,
    NO_POINT,
    GO_COLOR,
    GO_POINT,
    PASS,
)


"""
The GoBoard class implements a board and basic functions to play
moves, check the end of the game, and count the acore at the end.
The class also contains basic utility functions for writing a Go player.
For many more utility functions, see the GoBoardUtil class in board_util.py.

The board is stored as a one-dimensional array of GO_POINT in self.board.
See GoBoardUtil.coord_to_point for explanations of the array encoding.
"""
class GoBoard(object):
    def __init__(self, size: int):
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)

    def reset(self, size: int) -> None:
        """
        Creates a start state, an empty board with given size.
        """
        self.size: int = size
        self.NS: int = size + 1
        self.WE: int = 1
        self.current_player: GO_COLOR = BLACK
        self.maxpoint: int = board_array_size(size)
        self.board: np.ndarray[GO_POINT] = np.full(self.maxpoint, BORDER, dtype=GO_POINT)
        self._initialize_empty_points(self.board)
        self.ko_recapture: GO_POINT = NO_POINT
        self.last_move: GO_POINT = NO_POINT
        self.last2_move: GO_POINT = NO_POINT
        self.to_win_move: GO_POINT = NO_POINT
        self.time: int = 0
        self.valid_points = self.validPoint()
    def copy(self) -> 'GoBoard':
        b = GoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

        
    def get_color(self, point: GO_POINT) -> GO_COLOR:
        return self.board[point]

    def pt(self, row: int, col: int) -> GO_POINT:
        return coord_to_point(row, col, self.size)

        
        
    def is_legal(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check whether it is legal for color to play on point
        This method tries to play the move on a temporary copy of the board.
        This prevents the board from being modified by the move
        """
        board_copy: GoBoard = self.copy()
        try:
            can_play_move = board_copy.play_move(point, color)
            return True
        except ValueError:
            return False

        
           
    def get_empty_points(self) -> np.ndarray:
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def row_start(self, row: int) -> int:
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1
        
        
    def _initialize_empty_points(self, board_array: np.ndarray) -> None:
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start: int = self.row_start(row)
            board_array[start : start + self.size] = EMPTY

    def is_eye(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge  # 0 at edge, 1 in center
        
        
    def _is_surrounded(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        check whether empty point is surrounded by stones of color
        (or BORDER) neighbors
        """
        for nb in self._neighbors(point):
            nb_color = self.board[nb]
            if nb_color != BORDER and nb_color != color:
                return False
        return True

    def _has_liberty(self, block: np.ndarray) -> bool:
        """
        Check if the given block has any liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            empty_nbs = self.neighbors_of_color(stone, EMPTY)
            if empty_nbs:
                return True
        return False
        
        
    def _block_of(self, stone: GO_POINT) -> np.ndarray:
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        color: GO_COLOR = self.get_color(stone)
        assert is_black_white(color)
        return self.connected_component(stone)

    def connected_component(self, point: GO_POINT) -> np.ndarray:
        """
        Find the connected component of the given point.
        """
        marker = np.full(self.maxpoint, False, dtype=np.bool_)
        pointstack = [point]
        color: GO_COLOR = self.get_color(point)
        assert is_black_white_empty(color)
        marker[point] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker
        
        
    def _detect_and_process_capture(self, nb_point: GO_POINT) -> GO_POINT:
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
        and returns NO_POINT otherwise.
        """
        opp_block = self._block_of(nb_point)
        return not self._has_liberty(opp_block)


    def play_move(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Play a move of color on point
        Returns whether move was legal
        """
        
        assert is_black_white(color)
        
        if self.board[point] != EMPTY:
            raise ValueError("occupied")
            
        opp_color = opponent(color)
        in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        neighbors = self._neighbors(point)
        
        #check for capturing
        for nb in neighbors:
            if self.board[nb] == opp_color:
                captured = self._detect_and_process_capture(nb)
                if captured:
                #undo capturing move
                    self.board[point] = EMPTY
                    raise ValueError("capture")
                    
                    
        #check for suicide
        block = self._block_of(point)
        if not self._has_liberty(block):  
            # undo suicide move
            self.board[point] = EMPTY
            raise ValueError("suicide")
            
        self.ko_recapture = NO_POINT
        '''
        if in_enemy_eye and len(single_captures) == 1:
            self.ko_recapture = single_captures[0]
        '''
        self.current_player = opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        return True
        
    def winner(self):
        if self.current_player == BLACK:
            result = WHITE
        else:
            result = BLACK
        return result

    def staticallyEvaluateForPlay(self):
        winColor = self.winner()
        assert winColor != EMPTY
        if winColor == self.current_player:
            return True
        assert winColor == opponent(self.current_player)
        return False

    def validPoint(self):
        bCoord = where1d(self.board == BLACK)
        wCoord = where1d(self.board == WHITE)
        eCoord = where1d(self.board == EMPTY)
        return np.concatenate([bCoord,wCoord,eCoord])

    def code(self):
        code = 0
        for i in self.valid_points:
            code+=  3*code + self.board[i]
        return code
    def storeResult(self,table,result):
        table.store(self.code(),result)
        return result

    def firstSolve(self,table,point):
        square = (self.size+1)**2
        edge = self.size +1
        mid = int((square+edge)/2)
        frstPoint = mid*2 - point[0]
        if time.time()> self.time:
            return False
        timeEnded = False
        codes = self.code()
        result = table.lookup(codes)
        if result != None:
            return result
        color = self.current_player
        emptyCoords = self.get_empty_points()

        if frstPoint in emptyCoords:
            timeEnded = False
            self.board[frstPoint] = color
            self.current_player = opponent(color)
            success = not self.negamaxBoolean(table)
            self.board[frstPoint] = EMPTY
            self.current_player = color
            if success:
                self.to_win_move = frstPoint
                table.store(codes,True)
                return True
        for move in emptyCoords:
            
            if self.is_legal(move,color):
                timeEnded = False
                self.board[move] = color
                self.current_player = opponent(color)
                success = not self.negamaxBoolean(table)
                self.board[move] = EMPTY
                self.current_player = color
                if success:
                    self.to_win_move = move
                    table.store(codes,True)
                    return True
        if timeEnded:
            result = self.staticallyEvaluateForPlay()
            table.store(codes,result)
            return result
        table.store(codes,False)
        return False

    def negamaxBoolean(self,table):
        
        if time.time() > self.time:
            return False
        timeEnded = False
        codes = self.code()
        result = table.lookup(codes)
        if result != None:
            return result
        color = self.current_player
        emptyCoords = self.get_empty_points()

        for move in emptyCoords:
            
            if self.is_legal(move,color):
                timeEnded = False
                self.board[move] = color
                self.current_player = opponent(color)
                success = not self.negamaxBoolean(table)
                self.board[move] = EMPTY
                self.current_player = color
                if success:
                    self.to_win_move = move
                    table.store(codes,True)
                    return True
        if timeEnded:
            result = self.staticallyEvaluateForPlay()
            table.store(codes,result)
            return result
        table.store(codes,False)
        return False


    def findWinner(self,point):
        
        table = transpositiontable()
        if point == None:
            return self.negamaxBoolean(table)
        else:
            return self.firstSolve(table,point)


    def firstPlay(self):
        
        bCoord = where1d(self.board == BLACK)
        wCoord = where1d(self.board == WHITE)
        point = np.concatenate([bCoord,wCoord])
        if len(point) == 1:
            return point
        return
    def solve(self,color,timelimit):
        self.time = time.time()+timelimit
        
        timeEnded = False
        point = self.firstPlay()
        checkWin = self.findWinner(point)
        if time.time()>self.time:
            timeEnded = True
        if checkWin == (color == self.current_player):
            return True, timeEnded,self.to_win_move
        else:
            return False, timeEnded,self.to_win_move

    def neighbors_of_color(self, point: GO_POINT, color: GO_COLOR) -> List:
        """ List of neighbors of point of given color """
        nbc: List[GO_POINT] = []
        for nb in self._neighbors(point):
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def _neighbors(self, point: GO_POINT) -> List:
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point: GO_POINT) -> List:
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1,
                point - self.NS + 1,
                point + self.NS - 1,
                point + self.NS + 1]

    def last_board_moves(self) -> List:
        """
        Get the list of last_move and second last move.
        Only include moves on the board (not NO_POINT, not PASS).
        """
        board_moves: List[GO_POINT] = []
        return board_moves

        
class transpositiontable(object):
    def __init__(self):
            self.table = {}

    # Used to print the whole table with print(tt)
    def __repr__(self):
        return self.table.__repr__()
        
    def store(self, code, score):
        self.table[code] = score
    
    # Python dictionary returns 'None' if key not found by get()
    def lookup(self, code):
        return self.table.get(code)