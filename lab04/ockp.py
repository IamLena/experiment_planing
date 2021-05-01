from model import Model
import random
import numpy
import math
from prettytable import PrettyTable
from itertools import combinations
from scipy import stats

def get_value(prop, min_max):
	x_min = min_max[0]
	x_max = min_max[1]
	return (prop + 1) / 2 * (x_max - x_min) + x_min

def get_prop(x_min, x_max, x):
	return 2 * (x - x_min) / (x_max - x_min) - 1

class OCKP:
	def __init__ (self, min_max_params, times):
		self.min_max_params = min_max_params
		self.times = times
		self.number_of_factors = len(min_max_params)
		self.n = 2**self.number_of_factors
		self.na = 2*self.number_of_factors
		self.nc = 1
		self.number_of_experiments = self.n + self.na + self.nc
		self.doubles_count = int((self.number_of_factors) * (self.number_of_factors - 1)/2)
		self.S = math.sqrt(self.n / self.number_of_experiments)
		self.alpha = math.sqrt(self.n / 2 * (math.sqrt(self.number_of_experiments / self.n) - 1))
		self.plantable = []
		self.realtable = []
		self.exp_data_filled = False
		self.cal_data_filled = False
		self.koef_count = 2 * self.number_of_factors + self.doubles_count + 1

		print("ОЦКП для ", str(self.number_of_factors), " факторов")
		print("Количество экспериментов ", self.number_of_experiments)
		print("Количество коэффициентов в уравнении регрессии второй степени ", self.koef_count)
		print("S = ", self.S)
		print("alpha = ", self.alpha)
		print("--------------------------------")

		self.form_plantable()
		# self.show_plantable()

		self.form_realtable()
		# self.show_realtable()
		self.fill_experiment_data()
		# self.show_realtable()

		self.koefs = []
		self.calculate_koefs()

		self.fill_calculated_data()
		self.show_realtable()

		self.print_equation()

	def form_plantable(self):
		for experiment in range(self.n):
			tablerow = []
			for i in range(self.number_of_factors):
				if (experiment & (1 << i)):
					tablerow.append(-1)
				else:
					tablerow.append(1)
			for i in range(1, self.number_of_factors):
				for j in range(i + 1, self.number_of_factors + 1):
					tablerow.append(tablerow[i-1] * tablerow[j-1])
			for i in range(self.number_of_factors):
				tablerow.append(1 - self.S)
			self.plantable.append(tablerow)

		for experiment in range(self.na):
			tablerow = []
			pos = math.floor(experiment / 2) + 1
			for i in range(self.number_of_factors):
				if (i < self.number_of_factors - pos):
					tablerow.append(0)
				elif (i == self.number_of_factors - pos):
					if (experiment % 2 == 0):
						tablerow.append(-self.alpha)
					else:
						tablerow.append(self.alpha)
				else:
					tablerow.append(0)
			for i in range(1, self.number_of_factors):
				for j in range(i + 1, self.number_of_factors + 1):
					tablerow.append(tablerow[i-1] * tablerow[j-1])
			for i in range(self.number_of_factors):
				tablerow.append(tablerow[i]**2 - self.S)
			self.plantable.append(tablerow)

		tablerow = []
		for i in range(self.number_of_factors):
			tablerow.append(0)
		for i in range(1, self.number_of_factors):
			for j in range(i + 1, self.number_of_factors + 1):
				tablerow.append(tablerow[i-1] * tablerow[j-1])
		for i in range(self.number_of_factors):
			tablerow.append(-self.S)
		self.plantable.append(tablerow)


	def show_plantable(self):
		pt = PrettyTable()
		field_names = ['#']
		for factor in range (self.number_of_factors + 1):
			field_names.append('x' + str(factor))

		for i in range(1, self.number_of_factors):
			for j in range(i + 1, self.number_of_factors + 1):
				field_names.append('x' + str(i) + 'x' + str(j))

		for factor in range (1, self.number_of_factors + 1):
			field_names.append('x' + str(factor) + '^2 - S')

		pt.field_names = field_names
		i = 1
		for row in self.plantable:
			insertrow = row.copy()
			insertrow.insert(0, i)
			insertrow.insert(1, str(1))
			pt.add_row(insertrow)
			i += 1
		print(pt)
		# print(pt.get_string(fields=["x1","x1^2-S"]))


	def form_realtable(self):
		tablelen = len(self.plantable[0])
		for experiment in range(self.number_of_experiments):
			tablerow = []
			for i in range(self.number_of_factors):
				tablerow.append(get_value(self.plantable[experiment][i],self.min_max_params[i]))
			for i in range(self.number_of_factors - 1):
				for j in range(i + 1, self.number_of_factors):
					tablerow.append(get_value(self.plantable[experiment][i],self.min_max_params[i]) * get_value(self.plantable[experiment][j],self.min_max_params[j]))
			for i in range(self.number_of_factors):
				tablerow.append(get_value(self.plantable[experiment][i],self.min_max_params[i])**2 - self.S)
			self.realtable.append(tablerow)


	def show_realtable(self):
		pt = PrettyTable()
		field_names = ['#']
		for factor in range (1, self.number_of_factors + 1):
			field_names.append('x' + str(factor))

		for i in range(1, self.number_of_factors):
			for j in range(i + 1, self.number_of_factors + 1):
				field_names.append('x' + str(i) + 'x' + str(j))

		for factor in range (1, self.number_of_factors + 1):
			field_names.append('x' + str(factor) + '^2 - S')

		if (self.exp_data_filled):
			field_names.append('y_avg of ' + str(self.times) + ' times')
			field_names.append('disperssion')

		if (self.cal_data_filled):
			field_names.append('calculated_y')
			field_names.append('y_diff')

		pt.field_names = field_names
		i = 1
		for row in self.realtable:
			insertrow = row.copy()
			insertrow.insert(0, i)
			pt.add_row(insertrow)
			i += 1
		# print(pt)
		print(pt.get_string(fields=['y_avg of ' + str(self.times) + ' times', 'calculated_y', 'y_diff']))
		# print(pt.get_string(fields=["x1","x1^2 - S"]))


	def fill_experiment_data(self):
		self.exp_data_filled = True
		sumdisppersion = 0
		maxdispersion = 0
		for exp in range(self.number_of_experiments):
			# change to fit model
			x1 = self.realtable[exp][0]
			x2 = self.realtable[exp][1]
			x3 = self.realtable[exp][2]
			x4 = self.realtable[exp][3]
			x5 = self.realtable[exp][4]
			x6 = self.realtable[exp][5]
			##############
			sigma1 =  1 / x1 * math.sqrt(2 / math.pi)
			a1 = 1/x2 - x3 * math.sqrt(3)
			b1 = 1/x2 + x3 * math.sqrt(3)
			sigma2 =  1 / x4 * math.sqrt(2 / math.pi)
			a2 = 1/x5 - x6 * math.sqrt(3)
			b2 = 1/x5 + x6 * math.sqrt(3)

			model = Model(0, 20, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
			#############################
			y_arr = model.array_calculate(self.times)
			y_avg = sum(y_arr)/self.times
			self.realtable[exp].append(y_avg)
			y_dispersion = sum([(y_avg - y_ex_value)**2 / self.times for y_ex_value in y_arr])
			self.realtable[exp].append(y_dispersion)
			if (y_dispersion > maxdispersion):
				maxdispersion = y_dispersion
			sumdisppersion += y_dispersion

		self.Gp = maxdispersion / sumdisppersion
		self.Sv = sumdisppersion / self.number_of_experiments
		self.Sa = (self.S / self.number_of_experiments / self.times) ** 0.5
		self.student_table = stats.t(df=(self.number_of_experiments * (self.times - 1))).ppf(0.95)
		self.meaningful_koefs = 0


	def calculate_koefs(self):
		assert(self.exp_data_filled == True)
		a0 = 0
		y_avg_index = int(2 * self.number_of_factors + self.number_of_factors * (self.number_of_factors - 1) / 2)
		self.y_avg_index = y_avg_index
		for exp in range(self.number_of_experiments):
			a0 += self.realtable[exp][y_avg_index]
		a0 /= self.number_of_experiments
		self.koefs.append(a0)

		koef_value = 0
		for i in range(y_avg_index):
			for exp in range(self.number_of_experiments):
				koef_value += self.plantable[exp][i] * self.realtable[exp][y_avg_index]
			if (i < self.number_of_factors):
				delim = self.n + 2 * self.alpha **2
			elif (i < self.number_of_factors + self.number_of_factors * (self.number_of_factors - 1) / 2):
				delim = self.n
			else:
				delim = 2 * self.alpha**4
			koef_value /= delim
			self.koefs.append(koef_value)

		# print(self.student_table)
		# print(len(self.koefs))
		# print(self.koefs)

		comb = []
		for i in range(self.number_of_factors + 1):
			comb.append("a"+str(i))
		for i in range(1, self.number_of_factors):
			for j in range(i + 1, self.number_of_factors + 1):
				comb.append("a"+str(i)+str(j))
		for i in range(1, self.number_of_factors + 1):
			comb.append("a"+str(i)+str(i))
		j = 0
		# zero to non meaningfull koefs
		print("Student criteria = ", self.student_table)
		print("name\t\tvalue\t\tmeaning_value\tis_meaningfull")
		for koef_index in range(len(self.koefs)):
			koef_value = self.koefs[koef_index]
			koef_meaning = abs(koef_value)/self.Sa
			if (koef_meaning >= self.student_table):
				print (comb[j], "\t\t", round(koef_value, 7), "\t", round(koef_meaning, 7), "\t✓")
				self.meaningful_koefs += 1
			else:
				print (comb[j], "\t\t", round(koef_value, 7), "\t", round(koef_meaning, 7))
				self.koefs[koef_index] = 0
			j += 1


	def fill_calculated_data(self):
		self.cal_data_filled = True
		for exp in range(self.number_of_experiments):
			y = self.koefs[0]
			for i in range(1, len(self.koefs)):
				y += self.koefs[i] * self.plantable[exp][i-1]
			y_diff = y - self.realtable[exp][self.y_avg_index]
			self.realtable[exp].append(y)
			self.realtable[exp].append(y_diff)

		sumsquarediffs = 0
		for exp in range(self.number_of_experiments):
			sumsquarediffs += self.realtable[exp][self.y_avg_index + 2]
		self.Sad = self.number_of_factors / (self.number_of_experiments - self.meaningful_koefs) * sumsquarediffs
		self.F = self.Sad / self.Sv


	def print_equation(self):
		comb = []
		for i in range(self.number_of_factors + 1):
			comb.append("x"+str(i))
		for i in range(1, self.number_of_factors):
			for j in range(i + 1, self.number_of_factors + 1):
				comb.append("x"+str(i)+str(j))
		for i in range(1, self.number_of_factors + 1):
			comb.append("x"+str(i)+"^2")
		j = 0

		print("y = ", str(round(self.koefs[0], 4)), end="")
		for i in range(1, len(self.koefs)):
			if (self.koefs[i] != 0):
				print(" +", str(round(self.koefs[i], 4)) + comb[i], end="")
		print()

	def calculate(self, factors):
		assert(len(factors) == self.number_of_factors)
		res = self.koefs[0]
		for i in range(self.number_of_factors):
			res += self.koefs[i + 1] * get_value(factors[i], self.min_max_params[i])
		for i in range(self.number_of_factors - 1):
			for j in range(i+1, self.number_of_factors):
				res += self.koefs[self.number_of_factors + i + j] *  get_value(factors[i], self.min_max_params[i]) * get_value(factors[j], self.min_max_params[j])
		offset = int (self.number_of_factors + (self.number_of_factors - 1)*self.number_of_factors / 2)
		for i in range(self.number_of_factors):
			res += self.koefs[offset + i] * get_value(factors[i], self.min_max_params[i])**2
		return res

def getdotbyprop(ockp):
	x1_min = ockp.min_max_params[0][0]
	x1_max = ockp.min_max_params[0][1]
	x2_min = ockp.min_max_params[1][0]
	x2_max = ockp.min_max_params[1][1]
	x3_min = ockp.min_max_params[2][0]
	x3_max = ockp.min_max_params[2][1]
	x4_min = ockp.min_max_params[3][0]
	x4_max = ockp.min_max_params[3][1]
	x5_min = ockp.min_max_params[4][0]
	x5_max = ockp.min_max_params[4][1]
	x6_min = ockp.min_max_params[5][0]
	x6_max = ockp.min_max_params[5][1]

	x1_prop = float(input("Введите кодированное значение интенсивности генератора 1: "))
	x2_prop = float(input("Введите кодированное значение интенсивность обработки заявки 1 типа: "))
	x3_prop = float(input("Введите кодированное значение среднеквадратического отклонение обработки заявки 1 типа : "))
	x4_prop = float(input("Введите кодированное значение интенсивности генератора 2: "))
	x5_prop = float(input("Введите кодированное значение интенсивность обработки заявки 2 типа: "))
	x6_prop = float(input("Введите кодированное значение среднеквадратического отклонение обработки заявки 2 типа : "))

	assert(-1 <= x1_prop <= 1)
	assert(-1 <= x2_prop <= 1)
	assert(-1 <= x3_prop <= 1)
	assert(-1 <= x4_prop <= 1)
	assert(-1 <= x5_prop <= 1)
	assert(-1 <= x6_prop <= 1)

	x1 = get_value(x1_prop, [x1_min, x1_max])
	x2 = get_value(x2_prop, [x2_min, x2_max])
	x3 = get_value(x3_prop, [x3_min, x3_max])
	x4 = get_value(x4_prop, [x4_min, x4_max])
	x5 = get_value(x5_prop, [x5_min, x5_max])
	x6 = get_value(x6_prop, [x6_min, x6_max])

	sigma1 =  1 / x1 * math.sqrt(2 / math.pi)
	a1 = 1/x2 - x3 * math.sqrt(3)
	b1 = 1/x2 + x3 * math.sqrt(3)
	sigma2 =  1 / x4 * math.sqrt(2 / math.pi)
	a2 = 1/x5 - x6 * math.sqrt(3)
	b2 = 1/x5 + x6 * math.sqrt(3)

	model = Model(0, 100, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
	y_avg = model.calculate(5)
	y_cal = ockp.calculate([x1_prop, x2_prop, x3_prop, x4_prop, x5_prop, x6_prop])

	print("-------------------------------------------------------------------")
	print("Значение y полученное экспериментально:\t\t", y_avg)
	print()
	print("Расчитанное значение y по ОЦКП:\t\t", y_cal)
	print("Разница:\t\t\t\t", y_avg - y_cal)


x1_min = 0.1
x1_max = 0.2

x2_min = 0.7
x2_max = 0.8

x3_min = 0.03
x3_max = 0.1

x4_min = 0.125
x4_max = 0.4

x5_min = 0.9
x5_max = 1.1

x6_min = 0.05
x6_max = 0.15

times = 5
min_max_factors = [[x1_min, x1_max], [x2_min, x2_max], [x3_min, x3_max], [x4_min, x4_max], [x5_min, x5_max], [x6_min, x6_max]]
ockp = OCKP(min_max_factors, times)

getdotflag = True
while (getdotflag):
	flag = input('Рассчитать значение для точки из факторного пространства (ДA/нет)?')
	if (flag == '' or flag.lower() == 'да'):
		getdotbyprop(ockp)
	elif (flag.lower() == 'нет'):
		getdotflag = False
