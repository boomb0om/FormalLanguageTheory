from parser import parsed2str
from multiequations import MultiEquation, MultiEquationSet

### общая часть мультиуравнения
def find_common_part(trees):
	is_first = True
	first_constr_name = ''
	args_for_common_part = None
	for tree in trees:
		if tree['type'] == 'var':
			return {'type': 'var', 'name': tree['name']}
		elif tree['type'] == 'constr' and is_first:
			is_first = False
			first_constr_name = tree['name']
			args_for_common_part = [[] for i in range(len(tree['args']))]
		elif tree['type'] == 'constr' and not is_first and tree['name'] != first_constr_name:
			raise Exception(
				f"Unification error: name of constr {tree['name']} != name of constr {first_constr_name}"
			)
		
		if tree['type'] == 'constr':
			if len(tree['args']) != len(args_for_common_part):
				Exception(f"Unification error: args of {tree['name']} != args of {first_constr_name}")
			for i in range(len(tree['args'])):
				args_for_common_part[i].append(tree['args'][i])

	new_args = []
	for i in range(len(args_for_common_part)):
		new_args.append(find_common_part(args_for_common_part[i]))
	return {'type': 'constr', 'name': first_constr_name, 'args': new_args}


# удобное добавление элемента в словарь с массивами
def add_item_to_dict(d, key, value):
	if key not in d.keys():
		d[key] = [value]
	else:
		d[key].append(value)

# составление границы
def find_frontier(all_trees, common_part):
	stack = [(all_trees, common_part)]
	frontier = {}
	used_names = {}

	while len(stack) > 0:
		trees, common = stack.pop()

		for tree in trees:
			if common['type'] == 'var' and tree['type'] == 'var':
				if tree['name'] not in used_names.get(common['name'], []) and tree['name'] != common['name']:
					add_item_to_dict(frontier, common['name'], tree)
					add_item_to_dict(used_names, common['name'], tree['name'])
			elif common['type'] == 'var' and tree['type'] == 'constr':
				tree_str = parsed2str(tree)
				if tree_str not in used_names.get(common['name'], []):
					add_item_to_dict(frontier, common['name'], tree)
					add_item_to_dict(used_names, common['name'], tree_str)

			if common['type'] == 'constr':
				args_for_frontier_part = [[] for i in range(len(common['args']))]
				for i in range(len(args_for_frontier_part)):
					args_for_frontier_part[i].append(tree['args'][i])

				for i in range(len(args_for_frontier_part)):
					stack.append((args_for_frontier_part[i], common['args'][i]))

	return frontier


def frontier2MultiEquationSet(frontier, all_var_names):
	mes = []

	for k, v in frontier.items():
		vars = [k]
		terms = []
		for t in v:
			# если это переменная
			if t['type'] == 'var' and t['name'] in all_var_names:
				vars.append(t['name'])
			else:
				terms.append(t)
		mes.append(MultiEquation(vars, terms))

	return MultiEquationSet(mes)