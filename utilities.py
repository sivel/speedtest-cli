import os
import ast
import pandas as pd


def write_to_csv(input_str):
    # Convert single quotes to double quotes for valid JSON
    input_str = input_str.replace("'", "\"")

    # Convert the input string to a dictionary
    input_dict = eval(input_str)

    # Extract keys for the header row
    header = []
    for key, value in input_dict.items():
        if isinstance(value, dict):
            header.extend([f"{key}_{subkey}" for subkey in value.keys()])
        else:
            header.append(key)

    # Extract values for the data row
    values = []
    for key, value in input_dict.items():
        if isinstance(value, dict):
            values.extend(value.values())
        else:
            values.append(value)

    # Write to CSV
    with open('output.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(header)
        csv_writer.writerow(values)


def convert_and_save_to_xlsx(data_str, file_name):
    # Try to open the Excel file
    try:
        df = pd.read_excel(file_name)
    except IOError:
        # File doesn't exist, create a new one
        df = pd.DataFrame()

    # Convert the input string to a dictionary
    data_dict = ast.literal_eval(data_str)

    # Flatten the nested dictionaries
    flattened_data = flatten_dict(data_dict)

    # Append the flattened data to the DataFrame
    df = df._append(pd.DataFrame(flattened_data, index=[0]), ignore_index=True)

    # Save the DataFrame to an Excel file
    df.to_excel(file_name, index=False)

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a nested dictionary by joining keys with a separator.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
