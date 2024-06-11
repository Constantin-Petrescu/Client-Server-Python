# Client-Server Python

## Overview

This project implements a concurrent client that reads input data from a file, fetches information from a list of proxy addresses, and writes the fetched information to an output file. 

## File Structure

- `client.py`: Contains the `Client` class which implements the core functionality.
- `test_client.py`: Contains the unit tests for the `Client` class.
- `README.md`: Project documentation.

## Usage

### Building the dependencies

To install, use `pip install requests` or `pip install -r requirements.txt`. The code was developed on MacOS, with Python3.11, and uses requests library as a dependency.

### Running the Client

Added option `-h` and argv parse for the client. Included two optional line arguments with number of retries per query (default 5) and per server (default 30). To run the client, use the following command:

```console
python proxy_client.py <input_file_path> <addresses_file_path> <output_file_path>
```

The tests currently provide one/two warnings (`RuntimeWarning: coroutine was not awaited` and a `DeprecationWarning`). But, the execution works fine and all the tests are passed. To run the unit tests, use the following command:

```console
python -m unittest test_client.py 
```





Explanation of Tests:
test_read_file: Verifies that the read_file method correctly reads and processes input and addresses files.
test_write_output: method correctly writes a given string to the specified output file.
test_fetch_information: method correctly processes a successful 200 HTTP response.
test_fetch_with_retries: method retries the correct number of times and successfully retrieves data.
test_fetch_information_404: method correctly handles a 404 Not Found HTTP response.
test_fetch_information_503: method handles a 503 Service Unavailable HTTP response by indicating that a retry is needed.