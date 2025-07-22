#厚労科研を年度ごとにスプリット
import pandas as pd
import os

input_file="/Users/kuramotomana/Test/20250519-厚労科研.csv"

ouput_dir="split_by_year"
os.makedirs