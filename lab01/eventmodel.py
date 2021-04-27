import random
import numpy
import math
import matplotlib.pyplot as plt

class Task:
	def __init__ (self, arrive_time, time_to_operate, generator_id):
		self.cur_time = arrive_time
		self.arrive_time = arrive_time
		self.time_to_operate = time_to_operate
		self.generator_id = generator_id
		self.status = "new"

	def waits(self, queue):
		if (self.status == 'new'):
			i = 0
			while i < len(queue) and queue[i].status == 'done':
				i += 1
			if (i == len(queue)):
				i -= 1
			self.cur_time = queue[i].cur_time
			while i < len(queue) and queue[i].cur_time == self.cur_time:
				i += 1
			if (i == len(queue)):
				i -= 1
			self.await_time = self.cur_time - self.arrive_time
			self.status = "waits"
			queue.insert(i + 1, self)

	def start_operate(self, operator_id):
		self.start_operate_time = self.cur_time
		self.await_time = self.start_operate_time - self.arrive_time
		self.operator_id = operator_id
		self.status = "processing"

	def finish_operate(self):
		self.done_time = self.start_operate + self.time_to_operate
		self.cur_time = self.done_time
		self.status = "done"

	def info(self):
		print("time\t\t", self.cur_time)
		print("status\t\t", self.status)
		print("gen id\t\t", self.generator_id)
		print("arrival\t\t", self.arrive_time)
		print("time to operate\t\t", self.time_to_operate)
		if (self.status == 'waits'):
			print("await time\t\t", self.await_time)
		if (self.status == 'processing'):
			print("await time\t\t", self.await_time)
			print("start operate time\t\t", self.start_operate_time)
			print("op id\t\t", self.operator_id)
		if (self.status == 'done'):
			print("await time\t\t", self.await_time)
			print("start operate time\t\t", self.start_operate_time)
			print("op id\t\t", self.operator_id)

class Generator:
	# params = [sigma, a, b]
	def __init__(self, params, id):
		self.sigma = params[0]
		self.a = params[1]
		self.b = params[2]
		assert(self.sigma >= 0)
		assert(self.a >= 0 and self.b >= 0 and self.a < self.b)
		self.id = id
		self.lasttime = 0

	def generate_new_task(self):
		arrivetimes = numpy.random.rayleigh(self.sigma, 1)
		self.lasttime += arrivetimes[0]
		operatetime = random.uniform(self.a, self.b)
		task = Task(self.lasttime, operatetime, self.id)
		return task

	def add_new_task_to_the_queue(self, queue):
		new_task = self.generate_new_task
		i = 0
		while i < len(queue) and queue[i].cur_time <= new_task.cur_time:
			i += 1
		queue.insert(i, new_task)

class Operator:
	def __init__(self, id):
		self.busy = False
		self.id = id

	def operate_task(self, queue):
		if (self.busy):
			return -1
		task = queue.pop(0)
		while (task.status == 'done'):
			task = queue.pop(0)
		self.busy = True
		task.start_operate(self.id)
		task.finish_operate()
		self.busy = False
		i = 0
		while i < len(queue) and queue[i].cur_time <= task.cur_time:
			i += 1
		queue.insert(i, task)
		return 1

class Model:
	def __init__(self, start_time = 0, end_time = 20, generators_conf_array = [[4, 0, 2]], number_of_multioperators=1):
		assert(start_time >= 0 and end_time >= 0 and end_time > start_time)
		self.start_time = start_time
		self.end_time = end_time

		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = [Generator(generators_conf_array[i], i) for i in range (self.generators_number)]

		assert(number_of_multioperators > 0)
		self.operators_number = number_of_multioperators
		self.operators = [Operator(i) for i in range(self.operators_number)]

		self.avg_waiting_time = 0
		self.queue = list()

	def reset(self):
		self.avg_waiting_time = 0
		self.queue = list()
		for i in self.operators:
			operators[i].busy = False

	def calculate(self, times):
		cur_time = self.start_time
		while (cur_time < start_time):
			for generator in self.generators:
				generator.add_new_task_to_the_queue(self.queue)
			for operator in self.operators:
				if (operator.operate_task(self.queue) == -1):
					task = self.queue.pop(0)
					task.waits()

