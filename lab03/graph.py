import model
import math
import matplotlib.pyplot as plt

def getGraph():
	print("loadness,", "x1,", "x2,", "x3,", "x4,", "x5,", "x6,", "sigma1,", "a1,", "b1,", "sigma2,", "a2,", "b2,", "avg_await_time")
	start_time = 0
	stop_time = 20
	times = 5

	x1 = 0.1
	while x1 < 5:
		x2 = 0.1
		while x2 < 5:
			x3 = 0.1
			while x3 < 5:
				x4 = 0.1
				while x4 < 5:
					x5 = 0.1
					while x5 < 5:
						x6 = 0.1
						while x6 < 5:
							ro = (x1 + x4) / (x2 + x5)
							sigma1 =  1 / x1 * math.sqrt(2 / math.pi)
							a1 = 1/x2 - x3 * math.sqrt(3)
							b1 = 1/x2 + x3 * math.sqrt(3)
							sigma2 =  1 / x4 * math.sqrt(2 / math.pi)
							a2 = 1/x5 - x6 * math.sqrt(3)
							b2 = 1/x5 + x6 * math.sqrt(3)
							if (ro <= 1):
								if (a1 >= 0 and b1 >= 0 and a1 < b1 and sigma1 >= 0 and a2 >= 0 and b2 >= 0 and a2 < b2 and sigma2 >= 0):
									m = model.Model(start_time, stop_time, [[sigma1, a1, b1], [sigma2, a2, b2]], 1)
									avg_wait_time = m.calculate(times)
									if (avg_wait_time < 0):
										avg_wait_time = m.calculate(times)
									if (avg_wait_time < 0):
										avg_wait_time = m.calculate(times)
									if (avg_wait_time < 0):
										avg_wait_time = m.calculate(times)
									if (avg_wait_time >= 0):
										print(ro, ",", x1, ",", x2, ",", x3, ",", x4, ",", x5, ",", x6, ",", sigma1, ",", a1, ",", b1, ",", sigma2, ",", a2, ",", b2, ",", avg_wait_time)
							x6 += 0.5
						x5 += 0.5
					x4 += 0.5
				x3 += 0.5
			x2 += 0.5
		x1 += 0.5

getGraph()
