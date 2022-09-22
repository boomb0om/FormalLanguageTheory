import re

class Parser:
	# {"type": "var", name: "x"}
	# {"type": "constr", "name": "f", args: [...]}

	def __init__(self, var_names, constr_names):
		self.var_names = var_names
		self.constr_names = constr_names

	def parse_term(self, s):
		if self.is_var(s):
			return self.parse_var(s)
		elif self.is_constr(s):
			return self.parse_constr(s)
		else:
			raise ValueError(f"Unknown term: {s}")

	def is_var(self, s):
		return re.fullmatch('[a-zA-Z]+', s) and s in self.var_names

	def is_constr(self, s):
		if re.fullmatch('[a-zA-Z]+', s) and s in self.constr_names:
			# 0-местный конструктор
			return True
		elif re.fullmatch('[a-zA-Z]+\(.*\)', s) and s.split('(')[0] in self.constr_names:
			num_brackets = 0
			passed_first_bracket = False
			first_bracket_index = 0
			arg_ended = False
			for i in range(len(s)):
				# check args correctness
				if passed_first_bracket and arg_ended:
					arg_ended = False
					if s[i] != ',' and i != first_bracket_index+1 and i != len(s)-1:
						raise ValueError("Bad constructor args")
				# check brackets
				if s[i] == '(':
					if not passed_first_bracket:
						first_bracket_index = i
					passed_first_bracket = True
					num_brackets += 1
				elif s[i] == ')':
					num_brackets -= 1
					if num_brackets == 1:
						arg_ended = True
			if num_brackets == 0:
				return True
		return False

	def parse_var(self, s):
		return {"type": "var", "name": s}

	def parse_constr(self, s):
		first_bracket_index = s.find('(')

		if first_bracket_index == -1: 
			# 0-местный конструктор
			parsed_constr = {"type": "constr", "name": s, "args": []}
		else:
			constr_name = s[:first_bracket_index]
			constr_args_s = s[first_bracket_index+1:-1]

			# parse args
			num_brackets = 0
			constr_args = []
			arg_start_index = 0
			for i in range(len(constr_args_s)):
				if constr_args_s[i] == '(':
					num_brackets += 1
				elif constr_args_s[i] == ')':
					num_brackets -= 1
				if num_brackets == 0 and constr_args_s[i] == ',':
					constr_args.append(constr_args_s[arg_start_index:i])
					arg_start_index = i+1
			if len(constr_args_s)>0:
				constr_args.append(constr_args_s[arg_start_index:]) # last arg

			parsed_constr = {"type": "constr", "name": constr_name, "args": []}
			for arg in constr_args:
				parsed_constr['args'].append(self.parse_term(arg))

		return parsed_constr


### распаршенная структура -> строка
def parsed2str(tree):
	if tree['type'] == 'var':
		return tree['name']
	elif tree['type'] == 'constr' and len(tree['args']) == 0: # 0-местный конструктор
		return tree['name']
	else:
		args_strs = []
		for i in range(len(tree['args'])):
			args_strs.append(parsed2str(tree['args'][i]))
		result = f"{tree['name']}("+', '.join(args_strs)+')'
		return result