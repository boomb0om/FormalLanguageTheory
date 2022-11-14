import copy
import graphviz

from cfg import CFG
from utils import Types

def get_sentential_forms_automaton(cfg, start_nterm, prefix):
	final_state_name = f"N"+prefix
	start_nterm_new = start_nterm+prefix
	states = set([start_nterm_new, final_state_name])
	transitions = []

	nterms_to_process = set()
	nterms_to_check = [start_nterm]
	nonterms2rules = cfg.get_nonterm_to_rule()
	while len(nterms_to_check) > 0:
		nterm = nterms_to_check.pop()
		for rule_ind in nonterms2rules[nterm]:
			rule = cfg.grammar[rule_ind]

			item_to = rule['right'][0]
			if item_to['type'] == Types.nonterminal:
				nterm_to = item_to['value']+prefix
				symbol_items = rule['right'][1:]
				symbol = cfg.items_to_str(symbol_items)
				transition = {
					"from": rule['left']+prefix,
					"symbol": symbol,
					"to": nterm_to,
					"data": symbol_items
				}
				if nterm_to not in states:
					nterms_to_check.append(item_to['value'])
					states.add(nterm_to)
			else:
				symbol_items = rule['right']
				symbol = cfg.items_to_str(symbol_items)
				transition = {
					"from": rule['left']+prefix,
					"symbol": symbol,
					"to": final_state_name,
					"data": symbol_items
				}
			transitions.append(transition)

			for item in symbol_items:
				if item['type'] == Types.nonterminal and item['value'] != start_nterm:
					nterms_to_process.add(item['value'])

	return SententionalAutomaton(states, start_nterm_new, final_state_name, transitions), nterms_to_process


class SententionalAutomaton:
	def __init__(self, states, start_state, final_state, transitions):
		self.states = set(states)
		self.start_state = start_state
		assert self.start_state in self.states
		self.final_state = final_state
		assert self.final_state in self.states
		# transition = {"from": , "symbol": , "to": , "data": ...}
		self.transitions = transitions
		self.build_tree()

	def build_tree(self):
		self.tree = {}
		for transition in self.transitions:
			state_from = transition['from']
			symbol = transition["symbol"]
			state_to = transition['to']
			if state_from not in self.tree:
				self.tree[state_from] = {}

			if symbol not in self.tree[state_from]:
				self.tree[state_from][symbol] = [state_to]
			else:
				self.tree[state_from][symbol].append(state_to)

	def print(self):
		print("Automaton (from -- symbol -> to)")
		for state_from, paths in self.tree.items():
			for symbol, states_to in paths.items():
				print(f"{state_from} -- {symbol} -> {states_to}")

	def export_as_graph(self, name):
		dot = graphviz.Digraph(name, format='png')
		for state in self.states:
			dot.node(state)
		for transition in self.transitions:
			dot.edge(transition['from'], transition['to'], label=transition['symbol'])
		filename = dot.render(directory='graphs')
		return filename

	def reverse(self):
		start = self.start_state
		self.start_state = self.final_state
		self.final_state = start
		#
		for i in range(len(self.transitions)):
			transition = self.transitions[i]
			transition['from'], transition['to'] = transition['to'], transition['from']
		self.build_tree()

	def to_CFG(self):
		grammar = []
		for transition in self.transitions:
			if transition['to'] in self.tree:
				rule = {
					"left": transition['from'],
					"right": transition['data'] + [{"type": Types.nonterminal, "value": transition['to']}]
				}
				grammar.append(rule)
			if transition['to'] == self.final_state:
				rule = {"left": transition['from'], "right": transition['data']}
				grammar.append(rule)
		cfg = CFG(grammar)
		return cfg