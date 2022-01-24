#!/usr/bin/python3
# -*- coding: utf-8 -*

"""
Solve Freecell with tree search and evolutionary algorithm on best solvers
"""

import random
import sys
import freecell as fc
import random

MAX_ITER_DEPTH = 2000
PARAMS = 6
SORTED_DECK = [fc.Card(j, i) for j in fc.SUITS for i in range(1, len(fc.CARD_VALUE)+1)]

class StateData(object):
    def __init__(self, state, weight, choice, choice_hash):
        self.state = state
        self.weight = weight
        self.choice = choice
        self.choice_hash = choice_hash

class Solver(object):
    def __init__(self, init_state, strategy):
        self.init_state = init_state
        self.strategy = strategy

        self._iter = 0
        self._path = []
        self._path_hash = set()

    @staticmethod
    def hash_choice(choice, state):
        ret = ",".join([str(c.uid) for c in choice.cards]) + ":"
        col_orig_str = choice.col_orig
        if choice.col_orig != fc.COL_FC:
            col_orig_str = ",".join([str(c.uid) for c in state.columns[choice.col_orig][:-len(choice.cards)]])
        col_dest_str = choice.col_dest
        if choice.col_dest != fc.COL_BASE and choice.col_dest != fc.COL_FC:
            col_dest_str = ",".join([str(c.uid) for c in state.columns[choice.col_dest]])
        ret += "-".join(sorted([col_orig_str, col_dest_str]))
        return ret


    def _weight_state(self, state):
        """ .in base/52
            .in serie/remaining
            .max_mvt/13 (max 1)
            .to base/choices
            .from fc/choices
            .free col & not for fc/choices
        """
        if state.is_won:
            return 1.0

        in_base = sum([len(state.bases.get(k)) for k in fc.SUITS])
        in_base_norm = in_base / 52.0

        in_serie = sum([len(state.column_series[i]) for i in range(0, fc.COLUMN)]) / (52.0 - in_base)

        mvt = min(state.max_mvt / 13.0, 1.0)

        choices = state.compute_choices()
        to_base = 0.0
        from_fc = 0.0
        free_col = 0.0
        for c in choices:
            if c.col_dest == fc.COL_BASE:
                to_base += 1.0
            if c.col_orig == fc.COL_FC:
                from_fc += 1.0
            elif len(state.columns[c.col_orig]) == len(c.cards) and c.col_dest != fc.COL_FC:
                free_col += 1.0
        if len(choices) > 0:
            to_base = to_base / len(choices)
            from_fc = from_fc / len(choices)
            free_col = free_col / len(choices)

        state_weight = (in_base_norm, in_serie, mvt, to_base, from_fc, free_col)

        ret = 0
        for i in range(PARAMS):
            ret += state_weight[i]*self.strategy[i]
        return float(ret/PARAMS)

    
    def solve(self):
        self._play(StateData(self.init_state, self._weight_state(self.init_state), None, ""), -2)
        print(self._iter)
        return self._path

    def _play(self, state_data, best_weight):
        #print(self._iter, state_data.weight, best_weight)
        #print(state_data.state)
        #input()
        self._iter += 1
        if self._iter > MAX_ITER_DEPTH:
            return False
        
        self._path.append(state_data.choice)
        self._path_hash.add(state_data.choice_hash)

        if state_data.state.is_won:
            return True
        
        # keep knowledge of best visited state
        not_better = state_data.weight < best_weight
        nbw = max(state_data.weight, best_weight)
        
        # Compute & sort list of next accessible state
        next_states_data = []
        for c in state_data.state.compute_choices():
            # skip choice that we already did/revert past ones
            hc = Solver.hash_choice(c, state_data.state)
            if hc in self._path_hash:
                continue
          
            ns = state_data.state.apply(c)
            next_states_data.append(StateData(ns, self._weight_state(ns), c, hc))
        next_states_data.sort(key=lambda x: x.weight, reverse=True)

        # recurse on next states, stop when won or if state is not best
        ret = False
        for nsd in next_states_data:
            ret = self._play(nsd, nbw)
            if ret or not_better:
                break

        if not ret:
            self._path.pop()
            self._path_hash.remove(state_data.choice_hash)
        return ret
        

def solve_game(game):
    solvers = [(1.0,0.5,1.0,0.0,1.0,0.0)]
    solvers.extend([(random.random(),random.random(),random.random(),random.random(),random.random(),random.random()) for _ in range(99)])
    
    for s in solvers:
        print(s)
        solver = Solver(game.state, s)
        res = solver.solve()
        if len(res) > 0:
            for c in res:
                print(c)
            break

def train(nb_games):
    pass

if __name__ == "__main__":

    usage = "./fcml2022.py solve <game file>\n" + \
            "              train <number of games>"

    if len(sys.argv) < 2:
        print(usage)
        exit(1)

    # Training mode
    if sys.argv[1] == "train":
        if len(sys.argv) < 4:
            print(usage)
            exit(1)

        # Read parameter
        ngames = 0
        try:
            ngames = int(sys.argv[3])
        except ValueError as v:
            print(v)
            print(usage)
            exit(1)

        train(ngames)

    # Solving mode
    elif sys.argv[1] == "solve":
        if len(sys.argv) < 3:
            print(usage)
            exit(1)

        filename = sys.argv[2]
        try:
            game = fc.FreecellGame.from_file(filename)
        except:
            print("Please give a valid game file")
            exit(1)
        
        solve_game(game)

    else:
        print(usage)
        exit(1)
    
    exit(0)
