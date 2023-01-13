import sys
from parser import *
from unification import *
from multiequations import *
from parser import parsed2str


def debugprint(*args):
    if DEBUG:
        print(*args)


def parse_input(input_data):
    input_data = ''.join(input_data)
    input_data = input_data.replace(' ', '').replace('\n', '').replace('\r', '')
    input_data = input_data[13:]
    i = input_data.index("variables")
    constructors = input_data[0:i].split(',')
    constructors = [i[:-1].split('(') for i in constructors]
    constructors = {i[0]: int(i[1]) for i in constructors}
    j = input_data.index("Firstterm")
    varstring = input_data[i:j]
    variables = varstring[10:j].split(',')
    k = input_data.index("Secondterm")
    first_term = input_data[j + 10:k]
    second_term = input_data[k + 11:]

    parser = Parser(variables, constructors)
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


def replace(result, T):
    if result['type'] == 'var':
        for multieq in T.multiequations[1:]:
            if result['name'] in multieq.vars:
                if multieq.terms:
                    replacement = multieq.terms[0]
                    #print(f"replacing {result['name']} with {replacement['name']}")
                    if replacement['type'] == 'constr':
                        for c in range(len(replacement['args'])):
                            replacement['args'][c] = replace(replacement['args'][c], T)
                    return replacement
                else:  # если правая часть пустая
                    replacer_index = -1
                    for i in range(len(multieq.vars)):
                        replacer_index = i
                        good_replacer = True
                        for meq in T.multiequations[1:]:
                            if meq != multieq and multieq.vars[i] in meq.vars:
                                good_replacer = False
                        if not good_replacer:
                            replacer_index = -1
                        else:
                            break
                    if replacer_index == -1: replacer_index = 0
                    replacement = {"type": "var", "name": multieq.vars[replacer_index]}
                    #print(f"replacing <empty right meq part> {result['name']} with {replacement['name']}")
                    return replacement
    elif result['type'] == 'constr':
        for c in range(len(result['args'])):
            result['args'][c] = replace(result['args'][c], T)
    return result


if __name__ == '__main__':
    # установка флага для дебага
    if len(sys.argv) == 2 and sys.argv[1] == '--debug':
        DEBUG = True
    else:
        DEBUG = False

    # считываем данные
    input_data = sys.stdin.readlines()

    constructors, variables, parsed_first, parsed_second = parse_input(input_data)

    U = start_multiequation(parsed_first, parsed_second, variables)  # изначальная система
    T = MultiEquationSet([])  # финальная система
    i = 0
    while True:
        i += 1
        debugprint('-' * 40)
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

    print('-' * 40)
    print('RESULT:')
    print(T)

    X_START = T.multiequations[0]
    result = X_START.terms[0]
    #result = replace(result, T)
    #result = parsed2str(result)
    #final = f"FINAL = {result}"
    #print(final)