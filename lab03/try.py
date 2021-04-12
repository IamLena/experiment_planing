from itertools import combinations

s = []
for i in range (5):
	s.append(i + 1)
print (s)

for i in range (5):
	for j in combinations(s, i):
		print(j, end=' ') # ab ac ad bc bd cd

