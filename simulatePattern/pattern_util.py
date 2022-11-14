"""
pattern_util.py
Utility functions for rule based simulations.
"""

from board_base import opponent, EMPTY, PASS, BORDER, GO_COLOR, GO_POINT, NO_POINT
from board import GoBoard
from board_util import GoBoardUtil
from pattern import pat3set
import numpy as np
import random
from typing import List, Tuple


class PatternUtil(object):

    @staticmethod
    def neighborhood_33(board, point):
        """
        Get the pattern around point.
        Returns
        -------
        patterns :
        Set of patterns in the same format of what michi pattern base provides. Please refer to pattern.py to see the format of the pattern.
        """
        positions = [point+board.NS-1, 
                     point+board.NS, 
                     point+board.NS+1,
                     point-1, 
                     point, 
                     point+1,
                     point-board.NS-1, 
                     point-board.NS, 
                     point-board.NS+1]
                     
                     #positions = [point-board.NS-1, point-board.NS, point-board.NS+1,
                     #            point-1, point, point+1,
                     #            point+board.NS-1, point+board.NS, point+board.NS+1]

        pattern = 0  # based on given rule 4**n, see assignment 3
        for d in range(9):
            if d == 4:
                pattern += 0
            elif d < 4:
                if board.board[positions[d]] == board.current_player:
                    pattern += 1 * (4 ** d)
                elif board.board[positions[d]] == GoBoardUtil.opponent(board.current_player):
                    pattern += 2 * (4 ** d)
                elif board.board[positions[d]] == EMPTY:
                    pattern += 0
                elif board.board[positions[d]] == BORDER:
                    pattern += 3 * (4 ** d)
            elif d > 4:
                if board.board[positions[d]] == board.current_player:
                    pattern += 1 * (4 ** (d-1))
                elif board.board[positions[d]] == GoBoardUtil.opponent(board.current_player):
                    pattern += 2 * (4 ** (d-1))
                elif board.board[positions[d]] == EMPTY:
                    pattern += 0
                elif board.board[positions[d]] == BORDER:
                    pattern += 3 * (4 ** (d-1))
        return pattern

    @staticmethod
    def last_moves_empty_neighbors(board: GoBoard) -> List:
        """
        Get the neighbors of last_move and second last move.

        Returns
        -------
        points:
        points which are neighbors of last_move and last2_move
        """
        nb_list = []
        for c in board.last_board_moves():
            nb_of_c_list = list(board._neighbors(c) + board._diag_neighbors(c))
            nb_list += [
                d for d in nb_of_c_list if board.board[d] == EMPTY and d not in nb_list
            ]
        return nb_list

    @staticmethod
    def generate_pattern_moves(board: GoBoard) -> List:
        """
        Generate a list of moves that match pattern.
        This only checks moves that are neighbors of the moves in the last two steps.
        See last_moves_empty_neighbors() in board for detail.
        """
        pattern_checking_set: List[GO_POINT] = PatternUtil.last_moves_empty_neighbors(board)
        moves = []
        for p in pattern_checking_set:
            if PatternUtil.neighborhood_33(board, p) in pat3set:
                assert p not in moves
                assert board.board[p] == EMPTY
                moves.append(p)
        return moves
        

    #@staticmethod
    #def filter_moves_and_generate(board, moves, check_selfatari):
        #"""
        #Move filter function.
        #"""
        #color = board.current_player
        #while len(moves) > 0:
            #candidate = random.choice(moves)
            #if PatternUtil.filter(board, candidate, color, check_selfatari):
                #moves.remove(candidate)
            #else:
                #return candidate
        #return None
    
    @staticmethod
    def filter_moves(board, moves, check_selfatari):
        color = board.current_player
        good_moves = []
        for move in moves:
            if not PatternUtil.filter(board,move,color,check_selfatari):
                good_moves.append(move)
        return good_moves
    
    # return True if move should be filtered
    @staticmethod
    def filleye_filter(board, move, color):
        assert move != None
        return not board.is_legal(move, color) or board.is_eye(move, color)
    
    # return True if move should be filtered
    @staticmethod
    def selfatari_filter(board, move, color):
        return (  PatternUtil.filleye_filter(board, move, color)
                or PatternUtil.selfatari(board, move, color)
                )
    
    # return True if move should be filtered
    @staticmethod
    def filter(board, move, color, check_selfatari):
        if check_selfatari:
            return PatternUtil.selfatari_filter(board, move, color)
        else:
            return PatternUtil.filleye_filter(board, move, color)

    @staticmethod
    def selfatari(board, move, color):
        max_old_liberty = PatternUtil.blocks_max_liberty(board, move, color, 2)
        if max_old_liberty > 2:
            return False
        cboard = board.copy()
        # swap out true board for simulation board, and try to play the move
        isLegal = cboard.play_move(move, color)
        if isLegal:
            new_liberty = cboard._liberty(move, color)
            if new_liberty==1:
                return True
        return False
            
    @staticmethod
    def blocks_max_liberty(board, point, color, limit) -> int:
        assert board.board[point] == EMPTY
        max_lib = -1 # will return this value if this point is a new block
        neighbors = board._neighbors(point)
        for n in neighbors:
            if board.board[n] == color:
                num_lib = board._liberty(n, color)
                if num_lib > limit:
                    return num_lib
                if num_lib > max_lib:
                    max_lib = num_lib
        return max_lib
 
     
    @staticmethod
    def generate_move_with_filter(board, use_pattern):
        """
        Arguments
        ---------
        check_selfatari: filter selfatari moves?
        Note that even if True, this filter only applies to pattern moves
        use_pattern: Use pattern policy?
        """
        move = NO_POINT
        if use_pattern:
            moves,values = PatternUtil.generate_pattern_moves(board)
            newValues = []
            total = 0
            for val in values:
                total += val
            for val in values:
                newValues.append(val / total)
            x = random.uniform(0,1)
            totalProba = 0.0
            i = 0
            while i < len(moves):
                totalProba += newValues[i]
                if x < totalProba:
                    break
                i += 1
            if i < len(moves):
                move = moves[i]
            #move = PatternUtil.filter_moves_and_generate(board, moves, check_selfatari)
        if move == NO_POINT:
            move = GoBoardUtil.generate_random_move(board, board.current_player,False)
        return move, newValues
    
    @staticmethod
    def generate_all_policy_moves(board, pattern, check_selfatari):
        """
        generate a list of policy moves on board for board.current_player.
        Use in UI only. For playing, use generate_move_with_filter
        which is more efficient
        """
        if pattern:
            pattern_moves = []
            pattern_moves = PatternUtil.generate_pattern_moves(board)
            pattern_moves = PatternUtil.filter_moves(
                board, pattern_moves, check_selfatari
            )
            if len(pattern_moves) > 0:
                return pattern_moves, "Pattern"
        return GoBoardUtil.generate_random_moves(board, False), "Random"
            
    @staticmethod
    
    def playGame(board, color, **kwargs) -> GO_COLOR:
        """
        Run a simulation game according to give parameters.
        """
        komi = kwargs.pop('komi', 0)
        limit = kwargs.pop('limit', 1000)
        random_simulation = kwargs.pop('random_simulation',True)
        use_pattern = kwargs.pop('use_pattern',True)
        #check_selfatari = kwargs.pop('check_selfatari',True)
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)
        nuPasses = 0
        for _ in range(limit):
            color = board.current_player
            if random_simulation:
                move = GoBoardUtil.generate_random_move(board,color,False)
            else:
                move = PatternUtil.generate_move_with_filter(board,use_pattern)[0]
            
            board.play_move(move, color)
    
        winner = GoBoardUtil.opponent(color)
        return winner
