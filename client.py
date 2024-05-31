import sys
import requests
import threading
import time
from queue import Queue


class Client:
    def __init__(self, input_path, addresses_path, output_path):
        self.input_path = input_path
        self.addresses_path = addresses_path
        self.output_path = output_path
        self.input_data = self.read_file(self.input_path)
        self.proxy_addresses = self.read_file(self.addresses_path)
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.threads = []

    # Util functions to read/write
    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]

    def write_output(self, data):
        with open(self.output_path, 'a') as file:
            file.write(data + '\n')

    # function that makes the request and checks the response
    def fetch_information(self, proxy_url, input_str):
        try:
            response = requests.get(proxy_url)
            if response.status_code == 200:
                information = response.json().get("information", "")
                self.output_queue.put((input_str, information))
            elif response.status_code == 503:
                # Retry logic can be added here if needed
                pass
        except Exception as e:
            print(f"Request to {proxy_url} with data {input_str} failed: {e}")

    # Worker thread function to process items from the input queue using proxy addresses.
    def worker(self):
        while not self.input_queue.empty():
            input_str = self.input_queue.get()
            proxy_url = self.proxy_addresses.pop(0)
            self.proxy_addresses.append(proxy_url)
            self.fetch_information(proxy_url, input_str)
            self.input_queue.task_done()

    def start_threads(self):
        for i in range(len(self.proxy_addresses) * 30):
            thread = threading.Thread(target=self.worker)
            thread.start()
            self.threads.append(thread)
            time.sleep(0.1)  # Small delay to prevent all threads from starting simultaneously

    # Process output queue and write results to the output file.
    def process_output(self):
        while any(thread.is_alive() for thread in self.threads) or not self.output_queue.empty():
            try:
                input_str, information = self.output_queue.get(timeout=1)
                self.write_output(f"{input_str} {information}")
                self.output_queue.task_done()
            except Exception:
                pass

    def join_threads(self):
        for thread in self.threads:
            thread.join()

    def run(self):
        for item in self.input_data:
            self.input_queue.put(item)

        self.start_threads()
        self.process_output()
        self.join_threads()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py <input> <addresses> <output>")
        sys.exit(1)

    input_path = sys.argv[1]
    addresses_path = sys.argv[2]
    output_path = sys.argv[3]

    client = Client(input_path, addresses_path, output_path)
    client.run()
