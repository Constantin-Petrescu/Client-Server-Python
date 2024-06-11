import argparse
import asyncio
import os
from random import randrange

import aiohttp
import aiofiles
import async_timeout

import sys
import requests
import threading
import time
from queue import Queue


class Client:
    def __init__(self, input_path, addresses_path, output_path, concurent_req=30, retries=5):
        """
        Initialize the Client with paths to input, proxy addresses, and output files.
        default value for concurent_req 30 and max retries 5
        """
        self.input_path = input_path
        self.addresses_path = addresses_path
        self.output_path = output_path
        self.input_data = self.read_file(self.input_path)
        self.proxy_addresses = self.read_file(self.addresses_path)
        self.tasks = []
        self.CONCURRENT_REQUESTS_PER_PROXY = concurent_req
        self.semaphores = {proxy: asyncio.Semaphore(concurent_req) for proxy in self.proxy_addresses}
        self.MAX_RETRIES = retries

    """
    Util functions to read/append data on files
    """
    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]

    def write_output(self, data):
        with open(self.output_path, 'a') as file:
            file.write(data + '\n')

    async def fetch_information(self, session, proxy_url, params):
        """
        Fetch information from the proxy URL with the given parameters.
        Handle different HTTP response codes accordingly.
        Behaviour for 404 is not specified, thus we decided to retry it; after failed retries, log is printed on stderr
        """
        async with async_timeout.timeout(5):
            async with session.get(f"{proxy_url}/api/data", params=params) as response:
                print(response)
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return '404 Not Found' # Retry the request
                elif response.status == 503:
                    return None  # Retry the request
                else:
                    raise Exception(f"Unexpected status code {response.status}")

    async def fetch_with_retries(self, session, params):
        """
        Attempt to fetch information up to self.MAX_RETRIES times.
        """
        for _ in range(self.MAX_RETRIES):
            print(len)
            proxy_url = self.proxy_addresses[randrange(len(self.proxy_addresses))]
            async with self.semaphores[proxy_url]:
                try:
                    result = await self.fetch_information(session, proxy_url, params)
                    if result is not None:
                        return result
                except Exception as e:
                    print(f"Request failed for {params['input']} at {proxy_url}: {e}", file=sys.stderr)
        return None

    async def worker(self, inputs):
        """
        Worker coroutine to process input strings, fetch data, and write results to the output file.
        """
        conn = aiohttp.TCPConnector(limit_per_host=30)
        async with aiohttp.ClientSession(trust_env=True, connector=conn) as session:
            while not inputs.empty():
                input_str = await inputs.get()
                params = {'input': input_str}
                try:
                    result = await self.fetch_with_retries(session, params)
                    if result:
                        if result == '404 Not Found':
                            print(f"No data found for {input_str} after {self.MAX_RETRIES} retries (404 Not Found)",
                                  file=sys.stderr)
                        else:
                            async with aiofiles.open(self.output_path, 'a') as f:
                                await f.write(f"{input_str} {result['information']}\n")

                except Exception as e:
                    print(f"Failed to fetch data for {input_str}: {e}", file=sys.stderr)

                inputs.task_done()

    async def run(self):
        # Create a queue for input strings
        inputs = asyncio.Queue()
        for input_str in self.input_data:
            await inputs.put(input_str)

        # Create a list of tasks for each proxy address
        for _ in range(self.CONCURRENT_REQUESTS_PER_PROXY):
            task = asyncio.create_task(self.worker(inputs))
            self.tasks.append(task)

        # Run all tasks
        await asyncio.gather(*self.tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concurrent HTTP requests to proxies.")
    parser.add_argument('input_file', type=str, help="Path to the input file containing the strings.")
    parser.add_argument('addresses_file', type=str,
                        help="Path to the file containing the proxy addresses.")
    parser.add_argument('output_file', type=str, help="Path to the output file.")
    parser.add_argument('--max-retries', type=int, default=5,
                        help="Maximum number of retries for each request (default: 5).")
    parser.add_argument('--max-proxy-servers', type=int, default=30,
                        help="Maximum number of concurrent requests for proxy (default: 30).")

    args = parser.parse_args()

    input_file = args.input_file
    addresses_file = args.addresses_file
    output_file = args.output_file
    max_retries = args.max_retries
    max_proxy = args.max_proxy_servers

    # if not os.path.isabs(input_file) or not os.path.isabs(addresses_file) or not os.path.isabs(output_file):
    #     print("All file paths must be absolute", file=sys.stderr)
    #     sys.exit(1)

    client = Client(input_file, addresses_file, output_file, max_retries, max_proxy)
    asyncio.run(client.run())
