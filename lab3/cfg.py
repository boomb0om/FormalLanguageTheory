import copy
import itertools
import time

from utils import Types

class CFG:
	def __init__(self, parsed_grammar):
		self.grammar = parsed_grammar
		#
		self.update_terms_and_nonterms()


	def fill_elements_from_rule(self, rule):
		left = rule['left']
		self.nonterms.add(left)
		for item in rule['right']:
			if item['type'] == Types.nonterminal:
				self.nonterms.add(item['value'])
			else:
				self.terms.add(item['value'])

	def update_terms_and_nonterms(self):
		self.nonterms = set()
		self.terms = set()
		for rule in self.grammar:
			self.fill_elements_from_rule(rule)

	def get_left_nonterminals(self):
		nonterms = set()
		for rule in self.grammar:
			nonterms.add(rule['left'])
		return nonterms

	def add_rule(self, rule):
		self.fill_elements_from_rule(rule)
		self.grammar.append(rule)

	def remove_rules(self, idx_to_remove):
		for idx in sorted(idx_to_remove, reverse=True):
			self.grammar.pop(idx)

	def rename_nonterminal(self, old_name, new_name):
		self.nonterms.remove(old_name)
		self.nonterms.add(new_name)
		for rule in self.grammar:
			if rule['left'] == old_name:
				rule['left'] = new_name
			for item in rule['right']:
				if item['type'] == Types.nonterminal and item['value'] == old_name:
					item['value'] = new_name

	def get_nonterm_to_rule(self):
		nonterm_to_rule = {}
		for c, rule in enumerate(self.grammar):
			left = rule['left']
			#
			if left in nonterm_to_rule:
				nonterm_to_rule[left].append(c)
			else:
				nonterm_to_rule[left] = [c]
		return nonterm_to_rule

	def print(self, border_top=False, border_bottom=False):
		if border_top:
			print('-'*40)
		nonterm_to_rule = self.get_nonterm_to_rule()
		for nonterm, rules_indexes in nonterm_to_rule.items():
			s = f"[{nonterm}] -> "
			for rule_ind in rules_indexes:
				s_rule = ""
				for item in self.grammar[rule_ind]['right']:
					if item['type'] == Types.nonterminal:
						s_rule += f"[{item['value']}]"
					else:
						if len(item['value']) == 0:
							s_rule += "_eps_"
						else:
							s_rule += item['value']
				s_rule += " | "
				s += s_rule
			print(s[:-2])
		if border_bottom:
			print('-'*40)

	#
	# simple algos
	#
	def remove_unreachable_rules(self):
		changed = True
		while changed:
			start_grammar_count = len(self.grammar)

			nonterm_to_rule = self.get_nonterm_to_rule()
			nonterm_in_right_rules = {}
			for c, rule in enumerate(self.grammar):
				for item in rule['right']:
					if item['type'] == Types.nonterminal:
						nterm = item['value']
						if nterm in nonterm_in_right_rules:
							nonterm_in_right_rules[nterm].add(c)
						else:
							nonterm_in_right_rules[nterm] = set([c])
			# ненайденным поставим пустые массивы
			nterms_not_in_right = set(nonterm_to_rule.keys()).difference(set(nonterm_in_right_rules.keys()))
			nonterm_in_right_rules.update({i:[] for i in nterms_not_in_right})

			nonterms_to_remove = []
			for nterm in nonterm_to_rule:
				all_rules = nonterm_to_rule[nterm]
				rules_in_right = nonterm_in_right_rules[nterm]
				rules_that_lead_to_nterm = set(rules_in_right).difference(all_rules)
				if len(rules_that_lead_to_nterm) == 0:
					nonterms_to_remove.append(nterm)

			if 'S' in nonterms_to_remove:
				nonterms_to_remove.remove('S')

			rules_to_remove = []
			for nterm in nonterms_to_remove:
				rules_to_remove.extend(nonterm_to_rule[nterm])

			self.remove_rules(rules_to_remove)

			if start_grammar_count == len(self.grammar):
				changed = False

	#
	# EPSILON REMOVING
	#
	@staticmethod
	def _is_epsilon_rule(rule):
		return len(rule['right']) == 0 or (len(rule['right']) == 1 and len(rule['right'][0]['value']) == 0)

	def get_epsilon_nonterms(self):
		epsilon_terms = []
		is_epsilon = {i: False for i in self.nonterms}
		rules_to_skip = set()
		concerned_rules = {i: [] for i in self.nonterms}
		counter = [0 for i in range(len(self.grammar))]
		queue = []

		for c, rule in enumerate(self.grammar):
			left = rule['left']
			if self._is_epsilon_rule(rule):
				is_epsilon[left] = True
				epsilon_terms.append(left)
				queue.append(left)
				continue
			for item in rule['right']:
				if item['type'] == Types.nonterminal:
					concerned_rules[item['value']].append(c)
					counter[c] += 1
				else:
					rules_to_skip.add(c)

		while len(queue) > 0:
			left = queue.pop()
			rules_indexes = concerned_rules[left]
			for ind in rules_indexes:
				counter[ind] -= 1
				nonterm_in_rule_left = self.grammar[ind]['left']
				if counter[ind] == 0 and not is_epsilon[nonterm_in_rule_left] and\
					ind not in rules_to_skip:
					is_epsilon[nonterm_in_rule_left] = True
					epsilon_terms.append(nonterm_in_rule_left)
					queue.append(nonterm_in_rule_left)

		return epsilon_terms

	def is_need_to_product_new(self, rule, eps_nonterms):
		for item in rule['right']:
			if item['type'] == Types.nonterminal and item['value'] in eps_nonterms:
				return True
		return False

	def remove_only_epsilon_nonterms(self, eps_nonterms):
		eps_nonterms = set(eps_nonterms)
		terms_in_left = self.get_left_nonterminals()
		# nonterms_to_remove - терминалы у которых было только одно правило - вывод эпсилон
		nonterms_to_remove = eps_nonterms.difference(terms_in_left)
		if len(nonterms_to_remove) == 0:
			return
		changed = True
		while changed:
			changed = False
			for c in range(len(self.grammar)-1, -1, -1):
				rule = self.grammar[c]
				for i in range(len(rule['right'])-1, -1, -1):
					item = rule['right'][i]
					if item['type'] == Types.nonterminal and item['value'] in nonterms_to_remove:
						rule['right'].pop(i)
						changed = True
				if len(rule['right']) == 0:
					self.grammar.pop(c)
					changed = True
			terms_in_left_new = self.get_left_nonterminals()
			if len(terms_in_left_new) < len(terms_in_left):
				nonterms_to_remove.update(terms_in_left.difference(terms_in_left_new))
				terms_in_left = terms_in_left_new
				changed = True
			if not changed:
				break

	def remove_epsilon(self):
		eps_nonterms = self.get_epsilon_nonterms()
		eps_is_derived_in_S = 'S' in eps_nonterms

		# создаем копию грамматики
		cfg_new = CFG(copy.deepcopy(self.grammar))
		for c, rule in enumerate(self.grammar):
			# get indexes to product
			nonterminal_ids_to_product = []
			for i, item in enumerate(rule['right']):
				if item['type'] == Types.nonterminal and item['value'] in eps_nonterms:
					nonterminal_ids_to_product.append(i)
			# get all productions
			counter = 0
			for product_res in itertools.product((False, True), repeat=len(nonterminal_ids_to_product)):
				counter += 1
				if len(product_res) == 0:
					break
				if counter == 1:
					continue # элемент где ничего не выброшено уже есть

				new_rule = {"left": rule['left'], "right": copy.copy(rule['right'])}
				for i, idx in enumerate(nonterminal_ids_to_product[::-1]): # обязательно идем с конца
					if product_res[i]:
						new_rule['right'].pop(idx)
				cfg_new.add_rule(new_rule)
		# удаляем eps правила
		idx_to_remove = []
		for c, rule in enumerate(cfg_new.grammar):
			if self._is_epsilon_rule(rule):
				idx_to_remove.append(c)
		cfg_new.remove_rules(idx_to_remove)
		# из правых частей остальных правил удаляем нетерминалы, которые переходили ТОЛЬКО в эпсилон
		cfg_new.remove_only_epsilon_nonterms(eps_nonterms)
		# заменяем стартовый символ
		if eps_is_derived_in_S:
			new_s_name = "S1"
			cfg_new.rename_nonterminal("S", new_s_name)
			cfg_new.add_rule({"left": "S", "right":[{"type": Types.nonterminal, "value": new_s_name}]})
			cfg_new.add_rule({"left": "S", "right":[{"type": Types.terminal, "value": ""}]})
		
		self.grammar = cfg_new.grammar
		self.update_terms_and_nonterms()

	#
	# Left recursion removal
	#
	def remove_direct_left_recursion(self, nonterm):
		# получаем нетерминалы и правила у которых непосредственная левая рекурсия
		nonterm_rules = self.get_nonterm_to_rule()[nonterm]
		leftrec_rules = []
		for c, rule in enumerate(self.grammar):
			if rule['left'] != nonterm:
				continue
			first_product = rule['right'][0]
			if first_product['type'] == Types.nonterminal and first_product['value'] == nonterm:
				assert len(rule['right']) > 1, "идентичных правил ([A]->[A]) не должно быть!"
				leftrec_rules.append(c)

		# no direct left rec
		if len(leftrec_rules) == 0:
			return

		# правила к которым надо добавлять
		rules_add_to = []
		rules_add_to = list(
			set(nonterm_rules).difference(set(leftrec_rules))
		)

		# добавляем новые правила для A
		new_nonterm_name = nonterm+'l'
		# новые правила для нетерминала
		if len(rules_add_to) == 0:
			new_rule = {
				"left": nonterm,
				"right": [{"type":	Types.nonterminal, "value": new_nonterm_name}]
			}
			self.add_rule(new_rule)
		else:
			for rule_ind in rules_add_to:
				new_rule = {
					"left": nonterm,
					"right": copy.copy(self.grammar[rule_ind]['right'])
				}
				new_rule['right'].append({
					"type":	Types.nonterminal,
					"value": new_nonterm_name
				})
				self.add_rule(new_rule)
		# правила для нового нетерминала
		for rule_ind in leftrec_rules:
			new_rule = {
				"left": new_nonterm_name,
				"right": copy.copy(self.grammar[rule_ind]['right'][1:])
			}
			self.add_rule(new_rule)
			new_rule2 = new_rule.copy()
			new_rule2['right'] = new_rule['right'].copy() # copy rule
			new_rule2['right'].append({
				"type": Types.nonterminal,
				"value": new_nonterm_name
			})
			self.add_rule(new_rule2)

		# удаляю старые правила с левой рекурсией
		self.remove_rules(leftrec_rules)

	def index_nonterminals(self):
		nonterm2index = {'S': 1}
		ind = 2
		for rule in self.grammar:
			left = rule['left']
			if left not in nonterm2index:
				nonterm2index[left] = ind
				ind += 1
			for item in rule['right']:
				if item['type'] == Types.nonterminal:
					if item['value'] not in nonterm2index:
						nonterm2index[item['value']] = ind
						ind += 1
		return nonterm2index, ind-1

	def remove_left_recursion(self):
		nterm2index, max_ind = self.index_nonterminals()
		index2nterm = {v: k for k,v in nterm2index.items()}
		nterms_ordered = [index2nterm[i] for i in range(1, max_ind+1)]
		for i in range(len(nterms_ordered)):
			ai = nterms_ordered[i]
			for j in range(0, i):
				nonterm2rule = self.get_nonterm_to_rule()
				aj = nterms_ordered[j]
				products_to_del = []
				for c, rule in enumerate(self.grammar):
					if (rule['left'] == ai and rule['right'][0]['type'] == Types.nonterminal and \
						rule['right'][0]['value'] == aj):
						products_to_del.append(c)

				for rule_ind in products_to_del:
					aj_rules = nonterm2rule[aj]
					for x_rule in aj_rules:
						new_rule = {
							"left": ai,
							"right": self.grammar[x_rule]['right'].copy()
						}
						right_part_from_ai = self.grammar[rule_ind]['right'][1:].copy()
						new_rule["right"].extend(right_part_from_ai)
						self.add_rule(new_rule)

				self.remove_rules(products_to_del)

			self.remove_direct_left_recursion(ai)

		# remove unused nonterms
		self.remove_unreachable_rules()
		return nterm2index

	#
	# Greibach
	#
	def _transit_rule_gnf(self, i, nonterm2rules):
		ai = self.grammar[i]['left']
		nonterm_to_transit = self.grammar[i]['right'][0]
		rules_to_transit = nonterm2rules[nonterm_to_transit['value']]

		for ind in rules_to_transit:
			new_rule = {
				"left": ai,
				"right": self.grammar[ind]['right'].copy()
			}
			new_rule["right"].extend(self.grammar[i]['right'][1:])
			self.add_rule(new_rule)

	def to_GNF(self, debug=False):
		self.remove_epsilon()
		if debug:
			print("Грамматика после удаления эпсилон правил:")
			self.print(border_bottom=True)

		self.remove_chain_rules()
		if debug:
			print("Грамматика после удаления цепных правил:")
			self.print(border_bottom=True)

		nterm2index = self.remove_left_recursion()
		self.update_terms_and_nonterms()
		if debug:
			print("Грамматика после удаления левой рекурсии:")
			self.print(border_bottom=True)

		nterm2index = {k: v for k, v in nterm2index.items() if k in self.nonterms}
		new_nterms = self.nonterms.difference(set(nterm2index.keys()))
		for new_nterm in new_nterms:
			nterm2index[new_nterm] = 0
		nterms_ordered = [(k,v) for k,v in nterm2index.items()]
		nterms_ordered = sorted(nterms_ordered, key=lambda x: x[1])
		nterms_ordered = [i[0] for i in nterms_ordered]

		# function greibach
		for i in range(len(nterms_ordered)-1,-1,-1):
			ai = nterms_ordered[i]
			to_delete = []
			nonterm2rules = self.get_nonterm_to_rule()

			for j in range(i+1, len(nterms_ordered)):
				aj = nterms_ordered[j]
				for rule_ind in nonterm2rules[ai]:
					rule = self.grammar[rule_ind]
					first_elem = rule['right'][0]
					if first_elem['type'] == Types.nonterminal and first_elem['value'] == aj:
						self._transit_rule_gnf(rule_ind, nonterm2rules)
						to_delete.append(rule_ind)
			self.remove_rules(to_delete)

		return nterm2index

	#
	# utils
	#
	def union(self, other_cfg, prefix='n'):
		nterms_to_rename = self.nonterms.intersection(other_cfg.nonterms)
		#for nterm in nterms_to_rename:
		#	other_cfg.rename_nonterminal(nterm, nterm+prefix)
		self.grammar.extend(other_cfg.grammar)
		self.update_terms_and_nonterms()

	def remove_duplicated_rules(self):
		nonterm2rules = self.get_nonterm_to_rule()
		nonterms2rulesset = {k: set() for k in nonterm2rules.keys()}

		to_delete = []
		for nonterm, rules in nonterm2rules.items():
			rulesset = nonterms2rulesset[nonterm]
			for rule_ind in rules:
				rule_str = self.items_to_str(self.grammar[rule_ind]['right'])
				if rule_str in rulesset:
					to_delete.append(rule_ind)
				else:
					rulesset.add(rule_str)
		self.remove_rules(to_delete)

	# удаление стартового нетерминала из правых частей правил
	def _find_and_transit_s_rules(self):
		s_rules = []
		rules_with_s = []
		for c, rule in enumerate(self.grammar):
			if rule['left'] == "S":
				s_rules.append(c)
			for item in rule['right']:
				if item['type'] == Types.nonterminal and item['value'] == "S":
					rules_with_s.append(c)
					break

		for rule_ind in rules_with_s:
			rule = self.grammar[rule_ind]
			for c, item in enumerate(rule['right']):
				if item['type'] == Types.nonterminal and item['value'] == "S":
					s_ind = c
					break
			left_items = rule['right'][:c]
			right_items = rule['right'][c+1:]
			for ind in s_rules:
				s_rule = self.grammar[ind]['right'].copy()
				new_rule = {
					"left": rule["left"],
					"right": left_items+s_rule+right_items
				}
				self.add_rule(new_rule)
		self.remove_rules(rules_with_s)

		return len(rules_with_s) > 0


	def remove_start_nonterminal(self):
		S_rules = self.get_nonterm_to_rule()["S"]
		is_s_recursive = False
		for rule_ind in S_rules:
			for item in self.grammar[rule_ind]['right']:
				if item['type'] == Types.nonterminal and item['value'] == "S":
					is_s_recursive = True
					break
			if is_s_recursive:
				break

		if not is_s_recursive:
			rules_to_remove = []
			changed = True
			while changed:
				changed = self._find_and_transit_s_rules()
		else:
			pass

	#
	# remove chain rules
	#
	def is_rule_chained(self, rule):
		return len(rule['right']) == 1 and rule['right'][0]['type'] == Types.nonterminal

	def remove_chain_rules(self):
		# находим цепные правила
		chained_nonterms = []
		identincal_inds = []
		for c, rule in enumerate(self.grammar):
			if self.is_rule_chained(rule):
				if rule['right'][0]['value'] == rule['left']:
					identincal_inds.append(c)
					continue
				new_chain = (rule['left'], rule['right'][0]['value'])
				chained_nonterms.append(new_chain)
				# проверяем транзитивные цепные правила
				for i in range(len(chained_nonterms)):
					chain = chained_nonterms[i]
					if chain[1] == new_chain[0]:
						chained_nonterms.append((chain[0], new_chain[1]))
		self.remove_rules(identincal_inds)

		for chain in chained_nonterms:
			nonterm2rules = self.get_nonterm_to_rule()
			chain_rules = []
			to_delete = []
			for rule_ind in nonterm2rules[chain[0]]:
				rule = self.grammar[rule_ind]
				if self.is_rule_chained(rule) and rule['right'][0]['value'] == chain[1]:
					to_delete.append(rule_ind)
					# add new rules
					rules_to_transit = nonterm2rules[chain[1]]
					for ind in rules_to_transit:
						new_rule = {
							"left": chain[0],
							"right": self.grammar[ind]['right'].copy()
						}
						self.add_rule(new_rule)
			self.remove_rules(to_delete)

	#
	# sentential forms
	#
	def items_to_str(self, items):
		s = ""
		for item in items:
			if item['type'] == Types.nonterminal:
				s += f"[{item['value']}]"
			else:
				if len(item['value']) == 0:
					s += "_eps_"
				else:
					s += item['value']
		return s

	#
	# CHECKERS
	#
	def is_in_weak_GNF(self):
		is_weak_GNF = True
		for rule in self.grammar:
			left = rule['left']
			first_item = rule['right'][0]
			# check first element is terminal
			if first_item['type'] == Types.nonterminal:
				is_weak_GNF = False
				break
			# check eps
			if len(rule['right']) == 1 and first_item['value'] == '' and left != 'S':
				is_weak_GNF = False
				break
			# check S not in right part
			for item in rule['right']:
				if item['type'] == Types.nonterminal and item['value'] == 'S':
					is_weak_GNF = False
					break
			if not is_weak_GNF:
				break
		return is_weak_GNF


	def check_grammar(self):
		left_nterms = set([i['left'] for i in self.grammar])
		assert left_nterms == self.nonterms, f"{self.nonterms.difference(left_nterms)} nonterminals dont have rules"
