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
	def __init__(self, start_time = 0, end_time = 20, generators_conf_array = [4], operators_conf_array = [[0, 2]]):
		assert(start_time >= 0 and end_time >= 0 and end_time > start_time)
		self.start_time = start_time
		self.end_time = end_time

		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = [Generator(generators_conf_array[i]) for i in range (self.generators_number)]

		assert(len(operators_conf_array) != 0)
		self.operators_number = len(operators_conf_array)
		self.operators = [Operator(operators_conf_array[i][0], operators_conf_array[i][1]) for i in range(self.operators_number)]

		self.queue_length = 0
		self.max_queue_length = 0
		self.generated = 0
		self.processed = 0
		self.avg_waiting_time = 0
		self.started_processing = 0
		self.max_waiting_time = 0
		self.events = list()

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
			# print(event)
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


def getStat(model, times):
	waiting_time_arr = []

	for i in range(times):
		model.modeling()
		waiting_time_arr.append(model.avg_waiting_time)
		model.reset()

	return (waiting_time_arr)

def printtable(table, times):
	pt = PrettyTable()
	column_name = "y_avg out of " + str(times)
	pt.field_names = ["#", "x1", "x2", "x3", column_name, "y_dispersion", "math result", "diff"]
	for i in table:
		pt.add_row(i)
	print(pt)

def pfe(m1_min, m1_max, m2_min, m2_max, sigma2_min, sigma2_max, times):
	table = []
	sumdisppersion = 0
	maxdispersion = 0
	for i in range (8):
		tablerow = []
		if (i & 0b00000001 == 0b00000001):
			sigma2 = sigma2_max
		else:
			sigma2 = sigma2_min
		if (i & 0b00000010 == 0b00000010):
			m2 = m2_max
		else:
			m2 = m2_min
		if (i & 0b00000100 == 0b00000100):
			m1 = m1_max
		else:
			m1 = m1_min
		model = init_model(m1, m2, sigma2, 0, 20)
		y_array = getStat(model, times)
		length = len(y_array)
		y_avg = sum(y_array) / length
		y_dispersion = sum([(y_avg - i)**2 / length for i in y_array])
		if (y_dispersion > maxdispersion):
			maxdispersion = y_dispersion
		sumdisppersion += y_dispersion
		tablerow.append(i+1)
		tablerow.append(m1)
		tablerow.append(m2)
		tablerow.append(sigma2)
		tablerow.append(y_avg)
		tablerow.append(y_dispersion)
		tablerow.append("-")
		tablerow.append("-")
		table.append(tablerow)
	printtable(table, times)
	Gp = maxdispersion/sumdisppersion
	S = sumdisppersion / 8
	print("Критерий Кохрена: ", Gp)
	print("дисперсии воспроизводимости ", S)
	assert(Gp < 0.3910)
	koefs = calculate_koefs(table)
	y_hat = calculate(koefs)
	for i in range(8):
		table[i][6] = y_hat[i]
		table[i][7] = table[i][4] - y_hat[i]
	printtable(table, times)

def calculate(koefs):
	table = []
	for i in range (8):
		tablerow = []
		if (i & 0b00000001 == 0b00000001):
			sigma2 = 1
		else:
			sigma2 = -1
		if (i & 0b00000010 == 0b00000010):
			m2 = 1
		else:
			m2 = -1
		if (i & 0b00000100 == 0b00000100):
			m1 = 1
		else:
			m1 = -1
		tablerow.append(m1)
		tablerow.append(m2)
		tablerow.append(sigma2)
		table.append(tablerow)
	y_hat = []
	N = len(table)
	for i in range (N):
		y_hat_value = koefs[0] + koefs[1]*table[i][0] + koefs[2]*table[i][1] + koefs[3]*table[i][2] + koefs[4]*table[i][0]*table[i][1] + koefs[5]*table[i][0]*table[i][2] + koefs[6]*table[i][1]*table[i][2]
		y_hat.append(y_hat_value)
	return y_hat

def init_model(m1, m2, sigma2, start_time, end_time):
	generators_conf_array = []
	operators_conf_array = []

	M = m1
	sigma = M * math.sqrt(2 / math.pi)
	generators_conf_array.append(sigma)

	M = m2
	sigma = sigma2
	a = M - sigma * math.sqrt(3)
	b = M + sigma * math.sqrt(3)
	assert(a >= 0 and b >= 0 and a < b)
	operators_conf_array.append([a, b])

	model = System(start_time, end_time, generators_conf_array, operators_conf_array)
	return model

def calculate_koefs(table):
	ones = []
	for i in range (8):
		onesrow = []
		if (i & 0b00000001 == 0b00000001):
			sigma2 = 1
		else:
			sigma2 = -1
		if (i & 0b00000010 == 0b00000010):
			m2 = 1
		else:
			m2 = -1
		if (i & 0b00000100 == 0b00000100):
			m1 = 1
		else:
			m1 = -1
		onesrow.append(m1)
		onesrow.append(m2)
		onesrow.append(sigma2)
		ones.append(onesrow)

	koefs = []
	N = len(table)
	a_0 = 0
	for row in table:
		a_0 += row[4]
	a_0 /= N
	koefs.append(a_0)
	for i in range(3):
		ai_value = 0
		for n in range (N):
			ai_value += ones[n][i] * table[n][4]
		ai_value /= N
		koefs.append(ai_value)
	for i in range(3 - 1):
		for j in range(i + 1, 3):
			aij_value = 0
			for n in range (N):
				aij_value += ones[n][i] * ones[n][j] * table[n][4]
			aij_value /= N
			koefs.append(aij_value)

	print("a0: ", koefs[0])
	print("a1: ", koefs[1])
	print("a2: ", koefs[2])
	print("a3: ", koefs[3])
	print("a12: ", koefs[4])
	print("a13: ", koefs[5])
	print("a23: ", koefs[6])
	return koefs

if __name__ == "__main__":
	m1_min = 0.7
	m1_max = 2.4
	m2_min = 5
	m2_max = 6
	sigma2_min = 0.1
	sigma2_max = 1/math.sqrt(3)
	times = 5
	pfe(m1_min, m1_max, m2_min, m2_max, sigma2_min, sigma2_max, times)
