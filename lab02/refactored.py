import random
import numpy
import math
import matplotlib.pyplot as plt
from prettytable import PrettyTable

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
			sigma = generators_conf_array[i] * math.sqrt(2 / math.pi)
			self.generators.append(Generator(sigma))

	def set_operators_by_params(self, operators_conf_array = [[0, 2]]):
		self.operators_number = len(operators_conf_array)
		self.operators = [Operator(operators_conf_array[i][0], operators_conf_array[i][1]) for i in range(self.operators_number)]

	def set_operators_by_intensity_and_dispersion(self, operators_conf_array = [[5, 0.3]]):
		self.operators_number = len(operators_conf_array)
		self.operators = []
		for i in range (self.operators_number):
			a = operators_conf_array[i][0] - operators_conf_array[i][1] * math.sqrt(3)
			b = operators_conf_array[i][0] + operators_conf_array[i][1] * math.sqrt(3)
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

	def fill_experiment_data(self):
		self.experiment_data_filled = True
		model = System(0, 20)
		sumdisppersion = 0
		maxdispersion = 0
		for experiment in range (self.number_of_experiments):
			model.set_generators_by_intensity([self.real_table[experiment][0]])
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

	def calculate_koefs(self):
		self.koefs = []
		y_ex_avg_sum = 0
		for experiment in range(self.number_of_experiments):
			y_ex_avg_sum += self.real_table[experiment][self.number_of_factors]
		self.koefs.append(y_ex_avg_sum / self.number_of_experiments)

		for factor in range (self.number_of_factors):
			koef_value = 0
			for experiment in range(self.number_of_experiments):
				koef_value += self.plan_table[experiment][factor] * self.real_table[experiment][self.number_of_factors]
			koef_value /= self.number_of_experiments
			self.koefs.append(koef_value)

		for factor1 in range(self.number_of_factors - 1):
			for factor2 in range(factor1 + 1, self.number_of_factors):
				koef_value = 0
				for experiment in range(self.number_of_experiments):
					koef_value += self.plan_table[experiment][factor1] * self.plan_table[experiment][factor2] * self.real_table[experiment][self.number_of_factors]
				koef_value /= self.number_of_experiments
				self.koefs.append(koef_value)

	def calculate_partly_nonlinear(self, factors):
		result = self.koefs[0]
		for i in range (self.number_of_factors):
			result += self.koefs[i + 1] * factors[i]
		for i in range (self.number_of_factors - 1):
			for j in range (i + 1, self.number_of_factors):
				result += self.koefs[self.number_of_factors + i + j] * factors[i] * factors[j]
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
		self.Ss = self.times / self.number_of_experiments * diffsqsum
		print("дисперсия адекватности: ", self.Ss)
		self.F = self.Ss / self.S
		print("Критерий Фишера (ад / вос): ", self.F)

	def printtable(self):
		if (self.experiment_data_filled):
			pt = PrettyTable()
			field_names = ['#']
			for factor in range (self.number_of_factors):
				field_names.append('x' + str(factor))
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

	def printkoefs(self):
		print("a0: ", self.koefs[0])
		for i in range (1, self.number_of_factors + 1):
			print("a" + str(i) + ":", self.koefs[i])
		for i in range (self.number_of_factors - 1):
			for j in range (i + 1, self.number_of_factors):
				print("a" + str(i + 1) + str(j + 1) + ":", self.koefs[self.number_of_factors + i + j])

# дисперсия адекватности

def get_prop(x_min, x_max, x):
	return 2 * (x - x_min) / (x_max - x_min) - 1

def getdot(pfe):
	m1_min = pfe.factors[0][0]
	m1_max = pfe.factors[0][1]
	m2_min = pfe.factors[1][0]
	m2_max = pfe.factors[1][1]
	sigma2_min = pfe.factors[2][0]
	sigma2_max = pfe.factors[2][1]

	m1_prompt = "Введите интенсивность генерации " + str(m1_min) + " - " + str(m1_max) + ": "
	m2_prompt = "Введите интенсивность обслуживания " + str(m2_min) + " - " + str(m2_max) + ": "
	sigma2_prompt= "Введите среднеквадратическое отклонения обслуживания " + str(sigma2_min) + " - " + str(sigma2_max) + ": "
	m1 = float(input(m1_prompt))
	m2 = float(input(m2_prompt))
	sigma2 = float(input(sigma2_prompt))
	if (m1 < m1_min or m1 > m1_max):
		print("Интенсивность генерации не входит в факторное пространство")
	if (m2 < m2_min or m2 > m2_max):
		print("Интенсивность обслуживания не входит в факторное пространство")
		return
	if (sigma2 < sigma2_min or sigma2 > sigma2_max):
		print("Cреднеквадратическое отклонения обслуживания обслуживания не входит в факторное пространство")
		return
	m1_prop = get_prop(m1_min, m1_max, m1)
	m2_prop = get_prop(m2_min, m2_max, m2)
	sigma2_prop = get_prop(sigma2_min, sigma2_max, sigma2)

	model = System()
	model.set_generators_by_intensity([m1])
	model.set_operators_by_intensity_and_dispersion([[m2, sigma2]])
	y_avg = sum (model.getStat(5)) / 5
	y_linear = pfe.calculate_linear([m1_prop, m2_prop, sigma2_prop])
	y_nonlinear = pfe.calculate_partly_nonlinear([m1_prop, m2_prop, sigma2_prop])

	print("-------------------------------------------------------------------")
	print("Значение y полученное экспериментально:\t\t", y_avg)
	print("Расчитанное значение y (линейное):\t\t", y_linear)
	print("Разница (линейное):\t\t\t\t", y_avg - y_linear)
	print("Расчитанное значение y (частично-нелинейное):\t", y_nonlinear)
	print("Разница (частично-нелинейное):\t\t\t", y_avg - y_nonlinear)


if __name__ == "__main__":
	m1_min = 0.7
	m1_max = 2.4
	m2_min = 5
	m2_max = 6
	sigma2_min = 0.1
	sigma2_max = 1/math.sqrt(3)
	times = 5
	min_max_factors = [[m1_min, m1_max], [m2_min, m2_max], [sigma2_min, sigma2_max]]
	pfe = PFE(min_max_factors, times)
	pfe.fill_experiment_data()
	pfe.printtable()
	pfe.fill_calculated_data()
	pfe.printkoefs()
	pfe.printtable()
	pfe.check_adequacy()

	getdotflag = True
	while (getdotflag):
		flag = input('Ввести координаты из факторного пространства (ДA/нет)? ')
		if (flag == '' or flag.lower() == 'да'):
			getdot(pfe)
		elif (flag.lower() == 'нет'):
			getdotflag = False
