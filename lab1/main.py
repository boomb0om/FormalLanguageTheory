import sys
from parser import *
from unification import *
from multiequations import *


def debugprint(*args):
	if DEBUG:
		print(*args)

def parse_input(input_data):
	constructors = input_data[0].replace(' ', '').lstrip('constructors=').split(',')
	constructors = [i[:-1].split('(') for i in constructors]
	constructors = {i[0]:int(i[1]) for i in constructors}
	variables = input_data[1].replace(' ', '')[10:].split(',')
	first_term = input_data[2][12:]
	second_term = input_data[3][13:]

	parser = Parser(variables, list(constructors.keys()))
	parsed_first = parser.parse_term(first_term)
	parsed_second = parser.parse_term(second_term)

	return constructors, variables, parsed_first, parsed_second

def start_multiequation(term1, term2, variables):
	multiequations = [
		MultiEquation(['X_START'], [term1, term2])
	]
	multiequations.extend([
		MultiEquation([v], []) for v in variables
	])
	return MultiEquationSet(multiequations)


if __name__ == '__main__':
	# установка флага для дебага
	if len(sys.argv) == 2 and sys.argv[1] == '--debug':
		DEBUG = True
	else:
		DEBUG = False

	# считываем данные
	input_data = [input() for i in range(4)]

	constructors, variables, parsed_first, parsed_second = parse_input(input_data)

	U = start_multiequation(parsed_first, parsed_second, variables) # изначальная система
	T = MultiEquationSet([]) # финальная система
	i = 0
	while True:
		i += 1
		debugprint('-'*40)
		debugprint('STEP:', i)
		debugprint('System U:')
		debugprint(U)
		ind, me_to_process = U.choose_multieq()
		if ind >= 0:
			U.multiequations.pop(ind)
			#
			common_part = find_common_part(me_to_process.terms)
			debugprint('Common part: ', parsed2str(common_part))
			T.multiequations.append(MultiEquation(me_to_process.vars, [common_part]))
			#
			frontier = find_frontier(me_to_process.terms, common_part)
			frontier_multiequation_set = frontier2MultiEquationSet(frontier, variables)
			debugprint('Frontier:')
			debugprint(frontier_multiequation_set)
			#
			U.extend(frontier_multiequation_set)
			U.compactification()
			debugprint('System U after compactification:')
			debugprint(U)
			debugprint('Result system T:')
			debugprint(T)
		else:
			break
	# последний шаг
	while len(U.multiequations) > 0:
		ind, me_to_process = U.choose_multieq(last_step=True)
		U.multiequations.pop(ind)
		T.multiequations.append(me_to_process)

	print('-'*40)
	print('RESULT:')
	print(T)