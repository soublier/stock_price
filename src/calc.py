import numpy as np

def calc_macd(v, n_short=12, n_long=26):
    v_avg_short = calc_avg_exp(v, n_short)        
    v_avg_long = calc_avg_exp(v, n_long)
    v_macd = v_avg_short - v_avg_long
    return v_macd

def calc_signal(v, n_signal=9, n_short=12, n_long=26):
    v_macd = calc_macd(v, n_short, n_long)
    v_signal = calc_avg_exp(v_macd, n_signal)
    return v_signal
    
def calc_D_slow(v, n_K=5, n_D=3, n_D_slow=3):
    v_D = calc_D(v, n_K, n_D)
    v_D_slow = calc_avg_simple(v_D, n_D_slow)
    return v_D_slow

def calc_D(v, n_K=5, n_D=3):
    v_K_numer = np.zeros_like(v, dtype="float32")
    v_K_denom = np.zeros_like(v, dtype="float32")
    for i in range(len(v)):
        if i < n_K-1:
            v_K_numer[i] = np.nan
            v_K_denom[i] = np.nan
        else:
            v_over_n_K = v[i-(n_K-1):i+1]
            v_K_numer[i] = v[i] - np.min(v_over_n_K)
            v_K_denom[i] = np.max(v_over_n_K) - np.min(v_over_n_K)
    v_K_numer_avg = calc_avg_simple(v_K_numer, n_D)
    v_K_denom_avg = calc_avg_simple(v_K_denom, n_D)
    v_K = 100 * v_K_numer_avg / v_K_denom_avg
    return v_K

def calc_avg_simple(v, n):
    v_avg = np.zeros_like(v, dtype="float32")
    for i in range(len(v)):
        if i < n-1:
            v_avg[i] = np.nan
        else:
            v_over_n = v[i-(n-1):i+1]
            if np.isnan(v_over_n).any():
                v_avg[i] = np.nan
            else:
                v_avg[i] = np.mean(v_over_n)
    return v_avg

def calc_avg_exp(v, n):
    v_avg = np.zeros_like(v, dtype="float32")
    for i in range(len(v)):
        if i < n-1:
            v_avg[i] = np.nan
        else:
            v_over_n = v[i-(n-1):i+1]
            if np.isnan(v_over_n).any():
                v_avg[i] = np.nan
            else:
                if np.isnan(v_avg[i-1]):
                    v_avg[i] = np.mean(v_over_n)
                else:
                    v_avg[i] = (2*v[i] + (n-1)*v_avg[i-1]) / (n+1)
    return v_avg