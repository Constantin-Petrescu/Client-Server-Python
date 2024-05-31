# Client-Server Python

## Overview

This project implements a multi-threaded client that reads input data from a file, fetches information from a list of proxy addresses, and writes the fetched information to an output file. 

## File Structure

- `client.py`: Contains the `Client` class which implements the core functionality.
- `test_client.py`: Contains the unit tests for the `Client` class.
- `server.py`: Contains the proxy server that replies to the client with the data
- `README.md`: Project documentation.

## Usage

### Building the dependencies

To install, use `pip install requests` or `pip install -r requirements.txt`. The code was developed on MacOS, with Python3.11, and uses requests library as a dependency.

### Running the Client

To run the client, use the following command:

```console
python proxy_client.py <input_file_path> <addresses_file_path> <output_file_path>
```

To run the unit tests, use the following command:
```console
python -m unittest test_client.py 
```

To run the server , use the following command:
```console
python server <responses path> 
```
The path towards responses is optional as the server has two hardcoded outputs 



