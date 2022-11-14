import re
import sys
import time

from parsing import Parser
from automaton import get_sentential_forms_automaton 
from blum_koh import blum_koh

import argparse

parser = argparse.ArgumentParser(description='Converter to GNF')
parser.add_argument('--blum-coh', action='store_true', help='Использовать алгоритм Блюма-Коха')
parser.add_argument('--graphs', action='store_true', help='Сохранять графы автоматов')
parser.add_argument('--debug', action='store_true', help='Выводить промежуточную информацию')


def read_grammar():
	lines = []
	while True:
		try:
			lines.append(input())
		except EOFError:
			break

	lines = [
		i.replace(' ','').replace('\t','').replace('\r','') 
		for i in lines
	]
	lines = [i for i in lines if len(i)>0]
	return lines


if __name__ == "__main__":
	args = parser.parse_args()
	debug = args.debug

	input_lines = read_grammar()
	parser = Parser()
	cfg = parser.parse_grammar(input_lines)
	print('Входная грамматика:')
	cfg.print()
	in_gnf = cfg.is_in_weak_GNF()
	print("Грамматика в нормальной форме Грейбах?", in_gnf)
	if in_gnf:
		print("Грамматика уже в нормальной форме Грейбах. Упрощение не требуется")
		exit()

	t1 = time.time()

	cfg.remove_unreachable_rules()

	if not args.blum_coh:
		print("Привожу грамматику в ГНФ через удаление левой рекурсии...")

		cfg.remove_start_nonterminal()
		if debug:
			print("Грамматика после удаления стартового нетерминала из правых частей:")
			cfg.print(border_bottom=True)

		cfg.remove_chain_rules()
		if debug:
			print("Грамматика после удаления цепных правил:")
			cfg.print(border_bottom=True)

		nterm2index = cfg.to_GNF(debug)

		t_done = time.time()-t1
		# я не включаю удаление дубликатов и недостижимых нетерминалов в подсчет времени
		# так как грамматика уже находится в ГНФ и по-сути задача выполнена, а
		# это просто упростит вид грамматики
		cfg.remove_unreachable_rules()
		if debug:
			print("Удалены недостижимые правила")
		cfg.remove_duplicated_rules()
		if debug:
			print("Удалены дублирующиеся правила")

		print("Финальная грамматика в ГНФ (удалены недостижимые правила):")
		cfg.print(border_bottom=True)
		print("Грамматика в нормальной форме Грейбах?", cfg.is_in_weak_GNF())
		print(f"Выполнено за {t_done} секунд")

		cfg.update_terms_and_nonterms()
		nterms_ordered = [(k,v) for k,v in nterm2index.items() if k in cfg.nonterms]
		nterms_ordered = sorted(nterms_ordered, key=lambda x: x[1])
		print('Частичные порядок (нетерминал, индекс):')
		print(nterms_ordered)
	else:
		print("Привожу грамматику в ГНФ с помощью алгоритма Блюма-Коха...")

		cfg.remove_epsilon()
		if debug:
			print("Грамматика после удаления эпсилон правил:")
			cfg.print(border_bottom=True)

		cfg.remove_chain_rules()
		if debug:
			print("Грамматика после удаления цепных правил:")
			cfg.print(border_bottom=True)

		# Блюм-Кох
		cfg, automatons_data = blum_koh(cfg, debug)

		cfg.remove_start_nonterminal()
		if debug:
			print("Стартовый нетерминал удален из правых частей")

		t_done = time.time()-t1
		# я не включаю удаление дубликатов и недостижимых нетерминалов в подсчет времени
		# так как грамматика уже находится в ГНФ и по-сути задача выполнена, а
		# это просто упростит вид грамматики
		cfg.remove_unreachable_rules()
		if debug:
			print("Удалены недостижимые правила")
		cfg.remove_duplicated_rules()
		if debug:
			print("Удалены дублирующиеся правила")
		
		print("Финальная грамматика в ГНФ (удалены недостижимые правила):")
		cfg.print(border_bottom=True)
		print("Грамматика в нормальной форме Грейбах?", cfg.is_in_weak_GNF())
		print(f"Выполнено за {t_done} секунд")

		if args.graphs:
			for data in automatons_data:
				filename = data[1].export_as_graph(f"sententional_forms_{data[0]}")
				print(f"Автомат для нетерминала: [{data[0]}] сохранен в {filename}")
		else:
			print()
			print("Автоматы сентенциальных форм:")
			for data in automatons_data:
				print("Автомат для нетерминала:", f"[{data[0]}]")
				data[1].print()
				print('-'*40)
