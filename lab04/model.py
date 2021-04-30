import numpy
import random
import math

class Task:
	def __init__(self, arrive_time, operate_time, gen_id):
		self.arrive_time = arrive_time
		self.operate_time = operate_time
		self.status = "new"
		self.wait_time = 0
		self.gen_id = gen_id

	def operate(self, cur_time, op_id):
		self.status = "done"
		self.op_id = op_id
		self.wait_time = cur_time - self.arrive_time
		return cur_time + self.operate_time


	def info(self):
		print("status\t\t", self.status)
		print("gen id\t\t", self.gen_id)
		print("arrival\t\t", self.arrive_time)
		print("time to operate\t\t", self.operate_time)
		if (self.status == 'done'):
			print("await time\t\t", self.wait_time)
			print("op id\t\t", self.op_id)

class Event:
	def __init__(self, time, task):
		self.time = time
		self.task = task

class Generator:
	def __init__(self, params, id, start_time):
		self.sigma = params[0]
		self.a = params[1]
		self.b = params[2]
		try:
			assert(self.sigma >= 0)
		except AssertionError:
			print(self.sigma)
			assert(self.sigma >= 0)

		try:
			assert(self.a >= 0 and self.b >= 0 and self.a < self.b)
		except AssertionError:
			print(self.a, self.b)
			assert(self.a >= 0 and self.b >= 0 and self.a < self.b)
		self.id = id
		self.time = start_time

	def generate_new_task(self):
		arrivetimes = numpy.random.rayleigh(self.sigma, 1)
		self.time += arrivetimes[0]
		operatetime = random.uniform(self.a, self.b)
		task = Task(self.time, operatetime, self.id)
		return task

class Operator:
	def __init__(self, id):
		self.id = id
		self.busy = False

	def operate(self, event):
		self.busy = True
		event.task.operate(event.time, self.id)
		event.time += event.task.operate_time
		event.task.status = 'done'
		return event

class Model:
	def __init__(self, start_time = 0, end_time = 20, generators_conf_array = [[4, 0, 2]], number_of_multioperators=1):
		assert(start_time >= 0 and end_time >= 0 and end_time > start_time)
		self.start_time = start_time
		self.end_time = end_time

		assert(len(generators_conf_array) != 0)
		self.generators_number = len(generators_conf_array)
		self.generators = [Generator(generators_conf_array[i], i, self.start_time) for i in range (self.generators_number)]

		assert(number_of_multioperators > 0)
		self.operators_number = number_of_multioperators
		self.operators = [Operator(i) for i in range(self.operators_number)]

		self.avg_waiting_time = 0
		self.count = 0
		self.queue = list()

	def reset(self):
		self.avg_waiting_time = 0
		self.count = 0
		self.queue = list()
		for op in self.operators:
			op.busy = False
		for gen in self.generators:
			gen.time = self.start_time

	def add_event(self, event):
		i = 0
		while i < len(self.queue) and self.queue[i].time <= event.time:
			i += 1
		self.queue.insert(i, event)

	def get_event(self):
		return self.queue.pop(0)

	def set_task_wait(self, task):
		i = 0
		while i < len(self.queue) and self.queue[i].task.status != 'done':
			i += 1
		donetime = self.queue[i].time
		while i < len(self.queue) and self.queue[i].time == donetime:
			i += 1
		task.status = "waits"
		event = Event(donetime, task)
		self.queue.insert(i, event)

	def calculate(self, times, log = 0):
		avg = 0
		for time in range(times):
			for gen in self.generators:
				task = gen.generate_new_task()
				event = Event(task.arrive_time, task)
				if (task.arrive_time < self.end_time):
					self.add_event(event)
					if (log):
						print("\nGENERATE FIRST TASKS")
						print(event.time)
						task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
			cur_time = self.start_time
			while (cur_time < self.end_time and len(self.queue) > 0):
				if (log):
					print("\nCUR TIME", cur_time)
				event = self.get_event()
				cur_time = event.time
				if (cur_time > self.end_time):
					break
				if (log):
					print("\nPOPPED EVENT")
					print(event.time)
					print("len queue: ", len(self.queue))
					print(self.queue)
					event.task.info()
				if (event.task.status == 'new'):
					gen_id = event.task.gen_id
					new_task = self.generators[gen_id].generate_new_task()
					new_event = Event(new_task.arrive_time, new_task)
					if (new_task.arrive_time < self.end_time):
						self.add_event(new_event)
						if (log):
							print("\nGENERATE NEW TASK")
							print(new_event.time)
							new_task.info()
							print("len queue: ", len(self.queue))
							print(self.queue)
				if (event.task.status == 'done'):
					if (log):
						print("\nPOPPED TASK IS DONE")
						print(event.time)
						event.task.info()
					self.operators[event.task.op_id].busy = False
					continue
				i = 0
				while i < self.operators_number and self.operators[i].busy:
					i += 1
				if (i == self.operators_number):
					self.set_task_wait(event.task)
					if (log):
						print("\nTASK IS GOINT TO WAIT")
						print(event.time)
						event.task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
				else:
					event = self.operators[i].operate(event)
					self.avg_waiting_time += event.task.wait_time
					self.count += 1
					self.add_event(event)
					if (log):
						print("\nTASK IS BEING PROCESSED")
						print(event.time)
						event.task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
				cur_time = self.queue[0].time
			while (len(self.queue) > 0):
				if (self.queue[0].task.status == 'done'):
					if (log):
						print("\nPOPPING DONE TASKS AFTER MODEL TIME")
					event = self.queue.pop(0)
					self.operators[event.task.op_id].busy = False
				else:
					break
			ok_flag = False
			if (len(self.queue) == 1 and self.operators[0].busy == False):
				ok_flag = True
			if (log):
				print("len queue: ", len(self.queue))
				print(self.queue)
				if (len(self.queue) > 0):
					print(len(self.queue))
					print(self.operators[0].busy)
					for i in range(len(self.queue)):
						print(self.queue[i].time)
						self.queue[i].task.info()
			if (self.count != 0 and (len(self.queue) == 0 or ok_flag)):
				self.avg_waiting_time /= self.count
			else:
				self.avg_waiting_time = -1
			if (log):
				print("avg", time, ": ", self.avg_waiting_time)
			time += 1
			if (self.avg_waiting_time == -1):
				avg = -1
			else:
				avg += self.avg_waiting_time
			self.reset()
		return avg / times

	def array_calculate(self, times, log = 0):
		avg = []
		for time in range(times):
			for gen in self.generators:
				task = gen.generate_new_task()
				event = Event(task.arrive_time, task)
				if (task.arrive_time < self.end_time):
					self.add_event(event)
					if (log):
						print("\nGENERATE FIRST TASKS")
						print(event.time)
						task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
			cur_time = self.start_time
			while (cur_time < self.end_time and len(self.queue) > 0):
				if (log):
					print("\nCUR TIME", cur_time)
				event = self.get_event()
				cur_time = event.time
				if (cur_time > self.end_time):
					break
				if (log):
					print("\nPOPPED EVENT")
					print(event.time)
					print("len queue: ", len(self.queue))
					print(self.queue)
					event.task.info()
				if (event.task.status == 'new'):
					gen_id = event.task.gen_id
					new_task = self.generators[gen_id].generate_new_task()
					new_event = Event(new_task.arrive_time, new_task)
					if (new_task.arrive_time < self.end_time):
						self.add_event(new_event)
						if (log):
							print("\nGENERATE NEW TASK")
							print(new_event.time)
							new_task.info()
							print("len queue: ", len(self.queue))
							print(self.queue)
				if (event.task.status == 'done'):
					if (log):
						print("\nPOPPED TASK IS DONE")
						print(event.time)
						event.task.info()
					self.operators[event.task.op_id].busy = False
					continue
				i = 0
				while i < self.operators_number and self.operators[i].busy:
					i += 1
				if (i == self.operators_number):
					self.set_task_wait(event.task)
					if (log):
						print("\nTASK IS GOINT TO WAIT")
						print(event.time)
						event.task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
				else:
					event = self.operators[i].operate(event)
					self.avg_waiting_time += event.task.wait_time
					self.count += 1
					self.add_event(event)
					if (log):
						print("\nTASK IS BEING PROCESSED")
						print(event.time)
						event.task.info()
						print("len queue: ", len(self.queue))
						print(self.queue)
				cur_time = self.queue[0].time
			while (len(self.queue) > 0):
				if (self.queue[0].task.status == 'done'):
					if (log):
						print("\nPOPPING DONE TASKS AFTER MODEL TIME")
					event = self.queue.pop(0)
					self.operators[event.task.op_id].busy = False
				else:
					break
			ok_flag = False
			if (len(self.queue) == 1 and self.operators[0].busy == False):
				ok_flag = True
			if (log):
				print("len queue: ", len(self.queue))
				print(self.queue)
				if (len(self.queue) > 0):
					print(len(self.queue))
					print(self.operators[0].busy)
					for i in range(len(self.queue)):
						print(self.queue[i].time)
						self.queue[i].task.info()
			if (self.count != 0 and (len(self.queue) == 0 or ok_flag)):
				self.avg_waiting_time /= self.count
			else:
				self.avg_waiting_time = -1
			if (log):
				print("avg", time, ": ", self.avg_waiting_time)
			time += 1
			if (self.avg_waiting_time == -1):
				# avg.append(-1)
				avg.append(0)
			else:
				avg.append(self.avg_waiting_time)
			self.reset()
		return avg

# x1 = 0.1
# x2 = 0.5
# x3 = 0.1
# x4 = 0.125
# x5 = 0.9
# x6 = 0.05
# print(x1, x2, x3, x4, x5, x6)

# sigma1 =  1 / x1 * math.sqrt(2 / math.pi)
# a1 = 1/x2 - x3 * math.sqrt(3)
# b1 = 1/x2 + x3 * math.sqrt(3)
# sigma2 =  1 / x4 * math.sqrt(2 / math.pi)
# a2 = 1/x5 - x6 * math.sqrt(3)
# b2 = 1/x5 + x6 * math.sqrt(3)

# m1 = 1/x1
# m2 = (a1 + b1) / 2
# m3 = 1 / x4
# m4 = (a2 + b2) / 2

# print(sigma1, a1, b1, sigma2, a2, b2)
# print(m1, m2, m3, m4)

# m = Model(start_time = 0, end_time = 100, generators_conf_array = [[sigma1, a1, b1], [sigma2, a2, b2]], number_of_multioperators=1)
# avg = m.calculate(1)
# print(avg)
