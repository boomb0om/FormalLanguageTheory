import copy

from cfg import CFG
from automaton import get_sentential_forms_automaton 
from utils import Types

def get_new_grammar_for_nterm(cfg, nterm):
	sententional_dfa, nterms_to_process = get_sentential_forms_automaton(cfg, nterm, prefix=nterm.lower())
	sententional_dfa.reverse()
	cfg_new = sententional_dfa.to_CFG()
	return cfg_new, sententional_dfa.start_state

def blum_koh(cfg, debug):
	automatons_data = []

	sententional_dfa, nterms_to_process = get_sentential_forms_automaton(cfg, "S", prefix="s")
	sententional_dfa.reverse()
	automatons_data.append(("S", sententional_dfa))
	cfg_new = sententional_dfa.to_CFG()
	nterms_to_rename = [("S", sententional_dfa.start_state)]
	
	for nterm in nterms_to_process:
		sententional_dfa, _ = get_sentential_forms_automaton(cfg, nterm, prefix=nterm.lower())
		sententional_dfa.reverse()
		automatons_data.append((nterm, sententional_dfa))
		sent_cfg_for_nterm = sententional_dfa.to_CFG()
		cfg_new.union(sent_cfg_for_nterm)
		nterms_to_rename.append((nterm, sententional_dfa.start_state))

	for (nterm, nterm_new) in nterms_to_rename:
		cfg_new.nonterms.add(nterm)
		cfg_new.rename_nonterminal(nterm, nterm_new)

	if debug:
		print("Грамматика после Блюма-Коха и перед раскрытием нетерминалов:")
		cfg_new.print(border_bottom=True)

	nterms = list(cfg_new.nonterms)
	for i in range(len(nterms)):
		ai = nterms[i]
		to_delete = []
		nonterm2rules = cfg_new.get_nonterm_to_rule()

		for j in range(len(nterms)):
			if i == j:
				continue
			aj = nterms[j]
			for rule_ind in nonterm2rules[ai]:
				rule = cfg_new.grammar[rule_ind]
				first_elem = rule['right'][0]
				if first_elem['type'] == Types.nonterminal and first_elem['value'] == aj:
					cfg_new._transit_rule_gnf(rule_ind, nonterm2rules)
					to_delete.append(rule_ind)
		cfg_new.remove_rules(to_delete)

	cfg_new.rename_nonterminal(nterms_to_rename[0][1], "S")
	return cfg_new, automatons_data