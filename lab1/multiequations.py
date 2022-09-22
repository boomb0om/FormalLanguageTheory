from parser import parsed2str

### обходит дерево и возвращает имена всех переменных
def get_term_vars(tree):
	stack = [tree]
	var_names = set()

	while len(stack) > 0:
		t = stack.pop()
		if t['type'] == 'var':
			var_names.add(t['name'])
		else:
			for i in range(len(t['args'])):
				stack.append(t['args'][i])
	return var_names


# класс для одного мультиуравнения
class MultiEquation:
	def __init__(self, vars, terms):
		# move variables from terms to vars
		indexes_to_drop = []
		for c, t in enumerate(terms):
			if t['type'] == 'var':
				indexes_to_drop.append(c)
				vars.append(t['name'])
		for i in indexes_to_drop[::-1]:
			terms.pop(i)
		
		self.vars_set = set(vars)
		self.vars = list(self.vars_set)

		self.terms = terms
		self.terms_strs = [parsed2str(term) for term in self.terms]
		self.terms_strs_set = set(self.terms_strs)

	def drop_duplicated(self):
		self.vars = list(self.vars_set)

		count = {v: 0 for v in self.terms_strs_set}
		ids_to_drop = []
		for c, v in enumerate(self.terms_strs):
			count[v] += 1
			if count[v] > 1:
				ids_to_drop.append(c)

		for i in ids_to_drop[::-1]:
			self.terms_strs.pop(i)
			self.terms.pop(i)

	def get_right_part_vars(self):
		all_vars = set()
		for t in self.terms:
			all_vars.update(get_term_vars(t))
		return all_vars

	def __eq__(self, other):
		return self.vars_set == other.vars_set and self.terms_strs_set == other.terms_strs_set

	def __str__(self):
		terms_str = "{"+', '.join(self.terms_strs)+"}"
		return "{"+', '.join(self.vars)+"}" + " = " + terms_str


# класс для набора мультиуравнений
class MultiEquationSet:
	def __init__(self, multiequations):
		self.multiequations = multiequations

	def extend(self, new_multiequation_set):
		self.multiequations.extend(new_multiequation_set.multiequations)

	def choose_multieq(self, last_step=False):
		multieqs_to_check = []
		right_part_vars = []
		for me in self.multiequations:
			if len(me.terms) > 1:
				multieqs_to_check.append(me) 
			right_part_vars.append(me.get_right_part_vars())

		if last_step and len(multieqs_to_check) > 0:
			raise Exception("Cant choose multiequation. Unification error")
		if last_step:
			multieqs_to_check = self.multiequations

		# нет мультиуравнений у которых >= 2 термов справа
		if len(multieqs_to_check) == 0:
			return -1, None

		for i in range(len(multieqs_to_check)):
			is_ok = True
			for me_right_vars in right_part_vars:
				if len(me_right_vars.intersection(multieqs_to_check[i].vars_set)) > 0:
					is_ok = False
					break
			if is_ok:
				break

		# нет мультиуравнения у которого ни одна переменная левой части 
		# не встречается в правой части никакого уравнения вообще
		if not is_ok:
			raise Exception("Cant choose multiequation. Unification error")

		result_multieq = multieqs_to_check[i]
		for i in range(len(self.multiequations)):
			if result_multieq == self.multiequations[i]:
				break

		return i, result_multieq

	def compactification(self):
		# делаем объединение мультиуравнений по переменным
		# (по левой части)

		vars_clusters = [self.multiequations[0].vars_set]
		for c, me in enumerate(self.multiequations):
			for v in me.vars:
				is_in_any_cluster = False
				for cluster in vars_clusters:
					if v in cluster:
						is_in_any_cluster = True
						cluster.update(me.vars_set)
						break
				if not is_in_any_cluster:
					vars_clusters.append(me.vars_set)

		c = 0
		while True:
			next_iter = False
			to_merge = (0, 0)
			for i in range(len(vars_clusters)):
				cluster1 = vars_clusters[i]
				for j in range(i+1, len(vars_clusters)):
					cluster2 = vars_clusters[j]
					if len(cluster1.intersection(cluster2)) > 0:
						next_iter = True
						to_merge = (i, j)
						break
				if next_iter:
					break

			if next_iter and not (to_merge[0] == 0 and to_merge[1] == 0):
				vars_clusters[i].update(vars_clusters[to_merge[1]])
				vars_clusters.pop(to_merge[1])
			else:
				break
			c += 1

		multieqs_to_merge = [[] for _ in range(len(vars_clusters))]
		for c, cluster in enumerate(vars_clusters):
			for me in self.multiequations:
				if len(me.vars_set.intersection(cluster)) > 0:
					multieqs_to_merge[c].append(me)

		new_multiequations = []
		for multieqs in multieqs_to_merge:
			vars = []
			terms = []
			for me in multieqs:
				vars.extend(me.vars)
				terms.extend(me.terms)
			multieq = MultiEquation(vars, terms)
			multieq.drop_duplicated()
			new_multiequations.append(multieq)
		self.multiequations = new_multiequations

	def __str__(self):
		return "\n".join([str(me) for me in self.multiequations])