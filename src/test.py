# test.py

from helpers import dat_line_to_data, read_log_to_df

df, meta, continues = read_log_to_df("./tests/test_data/test_data_all_good_lines.log")

print(df)
print(df.iloc[0])
print(type(df.iloc[0]))


dat_line = "8.548-1-72C0BCE#D23A266161"

line_data = dat_line_to_data(dat_line)

print(line_data)