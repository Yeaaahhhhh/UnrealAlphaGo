#!/usr/bin/env python3
#/usr/bin/python3
# Set the path to your python3 above
import gtp_connection as gtp
from gtp_connection import GtpConnection, point_to_coord,format_point
from board_util import (
    GO_POINT,
    GoBoardUtil,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    PASS,
    MAXSIZE,
    coord_to_point,
)

from board import GoBoard 
from ucb import runUcb
import numpy as np
import argparse
import os, sys
from board_base import opponent, EMPTY, PASS, BORDER, GO_COLOR, GO_POINT, NO_POINT
from typing import Tuple
#from board_score import winner
import random


class Go0:
    def __init__(self, sim=10, move_select='simple', sim_rule='random', size=7, limit=100):
        """
        NoGo player that selects moves randomly from the set of legal moves.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "NoGoAssignment2"
        self.version = 1.0
        self.sim = sim
        self.limit = limit
        self.use_ucb = False if move_select =='simple' else True
        self.random_simulation = True if sim_rule == 'random' else False
        self.use_pattern = not self.random_simulation
        self.pattern = np.empty(shape=(0))
        sys.path.insert(0, os.path.__file__)
        dirpath = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(dirpath, "weights.txt")
        if os.path.isfile(filepath):
            sys.stderr.write("weights.txt loaded\n")
            data = np.loadtxt(filepath)
            self.pattern = np.ones(len(data))
            for i in range(len(self.pattern)):
                self.pattern[i] = data[i][1]
        else:
            print("weights.txt missing")
        
    def select_best_move(self, board, moves, moveWins):
        """
            Move select after the search.
            """
        max_child = np.argmax(moveWins)
        #print('I select ', moves[max_child], moveWins, max_child)
        return moves[max_child]

    def generate_random_move(self, board):
        randMoves, prob = self.simulation_policy(board)
        index = random.randrange(len(randMoves))
        #print('What are moves?', randMoves)
        #print('hello?',randMoves[index])
        return randMoves[index]

    def generate_pattern_move(self, board):
        move, moveWin = self.simulation_policy(board)
        return self.select_best_move(board, move, moveWin)

    def coord_to_num(self, coord, board_size): #very smart!
        row, col = gtp.move_to_coord(coord, board_size)
        return row*(board_size+1)+(col)

    def get_pattern_address(self, board, point):
        #position with point excluded
        positions = [point+board.NS-1, point+board.NS, point+board.NS+1,
                        point-1, point+1,
                        point-board.NS-1, point-board.NS, point-board.NS+1]
                        
        pattern_address_decimal = 0  
        for i in range(8):
            pattern_address_decimal += board.board[positions[i]] * (4 ** i)
        #print('This is one board', pattern_address_decimal, positions)
        return pattern_address_decimal

    def playGame(self, board: GoBoard, color: GO_COLOR) -> GO_COLOR:
        nuPasses = 0
        while True:
            legalMoves = []
            color = board.current_player
            empties = board.get_empty_points()
            for move in empties:
                if board.is_legal(move, color):
                    legalMoves.append(move) 
            if legalMoves == []:
                return opponent(color)
            if self.random_simulation: 
                #print('random')
                move = self.generate_random_move(board)
            else:
                #print('pattern')
                move = self.generate_pattern_move(board)
            move = self.coord_to_num(move, board.size)
            #print('**********', move, color)

            board.play_move(move, color)
            if move == PASS:
                return opponent(color)
            

    def simulation_policy(self, board):
        empties = board.get_empty_points()
        tempMoves = []
        tempMoves[:] = [format_point(point_to_coord(move, board.size)).lower() for move in empties]
        tempMoves = np.sort(tempMoves)
        if self.random_simulation == True:  # if random
            randMoves = []
            probabilities = []            
            color = board.current_player
            legalMoves = []
            
            for moveCord in tempMoves:
                move = self.coord_to_num(moveCord, board.size)
                if board.is_legal(move, color):
                    legalMoves.append(move)
            
            for move in legalMoves:
                coords = point_to_coord(move, board.size)
                randMoves.append(format_point(coords).lower())
                probabilities.append(str(round(1/len(legalMoves), 3))) #randomize
            return randMoves, probabilities

        else:  # if use pattern
            patternMoves = []  
            probabilityList = []
            weightSum = 0
            color = board.current_player
            for moveCord in tempMoves:
                move = self.coord_to_num(moveCord, board.size)
                #print('Move', move)
                if board.is_legal(move, color): #for every legal move
                    patternMoves.append(moveCord)
                    pattern_address = self.get_pattern_address(board, move)
                    weight = self.pattern[pattern_address]
                    probabilityList.append(weight)
                    weightSum += weight
            probabilityList[:] = [str(round((i/weightSum), 3)) for i in probabilityList]
            return patternMoves, probabilityList

    def simulate(self, board: GoBoard, move: GO_POINT, toplay: GO_COLOR) -> GO_COLOR:
        """
        Run a simulated game for a given move.
        """
        cboard = board.copy()
        cboard.play_move(move, toplay)
        opp = opponent(toplay)
        return self.playGame(cboard,opp)    
    
    def simulateMove(self, board, move, toplay):
        # simulation_engine.py file run self.sim simulations for a given move. Return number of wins
        wins = 0
        #numRun = 0
        for _ in range(self.sim):
            result = self.simulate(board, move, toplay)
            #print('WIN', result)
            if result == toplay:
                wins += 1

        return wins

    #move_selection either rr or ucb
    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        """
        Run one-ply MC simulations to get a move to play.
        """
        cboard = board.copy()
        emptyPoints = board.get_empty_points()
        moves = []
        for p in emptyPoints:
            if board.is_legal(p, color):
                moves.append(p)
        if not moves:
            return PASS
        moves.append(PASS)
        
        if self.use_ucb:
            C = 0.4  # sqrt(2) is safe, this is more aggressive
            best = runUcb(self, cboard, C, moves, color)
            return best
        else:
            moveWins = []
            #print('+++++++++++++++++',moves)
            for move in moves:
                if move < 0:
                    break
                #print('&&&&&&&&&', move)
                wins = self.simulateMove(cboard, move, color)
                moveWins.append(wins)
            #writeMoves(cboard, moves, moveWins, self.sim)
            return self.select_best_move(board, moves, moveWins)

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(Go0(), board)
    con.start_connection()

def parse_args() -> Tuple[int, str, str, bool]:
    """
    Parse the arguments of the program.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--sim",
        type=int,
        default=10,
        help="number of simulations per move, so total playouts=sim*legal_moves",
    )
    parser.add_argument(
        "--moveselect",
        type=str,
        default="simple",
        help="type of move selection: simple or ucb",
    )
    parser.add_argument(
        "--simrule",
        type=str,
        default="prob",
        help="type of simulation policy: random or rulebased or prob",
    )
    parser.add_argument(
        "--movefilter",
        action="store_true",
        default=False,
        help="whether use move filter or not",
    )

    args = parser.parse_args()
    sim = args.sim
    move_select = args.moveselect
    sim_rule = args.simrule
    move_filter = args.movefilter

    if move_select != "simple" and move_select != "ucb":
        print("moveselect must be simple or ucb")
        sys.exit(0)
    if sim_rule != "random" and sim_rule != "rulebased" and sim_rule != "prob":
        print("simrule must be random or rulebased or prob")
        sys.exit(0)

    return sim, move_select, sim_rule, move_filter
if __name__ == "__main__":
    run()
