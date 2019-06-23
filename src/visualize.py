import os
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import datetime
from dateutil import relativedelta
import numpy as np
import calc

def format_axis(fig, ax, datetimes):
    ax.grid()
    days_margin = relativedelta.relativedelta(days=3)
    ax.set_xlim([datetimes[0]-days_margin, datetimes[-1]+days_margin])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    fig.autofmt_xdate(rotation=90)    
    return fig, ax

def draw_candlestick(df, path=None):
    nums_date = mdates.date2num(df.index).reshape(-1, 1)
    mat_ohlc = df[["start", "high", "low", "end"]].values
    mat_ohlc = np.concatenate([nums_date, mat_ohlc], axis=1)
    fig, ax = plt.subplots(figsize=(16, 8))
    ax = candlestick(ax, mat_ohlc)
    fig, ax = format_axis(fig, ax, df.index)
    if path is not None:
        fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return

def draw_indicators(df, indicators, path):
    fig, ax = plt.subplots(figsize=(16, 8))
    for ind in indicators:
        ax.plot(df.index, df[ind], label=ind)
    ax.legend()
    fig, ax = format_axis(fig, ax, df.index)
    if path is not None:
        fig.savefig(path, bbox_inches='tight')
    plt.close(fig)

def candlestick(ax, quotes, width=0.2, colorup='k', colordown='r', alpha=1.0):

    OFFSET = width / 2.0

    for q in quotes:
        
        t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(xdata=(t, t), ydata=(low, high),
                       color=color, linewidth=0.5, antialiased=True)

        rect = Rectangle(xy=(t - OFFSET, lower),
                         width=width, height=height,
                         facecolor=color, edgecolor=color)
        
        rect.set_alpha(alpha)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()
    
    ax.plot(quotes[:, 0], calc.calc_avg_exp(quotes[:, -1], 12), 
            label="exponential moving average over 12 days")
    ax.plot(quotes[:, 0], calc.calc_avg_exp(quotes[:, -1], 26), 
            label="exponential moving average over 26 days")
    ax.legend()    
    return ax