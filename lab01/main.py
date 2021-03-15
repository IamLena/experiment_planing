import random
import numpy
import math
import matplotlib.pyplot as plt

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
	queue_length = 0
	max_queue_length = 0
	generated = 0
	started_processing = 0
	processed = 0
	avg_waiting_time = 0
	max_waiting_time = 0

	for i in range(times):
		model.modeling()
		queue_length += model.queue_length
		max_queue_length += model.max_queue_length
		generated += model.generated
		started_processing += model.started_processing
		processed += model.processed
		avg_waiting_time += model.avg_waiting_time
		max_waiting_time += model.max_waiting_time
		model.reset()

	queue_length /= times
	max_queue_length /= times
	generated /= times
	started_processing /= times
	processed /= times
	avg_waiting_time /= times
	max_waiting_time /= times
	print("---------------------------------------------------------")
	print("длина очереди в конце моделировная\t\t\t", queue_length)
	print("максимальная длина очереди за время моделирования\t", max_queue_length)
	print("количество сгенерированных заявок\t\t\t", generated)
	print("количество заявок, отправленных на обслуживание\t\t", started_processing)
	print("количество обслуженных заявок\t\t\t\t", processed)
	print("среднее время ожидания в очереди\t\t\t", avg_waiting_time)
	print("максимальное время ожидания в очереди\t\t\t", max_waiting_time)
	return (avg_waiting_time)

def input_model():
	generators_conf_array = []
	g_n = int(input("Введите количество генераторов: "))
	assert(g_n > 0)
	param_or_intensity = int(input("Интервалы времени между приходом заявок распределены по закону Рэлея\nКак определить генраторы?\n1-С помощью параметра сигма\n2-С помощью интенсивности поступления заявок\nВведите 1 или 2: "))
	assert(param_or_intensity == 1 or param_or_intensity == 2)
	for i in range (g_n):
		if (param_or_intensity == 1):
			msg = "Введите значение сигма для генератора" + str(i) + ": "
			generators_conf_array.append(float(input(msg)))
		else:
			alpha = float(input("Введите среднюю интенсивность для генератора" + str(i) + " (количество заявок в 10 единиц времени): "))
			M = 10 / alpha
			sigma = M * math.sqrt(2 / math.pi)
			print("sigma ", sigma)
			generators_conf_array.append(sigma)

	operators_conf_array = []
	op_n = int(input("Введите количество операторов: "))
	assert(op_n > 0)
	param_or_intensity = int(input("Закон распределения времени обслуживания заявок - равномерный\nКак определить операторы?\n1-С помощью параметров a и b\n2-С помощью интенсивности обсулживания заявок\nВведите 1 или 2: "))
	assert(param_or_intensity == 1 or param_or_intensity == 2)
	for i in range (op_n):
		if (param_or_intensity == 1):
			a = float(input("Введите значение a для оператора" + str(i) + ": "))
			b = float(input("Введите значение b для оператора" + str(i) + ": "))
			operators_conf_array.append([a, b])
		else:
			mu = float(input("Введите среднюю интенсивность для оператора" + str(i) + " (количество заявок в 10 единиц времени): "))
			M = 10 / mu
			sigma = float(input("Введите разброс значений времени обслуживания (среднеквадратичное отклонение) для оператора" + str(i) + ": "))
			a = M - sigma * math.sqrt(3)
			b = M + sigma * math.sqrt(3)
			print("a  ", a, "; b ", b)
			assert(a >= 0 and b >= 0 and a < b)
			operators_conf_array.append([a, b])
	start_time = float(input("Введите время начала моделирования: "))
	assert(start_time >= 0)
	end_time = float(input("Введите время окончания моделирования: "))
	assert(end_time >= 0)
	model = System(start_time, end_time, generators_conf_array, operators_conf_array)
	return model

def getGraph():
	ro_array = []
	wait_time = []

	generators_conf_array = []
	alpha = 5
	M = 10 / alpha
	sigma = M * math.sqrt(2 / math.pi)
	generators_conf_array.append(sigma)

	ro = 0.05
	while (ro <= 1):
		ro_array.append(ro)
		operators_conf_array = []
		mu = alpha / ro
		M = 10 / mu
		sigma = 0.05 * M #just 5% of M
		a = M - sigma * math.sqrt(3)
		b = M + sigma * math.sqrt(3)
		operators_conf_array.append([a, b])

		model = System(0, 50, generators_conf_array, operators_conf_array)
		# model.modeling()
		# wait_time.append(model.avg_waiting_time)

		wait_time.append(getStat(model, 50))
		print(ro_array)
		print(wait_time)
		ro += 0.05

	plt.plot(ro_array, wait_time)
	plt.xlabel("ro")
	plt.ylabel("ave_wait_time")
	plt.show()

if __name__ == "__main__":
	model = input_model()
	times = int(input("Введите количество повторений моделирования для нахождения среднего значения: "))
	assert(times > 0)
	getStat(model, times)

	# model = System(0, 10, [2], [[2, 5]])
	# getStat(model, 1)

	# getGraph()
