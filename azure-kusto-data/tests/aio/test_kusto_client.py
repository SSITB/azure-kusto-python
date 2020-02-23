"""Tests for KustoClient."""
import json

import pytest
from aioresponses import aioresponses, CallbackResult
from azure.kusto.data._decorators import aio_documented_by
from azure.kusto.data.aio.request import KustoClient
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table
from azure.kusto.data.request import ClientRequestProperties

from .case import TestCase
from ..kusto_client_common import KustoClientTestsMixin, mocked_requests_post
from ..test_kusto_client import KustoClientTestsTests as KustoClientTestsSync

PANDAS = False
try:
    import pandas

    PANDAS = True
except:
    pass

aio_installed = False
try:
    import asgiref

    aio_installed = True
except:
    pass


@pytest.mark.skipif(not aio_installed, reason="requires aio")
@aio_documented_by(KustoClientTestsSync)
class KustoClientTestsTests(TestCase, KustoClientTestsMixin):
    @staticmethod
    def _mock_callback(url, **kwargs):
        body = json.dumps(mocked_requests_post(str(url), **kwargs).json())
        return CallbackResult(status=200, body=body)

    def _mock_query(self, aioresponses):
        url = "{host}/v2/rest/query".format(host=self.HOST)
        aioresponses.post(url, callback=self._mock_callback)

    def _mock_mgmt(self, aioresponses):
        url = "{host}/v1/rest/mgmt".format(host=self.HOST)
        aioresponses.post(url, callback=self._mock_callback)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_sanity_query)
    def test_sanity_query(self, aioresponses):
        self._mock_query(aioresponses)
        client = KustoClient(self.HOST)
        response = self.loop.run_until_complete(client.execute_query("PythonTest", "Deft"))
        self._assert_sanity_query_response(response)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_sanity_control_command)
    def test_sanity_control_command(self, aioresponses):
        self._mock_mgmt(aioresponses)
        client = KustoClient(self.HOST)
        response = self.loop.run_until_complete(client.execute_mgmt("NetDefaultDB", ".show version"))
        self._assert_sanity_control_command_response(response)

    @pytest.mark.skipif(not PANDAS, reason="requires pandas")
    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_sanity_data_frame)
    def test_sanity_data_frame(self, aioresponses):
        self._mock_query(aioresponses)
        client = KustoClient(self.HOST)
        response = self.loop.run_until_complete(client.execute_query("PythonTest", "Deft"))
        data_frame = dataframe_from_result_table(response.primary_results[0])
        self._assert_sanity_data_frame_response(data_frame)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_partial_results)
    def test_partial_results(self, aioresponses):
        client = KustoClient(self.HOST)
        query = """set truncationmaxrecords = 5;
range x from 1 to 10 step 1"""
        properties = ClientRequestProperties()
        properties.set_option(ClientRequestProperties.results_defer_partial_query_failures_option_name, False)
        self._mock_query(aioresponses)
        with self.assertRaises(KustoServiceError):
            self.loop.run_until_complete(client.execute_query("PythonTest", query, properties))
        properties.set_option(ClientRequestProperties.results_defer_partial_query_failures_option_name, True)
        self._mock_query(aioresponses)
        response = self.loop.run_until_complete(client.execute_query("PythonTest", query, properties))
        self._assert_partial_results_response(response)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_admin_then_query)
    def test_admin_then_query(self, aioresponses):
        self._mock_mgmt(aioresponses)
        client = KustoClient(self.HOST)
        query = ".show tables | project DatabaseName, TableName"
        response = self.loop.run_until_complete(client.execute_mgmt("PythonTest", query))
        self._assert_admin_then_query_response(response)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_dynamic)
    def test_dynamic(self, aioresponses):
        self._mock_query(aioresponses)
        client = KustoClient(self.HOST)
        query = """print dynamic(123), dynamic("123"), dynamic("test bad json"),"""
        """ dynamic(null), dynamic('{"rowId":2,"arr":[0,2]}'), dynamic({"rowId":2,"arr":[0,2]})"""
        response = self.loop.run_until_complete(client.execute_query("PythonTest", query))
        row = response.primary_results[0].rows[0]
        self._assert_dynamic_response(row)

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_empty_result)
    def test_empty_result(self, aioresponses):
        self._mock_query(aioresponses)
        client = KustoClient(self.HOST)
        query = """print 'a' | take 0"""
        response = self.loop.run_until_complete(client.execute_query("PythonTest", query))
        assert response.primary_results[0]

    @aioresponses()
    @aio_documented_by(KustoClientTestsSync.test_null_values_in_data)
    def test_null_values_in_data(self, aioresponses):
        self._mock_query(aioresponses)
        client = KustoClient(self.HOST)
        query = "PrimaryResultName"
        response = self.loop.run_until_complete(client.execute_query("PythonTest", query))
        assert response is not None