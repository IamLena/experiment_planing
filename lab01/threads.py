import threading
import time
import logging
import random
import numpy
import math

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

queue = []
res = []

class Task():
	def __init__ (self, arrival, process, gen_id):
		self.arrival_time = arrival
		self.process_time = process
		self.await_time = 0
		self.gen_id = gen_id
		self.begin_process = -1
		self.op_id = -1

	def process(self, begin_time, op_id):
		self.begin_process = begin_time
		self.await_time = self.begin_process - self.arrival_time
		self.op_id = op_id

	def print(self):
		logging.debug('arrived ' + str(self.arrival_time) + ' : waited ' + str(self.await_time) + ' : needs ' + str(self.process_time) + ' to be processed : started process ' + str(self.begin_process) + ' : gen_' + str(self.gen_id) + ' : op_' + str(self.op_id))

class GeneraterThread(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, sigma=2, a=1, b=3, id=0, start_time = 0, stop_time = 15):
		super(GeneraterThread,self).__init__()
		self.target = target
		self.name = name
		self.sigma = sigma
		self.a = a
		self.b = b
		self.id = id
		self.start_time = start_time
		self.stop_time = stop_time

	def run(self):
		cur_time = self.start_time
		while (cur_time < self.stop_time):
			operatetime = random.uniform(self.a, self.b)
			newtask = Task(cur_time, operatetime, self.id)
			queue.append(newtask)
			logging.debug('NEW ' + str(cur_time) + ' : ' + str(len(queue)) + ' items in queue')
			newtask.print()
			arrivetimes = numpy.random.rayleigh(self.sigma, 1)
			sleep_time =  arrivetimes[0]
			time.sleep(sleep_time)
			cur_time += sleep_time

class OperatorThread(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, id=1, start_time = 0, stop_time = 15):
		super(OperatorThread,self).__init__()
		self.target = target
		self.name = name
		self.id = id
		self.start_time = start_time
		self.stop_time = stop_time

	def run(self):
		number_of_process_tasks = 0
		await_time = 0
		cur_time = self.start_time
		while (cur_time < self.stop_time):
			if (len(queue) > 0):
				task = queue.pop(0)
				logging.debug('POP ' + str(len(queue)) + ' items left in queue')
				if (cur_time < task.arrival_time):
					cur_time = task.arrival_time
				task.process(cur_time, self.id)
				task.print()
				time.sleep(task.process_time)
				cur_time += task.process_time
				number_of_process_tasks += 1
				await_time += task.await_time
		avg_await_time = await_time / number_of_process_tasks
		res.append(avg_await_time)

if __name__ == '__main__':
	gen1 = GeneraterThread(name='generater', sigma = 4, a = 1, b = 3, id = 0, start_time = 0, stop_time = 5)
	gen2 = GeneraterThread(name='generater', sigma = 2, a = 2, b = 3, id = 1, start_time = 0, stop_time = 5)
	op = OperatorThread(name='operator', start_time = 0, stop_time = 5)

	gen1.start()
	gen2.start()
	op.start()

	gen1.join()
	gen2.join()
	op.join()
	print(res)
