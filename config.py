import os
import itertools
from numpy.random import seed as seed_np
from tensorflow import set_random_seed as seed_tf
from time import time
from datetime import datetime
import logging
import warnings
import pandas


# ----------------------------------
# Reproducibility
# ----------------------------------
random_seed = int(time()*10000) % 2**31
seed_np(random_seed)
seed_tf(random_seed)

# ----------------------------------
# Data Preparation
# ----------------------------------
option_type = 'call'
start_year = 2010
end_year = 2016
annualization = 252
stock_count_to_pick = 6
do_redownload_all_data = False

overlapping_windows = True
limit_windows = 'final-testing'  # one of ['single', 'hyper-param-search', 'final-testing', 'no', 'mock-testing']
use_big_time_windows = False

fundamental_columns_to_include = [
    'permno',
    'public_date',
    'ffi49',
    'roa',
    'capital_ratio',
    'pe_op_dil'
]

# ----------------------------------
# Feature Selection
# ----------------------------------
ff_dummies = ['ff_ind_{}'.format(i) for i in range(49)]

mandatory_features = ['days', 'moneyness']
optional_features = ['r', 'v60', 'vix', 'returns', 'roa', 'capital_ratio', 'pe_op_dil']

full_feature_combination_list = []
include_only_single_features = False
for i in range(len(optional_features) + 1):
    if not include_only_single_features or i <= 1:
        for feature_tuple in list(itertools.combinations(optional_features, i)):
            feature_selection = mandatory_features + list(feature_tuple)
            full_feature_combination_list.append(feature_selection)

full_feature_combination_list = [mandatory_features]  # (None)
full_feature_combination_list += [mandatory_features+[feature] for feature in optional_features]  # Singles
full_feature_combination_list += [mandatory_features + ['r', 'vix']]  # BS-like
full_feature_combination_list += [mandatory_features + optional_features]  # (All)
active_feature_combinations = list(range(len(full_feature_combination_list)))


# ----------------------------------
# Hyperparameters
# ----------------------------------
epochs = 250
loss_func = 'mse'
# if required_precision is not reached during initial training, the run is declared "failed"
# only relevant during initial experimentation phase
if loss_func == 'mape':
    required_precision = 10**5
elif loss_func == 'mse':
    required_precision = 0.01
elif loss_func == 'mae':
    required_precision = 0.1
else:
    raise ValueError

separate_initial_epochs = int(epochs / 10)
lr = None  # 0.0001
batch_normalization = False
multi_target = False
useEarlyStopping = False

identical_reruns = 1

activations = ['relu']
number_of_nodes = [250]
number_of_layers = [3]
optimizers = ['adam']
include_synthetic_datas = [True, False]
dropout_rates = [0.1]
batch_sizes = [500]   # 100,
normalizations = ['mmscaler']  # 'no', 'rscaler', 'sscaler',
regularizers = [None]  # 'l1', 'l2', None

if limit_windows == 'mock-testing':
    epochs = 10
    separate_initial_epochs = 1
    required_precision = 100
    number_of_layers = [2]
    number_of_nodes = [25]

settings_list = [
    activations,
    number_of_nodes,
    number_of_layers,
    optimizers,
    include_synthetic_datas,
    dropout_rates,
    normalizations,
    batch_sizes,
    regularizers,
    active_feature_combinations
]

settings_combi_count = 1
for setting_options in settings_list:
    settings_combi_count *= len(setting_options)

# ----------------------------------
# Benchmark
# ----------------------------------
run_BS = 'yes'  # 'yes', 'no', only_BS'
vol_proxies = ['surface', 'hist_realized']  # , hist_implied
cd_of_quotes_to_consider_for_vol_surf = 7

# ----------------------------------
# Local file paths
# ----------------------------------
if os.path.isdir('D:/'):
    rootpath = "D:\\AlgoTradingData\\"
    localpath = "D:\\Dropbox\\Studium\\Master\\Thesis\\neuralnet"
    onCluster = False
elif os.path.isdir('/scratch/roklemm/option-pricing/sebbl_upload'):
    rootpath = '/scratch/roklemm/option-pricing/sebbl_upload'
    localpath = '/scratch/roklemm/option-pricing/sebbl_upload'
    onCluster = True
else:
    rootpath = "C:\\AlgoTradingData\\"
    localpath = "C:\\Dropbox\\Dropbox\\Studium\\Master\\Thesis\\neuralnet"
    onCluster = False

paths = {
    'results-excel': os.path.join(localpath, 'results_excel.xlsx'),
    'results-excel-BS': os.path.join(localpath, 'results_excel-BS.xlsx'),
    'data_for_latex': os.path.join(rootpath, "data_for_latex.h5"),
    'options_for_ann': os.path.join(rootpath, "options_for_ann.h5"),
    'weights': os.path.join(rootpath, "weights.h5"),
    'neural_net_output': os.path.join(rootpath, "ANN-output.h5"),
    'model_overfit': os.path.join(rootpath, "overfit_model.h5"),
    'model_mape': os.path.join(rootpath, "mape_model.h5"),
    'model_deep': os.path.join(rootpath, "deep_model.h5"),
    'model_best': os.path.join(rootpath, "model_currently_best.h5"),
    'gradients_data': os.path.join(rootpath, 'gradients_data.h5'),
    'prices_raw': os.path.join(rootpath, "prices.h5"),
    'merged': os.path.join(rootpath, "merged.h5"),
    'all_options_h5': os.path.join(rootpath, "all_options.h5"),
    'treasury': os.path.join(rootpath, '3months-treasury.h5'),
    'vix': os.path.join(rootpath, 'vix.h5'),
    'dividends': os.path.join(rootpath, 'dividends.h5'),
    'ratios': os.path.join(rootpath, 'ratios.h5'),
    'names': os.path.join(rootpath, 'names.h5'),
    'sp500_permnos': os.path.join(rootpath, 'SP500_permnos.csv'),
    'sample_model': os.path.join(rootpath, 'all_models', 'sample_model.h5'),
    'sample_data': os.path.join(rootpath, 'all_models', 'sample_data.h5'),
    'all_models': os.path.join(rootpath, 'all_models', '{:%Y-%m-%d_%H-%M}'.format(datetime.now())),
    'options': [
        os.path.join(rootpath, "OptionsData", "rawopt_" + str(y) + "AllIndices.csv") for y in (start_year, end_year)
    ]
}

# ----------------------------------
# Output for Latex
# ----------------------------------
saveResultsForLatex = True
collect_gradients_data = True

# ----------------------------------
# Disabling certain Warnings
# ----------------------------------
logging.getLogger("tensorflow").setLevel(logging.WARNING)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore', category=pandas.io.pytables.PerformanceWarning)
