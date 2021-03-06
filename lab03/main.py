import random
import numpy
import math
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from itertools import combinations
from scipy import stats

def increment(elem):
	elem += 1
	return elem

def get_value(x_min, x_max, prop):
	return (prop + 1) / 2 * (x_max - x_min) + x_min

class Generator:
	def __init__(self, sigma):
		assert(sigma >= 0)
		self.scale = sigma

	def generate_time(self):
		nparray = numpy.random.rayleigh(self.scale, 1)
		return nparray[0]

class Operator:
	def __init__(self, a, b):
		assert(a >= 0 and b >= 0 and a < b)
		self.busy = False
		self.low = a
		self.high = b

	def generate_time(self):
		return random.uniform(self.low, self.high)

class System:
	def __init__(self, start_time = 0, end_time = 20):
		assert(start_time >= 0 and end_time >= 0 and end_time > start_time)
		self.start_time = start_time
		self.end_time = end_time

		self.queue_length = 0
		self.max_queue_length = 0
		self.generated = 0
		self.processed = 0
		self.avg_waiting_time = 0
		self.started_processing = 0
		self.max_waiting_time = 0
		self.events = list()

	def set_generators_by_params(self, generators_conf_array = [4]):
		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = [Generator(generators_conf_array[i]) for i in range (self.generators_number)]

	def set_generators_by_intensity(self, generators_conf_array = [2]):
		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = []
		for i in range (self.generators_number):
			sigma = 1/generators_conf_array[i] * math.sqrt(2 / math.pi)
			self.generators.append(Generator(sigma))

	def set_operators_by_params(self, operators_conf_array = [[0, 2]]):
		self.operators_number = len(operators_conf_array)
		self.operators = [Operator(operators_conf_array[i][0], operators_conf_array[i][1]) for i in range(self.operators_number)]

	def set_operators_by_intensity_and_dispersion(self, operators_conf_array = [[5, 0.3]]):
		self.operators_number = len(operators_conf_array)
		self.operators = []
		for i in range (self.operators_number):
			a = 1/operators_conf_array[i][0] - operators_conf_array[i][1] * math.sqrt(3)
			b = 1/operators_conf_array[i][0] + operators_conf_array[i][1] * math.sqrt(3)
			assert(a >= 0 and b >= 0 and a < b)
			self.operators.append(Operator(a, b))

	def reset(self):
		self.queue_length = 0
		self.max_queue_length = 0
		self.generated = 0
		self.processed = 0
		self.avg_waiting_time = 0
		self.started_processing = 0
		self.max_waiting_time = 0
		self.events = list()
		for op in self.operators:
			op.busy = False

	def add_event(self, event: list):
		i = 0
		while i < len(self.events) and self.events[i][0] <= event[0]:
			i += 1
		self.events.insert(i, event)

	def modeling(self):
		for i in range(self.generators_number):
			self.add_event([self.start_time, 'client', i, 0])
			self.generated += 1
			self.queue_length += 1
			if (self.queue_length > self.max_queue_length):
				self.max_queue_length = self.queue_length
		cur_time = self.start_time
		while cur_time < self.end_time:
			event = self.events.pop(0)
			cur_time = event[0]
			if event[1] == 'client':
				self.start_operate(event)
			else: # if event[1] == 'operator':
				self.finish_operate(event)
		self.avg_waiting_time /= self.started_processing

	def start_operate(self, event):
		i = 0
		while i < self.operators_number and self.operators[i].busy:
			i += 1
		if i != self.operators_number:
			self.queue_length -= 1
			self.operators[i].busy = True
			self.add_event([event[0] + self.operators[i].generate_time(), 'operator', i])
			self.started_processing += 1
			self.avg_waiting_time += event[3]
			if (event[3] > self.max_waiting_time):
				self.max_waiting_time = event[3]
		else:
			j = 0
			while j < len(self.events) and self.events[j][1] != 'operator':
				j += 1
			self.add_event([self.events[j][0], 'client', event[2], event[3] + self.events[j][0] - event[0]])
		if (event[3] == 0):
			self.add_event([event[0] + self.generators[event[2]].generate_time(), 'client', event[2], 0])
			self.generated += 1
			self.queue_length += 1
			if (self.queue_length > self.max_queue_length):
				self.max_queue_length = self.queue_length

	def finish_operate(self, event):
		self.operators[event[2]].busy = False
		self.processed += 1

	def getStat(self, times):
		waiting_time_arr = []
		for i in range(times):
			self.modeling()
			waiting_time_arr.append(self.avg_waiting_time)
			self.reset()
		return waiting_time_arr

class PFE:
	# [[m1_min, m1_max], [m2_min, m2_max], [sigma2_min, sigma2_max]]
	def __init__ (self, min_max_factors, times):
		self.factors = min_max_factors
		self.number_of_factors = len(min_max_factors)
		self.number_of_experiments = 2 ** self.number_of_factors
		self.create_real_table(min_max_factors)
		self.create_plan_table()
		self.times = times
		self.experiment_data_filled = False
		self.calculated_data_filled = False

	def create_real_table(self, min_max_factors):
		self.real_table = []
		for experiment in range (self.number_of_experiments):
			tablerow = []
			for factor in range (self.number_of_factors):
				if (experiment & (1 << factor)):
					tablerow.append(min_max_factors[factor][0])
				else:
					tablerow.append(min_max_factors[factor][1])
			self.real_table.append(tablerow)

	def create_plan_table(self):
		self.plan_table = []
		for experiment in range (self.number_of_experiments):
			tablerow = []
			for factor in range (self.number_of_factors):
				if (experiment & (1 << factor)):
					tablerow.append(-1)
				else:
					tablerow.append(1)
			self.plan_table.append(tablerow)
		self.print_plan_table()

	def print_plan_table(self):
		pt = PrettyTable()
		field_names = ['#']
		for factor in range (self.number_of_factors + 1):
			field_names.append('x' + str(factor))

		pt.field_names = field_names
		i = 1
		for row in self.plan_table:
			insertrow = row.copy()
			insertrow.insert(0, i)
			insertrow.insert(1, str(1))
			pt.add_row(insertrow)
			i += 1
		print(pt)

	def fill_experiment_data(self):
		self.experiment_data_filled = True
		model = System(0, 20)
		sumdisppersion = 0
		maxdispersion = 0
		for experiment in range (self.number_of_experiments):
			model.set_generators_by_intensity([self.real_table[experiment][0], self.real_table[experiment][3]])
			model.set_operators_by_intensity_and_dispersion([[self.real_table[experiment][1], self.real_table[experiment][2]]])
			y_ex_values = model.getStat(self.times)
			y_ex_avg = sum(y_ex_values) / len (y_ex_values)
			self.real_table[experiment].append(y_ex_avg)
			y_dispersion = sum([(y_ex_avg - y_ex_value)**2 / self.times for y_ex_value in y_ex_values])
			self.real_table[experiment].append(y_dispersion)
			if (y_dispersion > maxdispersion):
				maxdispersion = y_dispersion
			sumdisppersion += y_dispersion

		Gp = maxdispersion / sumdisppersion
		print("Критерий Кохрена: ", Gp)
		self.S = sumdisppersion / self.number_of_experiments
		print("дисперсии воспроизводимости ", self.S)
		self.Sak = (self.S / self.number_of_experiments / self.times) ** 0.5
		print("среднее квадратическое отклонение коэффициента", self.Sak)
		self.student_table = stats.t(df=(self.number_of_experiments * (self.times - 1))).ppf(0.95) #1.998
		self.meaningful_koefs = 0

	def calculate_koefs(self):
		self.koefs = []
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments) #a0
		koef_meaning = abs(self.koefs[0])/self.Sak
		print("Критерий Стьюдента: ", self.student_table)
		if (koef_meaning >= self.student_table):
			ending = "\t✓\n"
			self.meaningful_koefs += 1
		else:
			ending = "\n"
		print ("a 0\t", round(self.koefs[0], 7), "\t", round(koef_meaning, 7), end = ending)
		if (koef_meaning < self.student_table):
			self.koefs[0] = 0

		factor_indexes = []
		for i in range (self.number_of_factors):
			factor_indexes.append(i)
		for i in range (1, self.number_of_factors + 1):
			for j in combinations(factor_indexes, i):
				koef_value = 0
				for experiment in range(self.number_of_experiments):
					mult = 1
					for k in range(i):
						mult *= self.plan_table[experiment][j[k]]
					koef_value += mult * self.real_table[experiment][self.number_of_factors]
				koef_value /= self.number_of_experiments
				koef_meaning = abs(koef_value)/self.Sak
				if (koef_meaning >= self.student_table):
					ending = "\t✓\n"
					self.meaningful_koefs += 1
				else:
					ending = "\n"
				print ("a", "".join(map(str,map(increment, j))), "\t", round(koef_value, 7), "\t", round(koef_meaning, 7), end=ending)
				if (koef_meaning < self.student_table):
					koef_value = 0
				self.koefs.append(koef_value)

	def calculate_partly_nonlinear(self, factors):
		result = self.koefs[0]

		koef_index = 1
		for i in range (1, len(factors) + 1):
			for j in combinations(factors, i):
				mult = 1
				for k in range(i):
					mult *= j[k]
				result += mult * self.koefs[koef_index]
				koef_index += 1
		return result

	def calculate_linear(self, factors):
		result = self.koefs[0]
		for i in range (self.number_of_factors):
			result += self.koefs[i + 1] * factors[i]
		return result

	def fill_calculated_data(self):
		self.calculate_koefs()
		self.calculated_data_filled = True
		for experiment in range (self.number_of_experiments):
			y_cal_value_non = self.calculate_partly_nonlinear(self.plan_table[experiment])
			y_cal_value = self.calculate_linear(self.plan_table[experiment])
			self.real_table[experiment].append(y_cal_value)
			self.real_table[experiment].append(y_cal_value_non)
			y_ex_value = self.real_table[experiment][self.number_of_factors]
			self.real_table[experiment].append(y_ex_value - y_cal_value)
			self.real_table[experiment].append(y_ex_value - y_cal_value_non)

	def check_adequacy(self):
		print("дисперсии воспроизводимости ", self.S)
		diffsqsum = 0
		for row in self.real_table:
			diffsqsum += row[self.number_of_factors + 5]**2
		self.Ss = self.times / (self.number_of_experiments - self.meaningful_koefs) * diffsqsum
		print("дисперсия адекватности: ", self.Ss)
		self.F = self.Ss / self.S
		print("Критерий Фишера (ад / вос): ", self.F)
		if (self.F < 1):
			q1 = self.number_of_experiments - self.meaningful_koefs
			q2 = self.number_of_experiments
		else:
			q1 = self.number_of_experiments
			q2 = self.number_of_experiments - self.meaningful_koefs
		print("q1 ",q1, " q2 ", q2)

	def printtable(self):
		if (self.experiment_data_filled):
			pt = PrettyTable()
			field_names = ['#']
			for factor in range (self.number_of_factors):
				field_names.append('x' + str(factor + 1))
			field_names.append('y среднее из ' + str(self.times) + ' опытов')
			field_names.append('дисперсия y')

		if (self.calculated_data_filled):
			field_names.append('линейное')
			field_names.append('частично нелинейное')
			field_names.append('разница (линейное)')
			field_names.append('разница (частично нелинейное)')

		pt.field_names = field_names
		i = 1
		for row in self.real_table:
			insertrow = row.copy()
			insertrow.insert(0, i)
			pt.add_row(insertrow)
			i += 1
		print(pt)

class DFE:
	def __init__ (self, min_max_factors, times, p):
		self.factors = min_max_factors
		self.number_of_factors = len(min_max_factors)
		self.p = p
		self.number_of_experiments = 2 ** (self.number_of_factors - self.p)
		self.create_plan_table()
		self.create_real_table(min_max_factors)
		self.times = times
		self.experiment_data_filled = False
		self.calculated_data_filled = False

	def create_real_table(self, min_max_factors):
		self.real_table = []
		for experiment in range (self.number_of_experiments):
			tablerow = []
			for factor in range (self.number_of_factors):
				if (self.plan_table[experiment][factor] == 1):
					tablerow.append(min_max_factors[factor][1])
				else:
					tablerow.append(min_max_factors[factor][0])
			self.real_table.append(tablerow)

	def create_plan_table(self):
		self.plan_table = []
		for experiment in range (self.number_of_experiments):
			tablerow = []
			for factor in range (self.number_of_factors):
				if factor == 3:
					tablerow.append(tablerow[0] * tablerow[1]) #x4 = x1 * x2
				else:
					if (experiment & (1 << factor)):
						tablerow.append(-1)
					else:
						tablerow.append(1)
			self.plan_table.append(tablerow)
		self.print_plan_table()

	def print_plan_table(self):
		pt = PrettyTable()
		field_names = ['#']
		for factor in range (self.number_of_factors + 1):
			field_names.append('x' + str(factor))

		pt.field_names = field_names
		i = 1
		for row in self.plan_table:
			insertrow = row.copy()
			insertrow.insert(0, i)
			insertrow.insert(1, str(1))
			pt.add_row(insertrow)
			i += 1
		print(pt)

	def fill_experiment_data(self):
		self.experiment_data_filled = True
		model = System(0, 20)
		sumdisppersion = 0
		maxdispersion = 0
		for experiment in range (self.number_of_experiments):
			model.set_generators_by_intensity([self.real_table[experiment][0], self.real_table[experiment][3]])
			model.set_operators_by_intensity_and_dispersion([[self.real_table[experiment][1], self.real_table[experiment][2]]])
			y_ex_values = model.getStat(self.times)
			y_ex_avg = sum(y_ex_values) / len (y_ex_values)
			self.real_table[experiment].append(y_ex_avg)
			y_dispersion = sum([(y_ex_avg - y_ex_value)**2 / self.times for y_ex_value in y_ex_values])
			self.real_table[experiment].append(y_dispersion)
			if (y_dispersion > maxdispersion):
				maxdispersion = y_dispersion
			sumdisppersion += y_dispersion

		Gp = maxdispersion / sumdisppersion
		print("Критерий Кохрена: ", Gp)
		self.S = sumdisppersion / self.number_of_experiments
		print("дисперсии воспроизводимости ", self.S)
		self.Sak = (self.S / self.number_of_experiments / self.times) ** 0.5
		print("среднее квадратическое отклонение коэффициента", self.Sak)
		self.student_table = stats.t(df=(self.number_of_experiments * (self.times - 1))).ppf(0.95) #1.998
		self.meaningful_koefs = 0

	def calculate_koefs(self):
		self.koefs = []
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments) #a0

		#ai
		for factorindex in range(self.number_of_factors):
			y_ex_avg_sum = 0
			for experiment in range(self.number_of_experiments):
				y_ex_avg_sum += self.plan_table[experiment][factorindex] * self.real_table[experiment][self.number_of_factors]
			self.koefs.append(y_ex_avg_sum / self.number_of_experiments)

		#a13
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.plan_table[experiment][0] * self.plan_table[experiment][2] * self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments)
		#a23
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.plan_table[experiment][1] * self.plan_table[experiment][2] * self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments)
		#a34
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.plan_table[experiment][2] * self.plan_table[experiment][3] * self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments)

		print("Критерий Стьюдента: ", self.student_table)
		lables = ["a0*\t", "a1*\t", "a2*\t", "a3*\t", "a4*\t", "a13*\t", "a23*\t", "a34*\t"]
		for koefindex in range(len(self.koefs)):
			koef_meaning = abs(self.koefs[koefindex])/self.Sak
			if (koef_meaning >= self.student_table):
				ending = "\t✓\n"
				self.meaningful_koefs += 1
			else:
				ending = "\n"
			print (lables[koefindex], round(self.koefs[koefindex], 7), "\t", round(koef_meaning, 7), end = ending)
			if (koef_meaning < self.student_table):
				self.koefs[koefindex] = 0

		self.allkoefs = [self.koefs[0], self.koefs[1], self.koefs[2], self.koefs[3], self.koefs[4], 0, self.koefs[5]/2, 0, self.koefs[6]/2, 0, self.koefs[7]/2, self.koefs[7]/2, 0, self.koefs[6]/2, self.koefs[5]/2, 0]

		factor_indexes = [i for i in range (self.number_of_factors)]
		index = 1
		print()
		print ("a 0", "\t", self.allkoefs[0])
		for i in range (1, self.number_of_factors + 1):
			for j in combinations(factor_indexes, i):
				print ("a", "".join(map(str,map(increment, j))), "\t", self.allkoefs[index])
				index += 1

	def calculate_partly_nonlinear(self, factors):
		result = self.allkoefs[0]
		koef_index = 1
		for i in range (1, len(factors) + 1):
			for j in combinations(factors, i):
				mult = 1
				for k in range(i):
					mult *= j[k]
				result += mult * self.allkoefs[koef_index]
				koef_index += 1
		return result


		# result = self.koefs[0]
		# for i in range (len(factors)):
		# 	result += self.koefs[i + 1] * factors[i]


		# result += self.koefs[self.number_of_factors] * factors[0] * factors[2] + self.koefs[self.number_of_factors+1] * factors[1] * factors[2] + self.koefs[self.number_of_factors+2]*factors[2]*factors[3]
		# return result

	def calculate_linear(self, factors):
		result = self.koefs[0]
		for i in range (len(factors)):
			result += self.koefs[i + 1] * factors[i]
		return result

	def fill_calculated_data(self):
		self.calculate_koefs()
		self.calculated_data_filled = True
		for experiment in range (self.number_of_experiments):
			y_cal_value_non = self.calculate_partly_nonlinear(self.plan_table[experiment])
			y_cal_value = self.calculate_linear(self.plan_table[experiment])
			self.real_table[experiment].append(y_cal_value)
			self.real_table[experiment].append(y_cal_value_non)
			y_ex_value = self.real_table[experiment][self.number_of_factors]
			self.real_table[experiment].append(y_ex_value - y_cal_value)
			self.real_table[experiment].append(y_ex_value - y_cal_value_non)

	def check_adequacy(self):
		print("дисперсии воспроизводимости ", self.S)
		diffsqsum = 0
		for row in self.real_table:
			diffsqsum += row[self.number_of_factors + 5]**2
		self.Ss = self.times / (self.number_of_experiments - self.meaningful_koefs) * diffsqsum
		print("дисперсия адекватности: ", self.Ss)
		self.F = self.Ss / self.S
		print("Критерий Фишера (ад / вос): ", self.F)
		if (self.F < 1):
			q1 = self.number_of_experiments - self.meaningful_koefs
			q2 = self.number_of_experiments
		else:
			q1 = self.number_of_experiments
			q2 = self.number_of_experiments - self.meaningful_koefs
		print("q1 ",q1, " q2 ", q2)

	def printtable(self):
		if (self.experiment_data_filled):
			pt = PrettyTable()
			field_names = ['#']
			for factor in range (self.number_of_factors):
				field_names.append('x' + str(factor + 1))
			field_names.append('y среднее из ' + str(self.times) + ' опытов')
			field_names.append('дисперсия y')

		if (self.calculated_data_filled):
			field_names.append('линейное')
			field_names.append('частично нелинейное')
			field_names.append('разница (линейное)')
			field_names.append('разница (частично нелинейное)')

		pt.field_names = field_names
		i = 1
		for row in self.real_table:
			insertrow = row.copy()
			insertrow.insert(0, i)
			pt.add_row(insertrow)
			i += 1
		print(pt)

def get_prop(x_min, x_max, x):
	return 2 * (x - x_min) / (x_max - x_min) - 1

def getdot(pfe):
	m1_min = pfe.factors[0][0]
	m1_max = pfe.factors[0][1]
	m2_min = pfe.factors[1][0]
	m2_max = pfe.factors[1][1]
	sigma2_min = pfe.factors[2][0]
	sigma2_max = pfe.factors[2][1]
	m3_min = pfe.factors[3][0]
	m3_max = pfe.factors[3][1]

	m1_prompt = "Введите интенсивность генерации " + str(m1_min) + " - " + str(m1_max) + ": "
	m3_prompt = "Введите интенсивность второго генератора " + str(m3_min) + " - " + str(m3_max) + ": "
	m2_prompt = "Введите интенсивность обслуживания " + str(m2_min) + " - " + str(m2_max) + ": "
	sigma2_prompt= "Введите среднеквадратическое отклонения обслуживания " + str(sigma2_min) + " - " + str(sigma2_max) + ": "
	m1 = float(input(m1_prompt))
	m2 = float(input(m2_prompt))
	sigma2 = float(input(sigma2_prompt))
	m3 = float(input(m3_prompt))
	if (m1 < m1_min or m1 > m1_max):
		print("Интенсивность генерации 1 не входит в факторное пространство")
		return
	if (m3 < m3_min or m3 > m3_max):
		print("Интенсивность генерации 2 не входит в факторное пространство")
		return
	if (m2 < m2_min or m2 > m2_max):
		print("Интенсивность обслуживания не входит в факторное пространство")
		return
	if (sigma2 < sigma2_min or sigma2 > sigma2_max):
		print("Cреднеквадратическое отклонения обслуживания обслуживания не входит в факторное пространство")
		return
	m1_prop = get_prop(m1_min, m1_max, m1)
	m2_prop = get_prop(m2_min, m2_max, m2)
	sigma2_prop = get_prop(sigma2_min, sigma2_max, sigma2)
	m3_prop = get_prop(m3_min, m3_max, m3)

	model = System()
	model.set_generators_by_intensity([m1, m3])
	model.set_operators_by_intensity_and_dispersion([[m2, sigma2]])
	y_avg = sum (model.getStat(5)) / 5
	y_linear = pfe.calculate_linear([m1_prop, m2_prop, sigma2_prop, m3_prop])
	y_nonlinear = pfe.calculate_partly_nonlinear([m1_prop, m2_prop, sigma2_prop, m3_prop])

	print("-------------------------------------------------------------------")
	print("Значение y полученное экспериментально:\t\t", y_avg)
	print("Расчитанное значение y (линейное):\t\t", y_linear)
	print("Разница (линейное):\t\t\t\t", y_avg - y_linear)
	print("Расчитанное значение y (частично-нелинейное):\t", y_nonlinear)
	print("Разница (частично-нелинейное):\t\t\t", y_avg - y_nonlinear)

def getdotbyprop(pfe, dfe):
	m1_min = pfe.factors[0][0]
	m1_max = pfe.factors[0][1]
	m2_min = pfe.factors[1][0]
	m2_max = pfe.factors[1][1]
	sigma2_min = pfe.factors[2][0]
	sigma2_max = pfe.factors[2][1]
	m3_min = pfe.factors[3][0]
	m3_max = pfe.factors[3][1]

	m1_min = dfe.factors[0][0]
	m1_max = dfe.factors[0][1]
	m2_min = dfe.factors[1][0]
	m2_max = dfe.factors[1][1]
	sigma2_min = dfe.factors[2][0]
	sigma2_max = dfe.factors[2][1]
	m3_min = dfe.factors[3][0]
	m3_max = dfe.factors[3][1]

	m1_prompt = "Введите кодированное значение интенсивности генерации: "
	m3_prompt = "Введите интенсивность второго генератора "
	m2_prompt = "Введите кодированное значение интенсивности обслуживания: "
	sigma2_prompt= "Введите кодированное значение среднеквадратического отклонения обслуживания: "
	m1_prop = float(input(m1_prompt))
	m3_prop = float(input(m3_prompt))
	m2_prop = float(input(m2_prompt))
	sigma2_prop = float(input(sigma2_prompt))
	if (m1_prop < -1 or m1_prop > 1):
		print("Интенсивность генерации не входит в факторное пространство")
	if (m3_prop < -1 or m3_prop > 1):
		print("Интенсивность генерации 2 не входит в факторное пространство")
	if (m2_prop < -1 or m2_prop > 1):
		print("Интенсивность обслуживания не входит в факторное пространство")
		return
	if (sigma2_prop < -1 or sigma2_prop > 1):
		print("Cреднеквадратическое отклонения обслуживания обслуживания не входит в факторное пространство")
		return
	m1 = get_value(m1_min, m1_max, m1_prop)
	m2 = get_value(m2_min, m2_max, m2_prop)
	sigma2 = get_value(sigma2_min, sigma2_max, sigma2_prop)
	m3 = get_value(m3_min, m3_max, m3_prop)

	model = System()
	model.set_generators_by_intensity([m1, m3])
	model.set_operators_by_intensity_and_dispersion([[m2, sigma2]])
	y_avg = sum (model.getStat(5)) / 5
	y_linear = pfe.calculate_linear([m1_prop, m2_prop, sigma2_prop, m3_prop])
	y_nonlinear = pfe.calculate_partly_nonlinear([m1_prop, m2_prop, sigma2_prop, m3_prop])

	y_linear_d = dfe.calculate_linear([m1_prop, m2_prop, sigma2_prop, m3_prop])
	y_nonlinear_d = dfe.calculate_partly_nonlinear([m1_prop, m2_prop, sigma2_prop, m3_prop])

	print("-------------------------------------------------------------------")
	print("Значение y полученное экспериментально:\t\t", y_avg)
	print()
	print("Расчитанное значение y (линейное) по ПФЭ:\t\t", y_linear)
	print("Разница (линейное) по ПФЭ:\t\t\t\t", y_avg - y_linear)
	print("Расчитанное значение y (частично-нелинейное) по ПФЭ:\t", y_nonlinear)
	print("Разница (частично-нелинейное) по ПФЭ:\t\t\t", y_avg - y_nonlinear)
	print()
	print("Расчитанное значение y (линейное) по ДФЭ:\t\t", y_linear_d)
	print("Разница (линейное) по ДФЭ:\t\t\t\t", y_avg - y_linear_d)
	print("Расчитанное значение y (частично-нелинейное) по ДФЭ:\t", y_nonlinear_d)
	print("Разница (частично-нелинейное) по ДФЭ:\t\t\t", y_avg - y_nonlinear_d)


if __name__ == "__main__":
	m1_max = 1/ 0.7
	m1_min = 1/2.4
	m2_max = 1/5
	m2_min = 1/6
	sigma2_min = 0.1
	sigma2_max = 1/math.sqrt(3)
	new_generator_m_max = 1/1.4
	new_generator_m_min = 1/4.8
	times = 5
	min_max_factors = [[m1_min, m1_max], [m2_min, m2_max], [sigma2_min, sigma2_max], [new_generator_m_min, new_generator_m_max]]

	print ("PFE")
	pfe = PFE(min_max_factors, times)
	pfe.fill_experiment_data()
	pfe.printtable()
	pfe.fill_calculated_data()
	pfe.printtable()
	pfe.check_adequacy()

	print ("DFE")
	dfe = DFE(min_max_factors, times, 1)
	dfe.fill_experiment_data()
	dfe.printtable()
	dfe.fill_calculated_data()
	dfe.printtable()
	dfe.check_adequacy()

	getdotflag = True
	while (getdotflag):
		flag = input('Ввести координаты из факторного пространства (ДA/нет)? ')
		if (flag == '' or flag.lower() == 'да'):
			getdotbyprop(pfe, dfe)
		elif (flag.lower() == 'нет'):
			getdotflag = False
