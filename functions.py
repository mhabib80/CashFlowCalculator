import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker


def sigmoid(x, k=3.627412246682911, b=-0.001164921989173435):
  return 1 / (1 + np.exp(-k*(x-b)))


def curve(p_name, contract_amount, start_date, completion_date,  curve, csrf=None):

    date_range = pd.date_range(start_date, completion_date, freq='d')  # date range per day
    dur = (date_range.max() - date_range.min()).days

    if curve == 'trapezoidal':
        sigmoid_input = np.linspace(-1.1, 1.1, dur + 1) #adjust the x values to better fit the S-Curve function
        x = sigmoid(sigmoid_input)

    else:
        x = np.linspace(0, 1, dur + 1)

    cum_earnings = (x * contract_amount).ravel()
    data = pd.DataFrame(cum_earnings, index=date_range, columns=['cum_earnings'])
    data.iloc[0] = 0
    # data.iloc[-1] = contract_amount  # last period should be 100% contract amount
    output = data.resample('M').cum_earnings.max().astype(int).to_frame()
    output[p_name + '_Monthly'] = output['cum_earnings'].diff().fillna(output['cum_earnings']) #so 1st period won't be NaN
    output.drop('cum_earnings', inplace=True, axis=1)
    return output


def plot_chart():
    df = pd.read_csv('tmp/df.csv', index_col=[0])
    ax = df.iloc[:, :-2].plot(kind='bar', stacked=True, figsize=(20, 15),
                              color=['#06283D', '#1363DF', '#47B5FF', '#FF6D02', '#7577CD'])
    ax2 = df['Cum_Monthly'].plot(c='red', ax=ax, secondary_y=True, legend=True, label='Cum_Monthly')
    ax.legend(loc='upper left', frameon=False, ncol=len(df.columns))
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax2.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.savefig('static/chart.png')


# Set Matplot parameters
plt.rcParams['text.color'] = 'black'
plt.rcParams['axes.labelcolor']='black'
plt.rcParams['axes.edgecolor']='black'
plt.rcParams['axes.linewidth']=0.5
plt.rcParams['xtick.color']='grey'
plt.rcParams['ytick.color']='grey'
plt.rc('axes.spines', top=False, right=False)
plt.rcParams['axes.grid.axis'] = 'x'
plt.rcParams['axes.xmargin'] = 0.01
plt.rcParams['axes.grid.axis'] = 'y'
plt.rcParams['figure.figsize'] = 20,10
plt.rcParams['axes.titlelocation']= 'left'
plt.rcParams['axes.titlepad'] = 10




