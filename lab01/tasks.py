import random
import numpy
import math
import matplotlib.pyplot as plt

class Task:
	def __init__ (self, arrive_time, time_to_operate, generator_id):
		self.arrive_time = arrive_time
		self.time_to_operate = time_to_operate
		self.start_operate_time = 0
		self.await_time = 0
		self.generator_id = generator_id

	def start_operate(self, time, operator_id):
		self.start_operate_time = time
		self.await_time = self.start_operate_time - self.arrive_time
		self.operator_id = operator_id

	def waits(self, cur_time):
		self.await_time = cur_time - self.arrive_time

	def print(self):
		print("arrival", self.arrive_time)
		print("time to operate", self.time_to_operate)
		print("start operate time", self.start_operate_time)
		print("start await time", self.await_time)
		print("gen id", self.generator_id)

class Generator:
	# params = [sigma, a, b]
	def __init__(self, params, id):
		self.sigma = params[0]
		self.a = params[1]
		self.b = params[2]
		assert(self.sigma >= 0)
		assert(self.a >= 0 and self.b >= 0 and self.a < self.b)
		self.id = id


	def generate_new_task(self):
		arrivetimes = numpy.random.rayleigh(self.sigma, 1)
		operatetime = random.uniform(self.a, self.b)
		task = Task(arrivetimes[0], operatetime, self.id)
		return task

# takes time of generated task to get operated
class Operator:
	def __init__(self):
		self.busy = False

class System:
	# generators_conf_array [[sigma, a, b], [sigma2, a2, b2]]
	# generator sigma of coming interavals, a and b of opetation time of the type of task, that this generator produces
	def __init__(self, start_time = 0, end_time = 20, generators_conf_array = [[4, 0, 2]], number_of_multioperators=1):
		assert(start_time >= 0 and end_time >= 0 and end_time > start_time)
		self.start_time = start_time
		self.end_time = end_time

		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = [Generator(generators_conf_array[i], i) for i in range (self.generators_number)]

		assert(number_of_multioperators > 0)
		self.operators_number = number_of_multioperators
		self.operators = [Operator() for i in range(self.operators_number)]

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

	# event[0] - is the time of this event occurance
	def add_event(self, event: list):
		i = 0
		while i < len(self.events) and self.events[i][0] <= event[0]:
			i += 1
		self.events.insert(i, event)

	# event method
	def modeling(self):
		# init queue; first tasks from each generator
		for i in range(self.generators_number):
			newtask = self.generators[i].generate_new_task()
			self.add_event([self.start_time + newtask.arrive_time, 'came', newtask])

		cur_time = self.start_time
		while cur_time < self.end_time:
			event = self.events.pop(0)
			cur_time = event[0]
			if event[1] == 'came':
				# at current time this new task came to the queue, so
				# a) it was generated
				self.generated += 1
				# b) queue length incremented
				self.queue_length += 1
				if (self.queue_length > self.max_queue_length):
					self.max_queue_length = self.queue_length

				# try to start operate this task
				self.start_operate(event)
			else:
				# the task is done
				self.finish_operate(event)

		self.avg_waiting_time /= self.started_processing

	def start_operate(self, event):
		i = 0
		task = event[2]
		while i < self.operators_number and self.operators[i].busy:
			i += 1
		if i != self.operators_number:
			# there is a free operator
			self.queue_length -= 1
			self.operators[i].busy = True
			# event = [time of task arrival, "came"/"done", task object]
			task.start_operate(event[0], i)
			self.started_processing += 1
			self.avg_waiting_time += task.await_time
			if ( task.await_time > self.max_waiting_time):
				self.max_waiting_time = task.await_time
			self.add_event([event[0] + task.time_to_operate, 'done', task])
		else:
			# return task back to queue on its place
			# task that wasnt taken to the operation when its came
			# it is move till free operator
			task.waits(event[0])
			i = 0
			while i < len(self.events) and self.events[i][0] <= event[0] and self.events[i][1] != 'done':
				i += 1
			event[0] = self.events[i][0]
			while i < len(self.events) and self.events[i][0] == event[0]:
				i += 1
			self.events.insert(i + 1, [event[0], 'came', task])

		newtask = self.generators[task.generator_id].generate_new_task()
		newtask.arrive_time += task.arrive_time
		self.add_event([newtask.arrive_time, 'came', newtask])

	def finish_operate(self, event):
		task = event[2]
		self.operators[task.operator_id].busy = False
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

def getGraph():
	ro_array = []
	wait_time = []

	generators_conf_array = []
	alpha = 5
	M = 10 / alpha
	sigma = M * math.sqrt(2 / math.pi)
	generators_conf_array.append(sigma)
	generators_conf_array.append(sigma*2)

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
	model = System(0, 10, [[2, 5, 7]])
	getStat(model, 1)
	# [[sigma, a, b], [sigma2, a2, b2]]
	# getGraph()
