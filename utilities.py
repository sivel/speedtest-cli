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

# Sample input string
sample_input = "{'download': 0, 'upload': 0, 'ping': 9.319, 'server': {'url': 'http://speedtest.nextgentel.no:8080/speedtest/upload.php', 'lat': '59.9494', 'lon': '10.7564', 'name': 'Oslo', 'country': 'Norway', 'cc': 'NO', 'sponsor': 'NextGenTel AS', 'id': '8018', 'host': 'speedtest.nextgentel.no:8080', 'd': 5.7463776547060155, 'latency': 9.319}, 'timestamp': '2024-01-01T20:06:56.839888Z', 'bytes_sent': 0, 'bytes_received': 0, 'share': None, 'client': {'ip': '84.215.59.36', 'lat': '59.955', 'lon': '10.859', 'isp': 'Telia Norge AS', 'isprating': '3.7', 'rating': '0', 'ispdlavg': '0', 'ispulavg': '0', 'loggedin': '0', 'country': 'NO'}}"

# Specify the file name
file_name = "output.xlsx"

# Call the function with the sample input and file name
convert_and_save_to_xlsx(sample_input, file_name)


# py .\speedtest.py --csv