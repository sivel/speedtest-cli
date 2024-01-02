import logging
import os
import shutil
import time
import csv
import json


def remove_directory(directory_path, n=100):
    directory_path = str(directory_path)
    if os.path.islink(directory_path):
        os.unlink(directory_path)
    elif os.path.exists(directory_path):
        deleted = False
        for i in range(0, n - 1):
            try:
                shutil.rmtree(directory_path, onerror=on_error)
                deleted = True
                break

            except OSError as err:
                logging.error(
                    "Error while deleting directory {}, on attempt number {}: {}. Retrying...".format(
                        directory_path, i, err.strerror
                    )
                )
                time.sleep(1)

        if not deleted:
            shutil.rmtree(directory_path, onerror=on_error)


def on_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=on_error)``
    """
    import stat

    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def make_directory(directory_path):
    directory_path = str(directory_path)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def make_clean_directory(directory_path):
    directory_path = str(directory_path)
    remove_directory(directory_path)
    while os.path.exists(directory_path):
        pass
    make_directory(directory_path)
    while not os.path.exists(directory_path):
        pass


def delete_file(file):
    file = str(file)
    if os.path.exists(file):
        os.remove(file)


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
