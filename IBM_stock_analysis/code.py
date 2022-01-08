import os

import pandas as pd

import numpy as np

from scipy import stats

import matplotlib.pyplot as plt

from distfit import distfit # From the distfit library import the class distfit



# Question 5

import quandl

import datetime

start = datetime.datetime(1962,1,1)

end = datetime.date.today()

stock = quandl.get("WIKI/IBM", start_date=start, end_date=end)

stock["Close"].head()



# Questions 1-2

############################## Import CSV to DF ###############################

os.chdir("C:/Documents/Giorgos/Python/Data")

df = pd.read_csv('IBM.csv', sep=',')

df['Cloce_pct'] = 100*df['Close'].pct_change()

############################## Export DF to CSV ###############################

df.to_csv('IBM_pct.csv', index=False) # CSV export

###############################################################################

# Import data from CSV

data = 100*df['Cloce_pct'].dropna()

# Import data from quandl

data = 100*stock['Close'].pct_change().dropna()



# Question 4 & 5

#####################   Fitting Best Distribution #############################

# Retrieve P-value for y

y = [0,10,45,55,100]

# Initialize.

# Set any properties here, such as alpha.

# The smoothing can be of use when working with integers. Otherwise your histogram

# may be jumping up-and-down, and getting the correct fit may be harder.

dist = distfit(alpha=0.05, smooth=10)

# Search for best theoretical fit on your empirical data

dist.fit_transform(data)

# Best fitted model

best_distr = dist.model

print(best_distr)

# Ranking distributions

dist.summary

# Plot the summary of fitted distributions

dist.plot_summary()

###############################################################################



# Questions 3 & 5

##############   Histogram and Density Function of Best Fitting   #############

#mu, std= norm.fit(data)# Μοντελοποίησημε μια κανονική κατανομή

ab,bb,cb,db = stats.beta.fit(data)

plt.hist(data, bins=25, density=True, alpha=0.3, color='g')

xmin, xmax= plt.xlim() # όρια του άξονα x

x = np.linspace(xmin, xmax, 1000)

#p = norm.pdf(x, mu, std)

pdf_beta = stats.beta.pdf(x, ab, bb,cb, db)

plt.plot(x, pdf_beta, 'k', linewidth=2)

title = "Fit results: aa = %.2f, bb %.2f, cb = %.2f, db %.2f"  % (ab, bb,cb, db)

plt.title(title)
