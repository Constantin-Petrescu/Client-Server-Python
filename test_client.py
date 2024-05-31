import unittest
from unittest.mock import patch, MagicMock
import threading
import os
from client import Client


class TestClient(unittest.TestCase):
    # Setup of the unit test class for Scraper class
    def setUp(self):
        self.input_path = 'test_input.txt'
        self.addresses_path = 'test_addresses.txt'
        self.output_path = 'test_output.txt'

        # Create test input file
        with open(self.input_path, 'w') as file:
            file.write("test_input_1\n")
            file.write("test_input_2\n")

        # Create test addresses file
        with open(self.addresses_path, 'w') as file:
            file.write("http://localhost:8080\n")

        # Ensure output file is empty
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    # Clean up test files after test execution
    def tearDown(self):
        os.remove(self.input_path)
        os.remove(self.addresses_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    #         Test the write_output method.
    def test_write_output(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        client.write_output("test_output")

        with open(self.output_path, 'r') as file:
            lines = file.read().splitlines()
            last_line = lines[-1]
            self.assertEqual(last_line, "test_output")

    #         Test the fetch_information method.
    @patch('requests.get')
    def test_fetch_information(self, mock_get):
        client = Client(self.input_path, self.addresses_path, self.output_path)

        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"information": "test_information"}
        mock_get.return_value = mock_response

        client.fetch_information("http://localhost:8080", "test_input_1")

        result = client.output_queue.get()
        self.assertEqual(result, ("test_input_1", "test_information"))

    # Test the worker method.
    def test_worker(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        client.input_queue.put("test_input_1")
        client.proxy_addresses = ["http://localhost:8080"]

        with patch.object(client, 'fetch_information') as mock_fetch:
            mock_fetch.return_value = None
            client.worker()

            mock_fetch.assert_called_once_with("http://localhost:8080", "test_input_1")

    #         Test the start_threads method.
    def test_start_threads(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        client.input_queue.put("test_input_1")

        with patch.object(threading.Thread, 'start') as mock_start:
            client.start_threads()

            self.assertEqual(mock_start.call_count, len(client.proxy_addresses) * 30)

    # Test to ensure that no more than 30 threads are started at the same time.
    @patch('threading.Thread.start')
    def test_no_more_than_30_threads(self, mock_start):
        client = Client(self.input_path, self.addresses_path, self.output_path)

        # Mocking the input queue to simulate enough data
        for i in range(100):
            client.input_queue.put(f"test_input_{i}")

        client.start_threads()

        # Check if the start method of threading.Thread was called no more than 30 times
        self.assertTrue(mock_start.call_count <= 30,
                        f"Expected <= 30 threads, but started {mock_start.call_count} threads.")

    #         Test the process_output method.
    def test_process_output(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        client.output_queue.put(("test_input_1", "test_information"))

        with patch.object(client, 'write_output') as mock_write:
            with patch.object(threading.Thread, 'is_alive', return_value=False):
                client.process_output()
                mock_write.assert_called_once_with("test_input_1 test_information")
                self.assertEqual(client.output_queue.qsize(), 0, "The output queue should be empty after processing.")

    # Test the join_threads method.
    def test_join_threads(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        mock_thread = MagicMock()
        client.threads = [mock_thread]

        client.join_threads()

        mock_thread.join.assert_called_once()
        self.assertEqual(mock_thread.join.call_count, 1, "Each thread should be joined exactly once.")

    def test_run(self):
        client = Client(self.input_path, self.addresses_path, self.output_path)
        client.run()

        # Check if output file has been created and has content
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'r') as file:
            lines = file.readlines()
            self.assertTrue(len(lines) > 0, "The output file is missing after a run")

        with patch.object(client, 'start_threads') as mock_start_threads, \
                patch.object(client, 'process_output') as mock_process_output, \
                patch.object(client, 'join_threads') as mock_join_threads:
            client.run()

            mock_start_threads.assert_called_once()
            mock_process_output.assert_called_once()
            mock_join_threads.assert_called_once()


if __name__ == "__main__":
    unittest.main()
