from model import Model
import random
import numpy
import math
from prettytable import PrettyTable
from itertools import combinations
from scipy import stats

def increment(elem):
	elem += 1
	return elem

def get_value(x_min, x_max, prop):
	return (prop + 1) / 2 * (x_max - x_min) + x_min

def get_prop(x_min, x_max, x):
	return 2 * (x - x_min) / (x_max - x_min) - 1

class PFE:
	# [[m1_min, m1_max], [m2_min, m2_max], [sigma2_min, sigma2_max]]
	def __init__ (self, min_max_factors, times):
		self.factors = min_max_factors
		self.number_of_factors = len(min_max_factors)
		self.number_of_experiments = 2 ** self.number_of_factors
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
				if (experiment & (1 << factor)):
					tablerow.insert(0, -1)
				else:
					tablerow.insert(0, 1)
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
		sumdisppersion = 0
		maxdispersion = 0
		for experiment in range (self.number_of_experiments):
			sigma1 =  1 / self.real_table[experiment][0] * math.sqrt(2 / math.pi)
			a1 = 1/self.real_table[experiment][1] - self.real_table[experiment][2] * math.sqrt(3)
			b1 = 1/self.real_table[experiment][1] + self.real_table[experiment][2] * math.sqrt(3)
			sigma2 =  1 / self.real_table[experiment][3] * math.sqrt(2 / math.pi)
			a2 = 1/self.real_table[experiment][4] - self.real_table[experiment][5] * math.sqrt(3)
			b2 = 1/self.real_table[experiment][4] + self.real_table[experiment][5] * math.sqrt(3)

			model = Model(0, 100, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
			y_ex_values = model.array_calculate(self.times)
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
			for factor in range (self.number_of_factors - self.p - 1, -1, -1):
				if (experiment & (1 << factor)):
					tablerow.append(-1)
				else:
					tablerow.append(1)
			for index in range (self.p):
				tablerow.append(tablerow[2 * index] * tablerow[2 * index + 1])
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
		sumdisppersion = 0
		maxdispersion = 0
		for experiment in range (self.number_of_experiments):
			sigma1 =  1 / self.real_table[experiment][0] * math.sqrt(2 / math.pi)
			a1 = 1/self.real_table[experiment][1] - self.real_table[experiment][2] * math.sqrt(3)
			b1 = 1/self.real_table[experiment][1] + self.real_table[experiment][2] * math.sqrt(3)
			sigma2 =  1 / self.real_table[experiment][3] * math.sqrt(2 / math.pi)
			a2 = 1/self.real_table[experiment][4] - self.real_table[experiment][5] * math.sqrt(3)
			b2 = 1/self.real_table[experiment][4] + self.real_table[experiment][5] * math.sqrt(3)

			model = Model(0, 100, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
			y_ex_values = model.array_calculate(self.times)
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

		sum_avg = 0
		for exp in range(self.number_of_experiments):
			sum_avg += self.real_table[exp][self.number_of_factors]
		self.koefs.append(sum_avg / self.number_of_experiments)

		for factor in range(self.number_of_factors):
			sum_avg = 0
			for exp in range(self.number_of_experiments):
				sum_avg += self.real_table[exp][self.number_of_factors] * self.real_table[exp][factor]
			self.koefs.append(sum_avg / self.number_of_experiments)


		koef_needed = [[1,3], [1, 4], [1, 6], [2, 3], [2, 4], [2, 6], [3, 5], [4, 5], [5, 6]]
		for koef in koef_needed:
			sum_avg = 0
			for exp in range(self.number_of_experiments):
				mult = self.real_table[exp][self.number_of_factors]
				for index in koef:
					mult *= self.real_table[exp][index - 1]
				sum_avg += mult
			self.koefs.append(sum_avg / self.number_of_experiments)

		index = 0
		print("Критерий Стьюдента: ", self.student_table, "\n")
		for koef_index in range(len(self.koefs)):
			koef_value = self.koefs[koef_index]
			koef_meaning = abs(koef_value)/self.Sak
			indexstr = ""
			if (index <= self.number_of_factors):
				indexstr = str(index)
			else:
				koef = koef_needed[index - self.number_of_factors - 1]
				for ind in koef:
					indexstr += str(ind)
			if (koef_meaning >= self.student_table):
				self.meaningful_koefs += 1
				print("a", indexstr,"*", koef_value, "✓")
			else:
				print("a", indexstr,"*", koef_value)
				self.koefs[koef_index] = 0
			index += 1

	def calculate_partly_nonlinear(self, factors):
		self.allkoefs = self.koefs[:self.number_of_factors+1]
		a13 = self.koefs[self.number_of_factors + 1] / 4
		a14 = self.koefs[self.number_of_factors + 2] / 4
		a16 = self.koefs[self.number_of_factors + 3] / 4
		a23 = self.koefs[self.number_of_factors + 4] / 4
		a24 = self.koefs[self.number_of_factors + 5] / 4
		a26 = self.koefs[self.number_of_factors + 6] / 4
		a35 = self.koefs[self.number_of_factors + 7] / 4
		a45 = self.koefs[self.number_of_factors + 8] / 4
		a56 = self.koefs[self.number_of_factors + 9] / 4

		rest_koefs = [0, a13, a14, 0, a16, a23, a24, 0, a26, 0, a35, 0, a45, 0, a56, a35, a45, 0, a56, a16, a23, a14, a24, a13, a26, a26, a13, a24, a14, a23, a16, a56, 0, a45, a35, a56, 0, a45, 0, a35, 0, a26, 0, a24, a23, a16, 0, a14, a13, 0, 0, 0, 0, 0, 0, 0, 0]
		self.allkoefs += rest_koefs
		result = self.allkoefs[0]

		koef_index = 1
		for i in range (1, len(factors) + 1):
			for j in combinations(factors, i):
				mult = self.allkoefs[koef_index]
				for k in range(i):
					mult *= j[k]
				result += mult
				koef_index += 1
		return result

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

def getdotbyprop(pfe, dfe):
	x1_min = pfe.factors[0][0]
	x1_max = pfe.factors[0][1]
	x2_min = pfe.factors[1][0]
	x2_max = pfe.factors[1][1]
	x3_min = pfe.factors[2][0]
	x3_max = pfe.factors[2][1]
	x4_min = pfe.factors[3][0]
	x4_max = pfe.factors[3][1]
	x5_min = pfe.factors[4][0]
	x5_max = pfe.factors[4][1]
	x6_min = pfe.factors[5][0]
	x6_max = pfe.factors[5][1]

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

	x1 = get_value(x1_min, x1_max, x1_prop)
	x2 = get_value(x2_min, x2_max, x2_prop)
	x3 = get_value(x3_min, x3_max, x3_prop)
	x4 = get_value(x4_min, x4_max, x4_prop)
	x5 = get_value(x5_min, x5_max, x5_prop)
	x6 = get_value(x6_min, x6_max, x6_prop)

	sigma1 =  1 / x1 * math.sqrt(2 / math.pi)
	a1 = 1/x2 - x3 * math.sqrt(3)
	b1 = 1/x2 + x3 * math.sqrt(3)
	sigma2 =  1 / x4 * math.sqrt(2 / math.pi)
	a2 = 1/x5 - x6 * math.sqrt(3)
	b2 = 1/x5 + x6 * math.sqrt(3)

	model = Model(0, 100, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
	y_avg = model.calculate(5)
	y_linear = pfe.calculate_linear([x1, x2, x3, x4, x5, x6])
	y_nonlinear = pfe.calculate_partly_nonlinear([x1, x2, x3, x4, x5, x6])

	y_linear_d = dfe.calculate_linear([x1, x2, x3, x4, x5, x6])
	y_nonlinear_d = dfe.calculate_partly_nonlinear([x1, x2, x3, x4, x5, x6])

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
	x1_min = 0.1
	x1_max = 0.2

	x2_min = 0.6
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

	print ("PFE")
	pfe = PFE(min_max_factors, times)
	pfe.fill_experiment_data()
	pfe.printtable()
	pfe.fill_calculated_data()
	pfe.printtable()
	pfe.check_adequacy()

	print ("DFE")
	dfe = DFE(min_max_factors, times, 2)
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
