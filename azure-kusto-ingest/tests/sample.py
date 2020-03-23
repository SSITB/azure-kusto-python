"""Samples on how to use Kusto Ingest client. Just Replace variables and run!"""

from azure.kusto.data.request import KustoConnectionStringBuilder
from azure.kusto.ingest import (
    KustoIngestClient,
    IngestionProperties,
    FileDescriptor,
    BlobDescriptor,
    StreamDescriptor,
    DataFormat,
    ReportLevel,
    IngestionMappingType,
    KustoStreamingIngestClient,

)
from azure.kusto.ingest.ingestion_properties import ColumnMapping

##################################################################
##                              AUTH                            ##
##################################################################
cluster = "https://ingest-ohbitton.dev.kusto.windows.net"

# In case you want to authenticate with AAD application.
client_id = "d5e0a24c-3a09-40ce-a1d6-dc5ab58dae66"
client_secret = "L+0hoM34kqC22XRniWOgkETwVvawiir2odEjYqZeyXA="

# read more at https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
authority_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"

kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(cluster, client_id, client_secret, authority_id)

# # In case you want to authenticate with AAD application certificate.
# filename = "path to a PEM certificate"
# with open(filename, "r") as pem_file:
#     PEM = pem_file.read()
#
# thumbprint = "certificate's thumbprint"
# kcsb = KustoConnectionStringBuilder.with_aad_application_certificate_authentication(cluster, client_id, PEM, thumbprint, authority_id)
#
# # In case you want to authenticate with AAD username and password
# username = "<username>"
# password = "<password>"
# kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(cluster, username, password, authority_id)

# In case you want to authenticate with AAD device code.
# Please note that if you choose this option, you'll need to autenticate for every new instance that is initialized.
# It is highly recommended to create one instance and use it for all of your queries.
# kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(cluster)

# The authentication method will be taken from the chosen KustoConnectionStringBuilder.
client = KustoIngestClient(kcsb)

# there are more options for authenticating - see azure-kusto-data samples

##################################################################
##                        INGESTION                             ##
##################################################################
column = ColumnMapping("ColA", "string")
column.setOrdinal(1)
column2 = ColumnMapping("ColB", "string")
column2.setOrdinal(0)
# there are a lot of useful properties, make sure to go over docs and check them out
ingestion_props = IngestionProperties(
    database="db1",
    table="tbl",
    dataFormat=DataFormat.CSV,
    # in case status update for success are also required
    reportLevel=ReportLevel.FailuresAndSuccesses,
    # in case a mapping is required
    # ingestionMappingReference="{json_mapping_that_already_exists_on_table}"
    # ingestionMappingType=IngestionMappingType.Json
    ingestionMapping=[column, column2]
)

# ingest from file
file_descriptor = FileDescriptor("C:\\Users\\ohbitton\\Desktop\\csv.csv", 8)  # 3333 is the raw size of the data in bytes.
client.ingest_from_file(file_descriptor, ingestion_properties=ingestion_props)
# client.ingest_from_file("{filename}.csv", ingestion_properties=ingestion_props)


# ingest from blob
# blob_descriptor = BlobDescriptor("https://{path_to_blob}.csv.gz?sas", 10)  # 10 is the raw size of the data in bytes.
# client.ingest_from_blob(blob_descriptor, ingestion_properties=ingestion_props)

# ingest from dataframe
# import pandas
#
# fields = ["id", "name", "value"]
# rows = [[1, "abc", 15.3], [2, "cde", 99.9]]
#
# df = pandas.DataFrame(data=rows, columns=fields)
#
# client.ingest_from_dataframe(df, ingestion_properties=ingestion_props)

# ingest a whole folder.
# import os
#
# path = "folder/path"
# [client.ingest_from_file(f, ingestion_properties=ingestion_props) for f in os.listdir(path)]

##################################################################
##                        INGESTION STATUS                      ##
##################################################################

# if status updates are required, something like this can be done
import pprint
import time
from azure.kusto.ingest.status import KustoIngestStatusQueues

qs = KustoIngestStatusQueues(client)

MAX_BACKOFF = 180

backoff = 1
while True:
    ################### NOTICE ####################
    # in order to get success status updates,
    # make sure ingestion properties set the
    # reportLevel=ReportLevel.FailuresAndSuccesses.
    if qs.success.is_empty() and qs.failure.is_empty():
        time.sleep(backoff)
        backoff = min(backoff * 2, MAX_BACKOFF)
        print("No new messages. backing off for {} seconds".format(backoff))
        continue

    backoff = 1

    success_messages = qs.success.pop(10)
    failure_messages = qs.failure.pop(10)

    pprint.pprint("SUCCESS : {}".format(success_messages))
    pprint.pprint("FAILURE : {}".format(failure_messages))

    # you can of course separate them and dump them into a file for follow up investigations
    with open("successes.log", "w+") as sf:
        for sm in success_messages:
            sf.write(str(sm))

    with open("failures.log", "w+") as ff:
        for fm in failure_messages:
            ff.write(str(fm))

##################################################################
##                        STREAMING INGEST                      ##
##################################################################

# Authenticate against this cluster endpoint as shows in the Auth section
cluster = "https://{cluster_name}.kusto.windows.net"

client = KustoStreamingIngestClient(kcsb)

ingestion_props = IngestionProperties(database="{database_name}", table="{table_name}", dataFormat=DataFormat.CSV)

# ingest from file
file_descriptor = FileDescriptor("{filename}.csv", 3333)  # 3333 is the raw size of the data in bytes.
client.ingest_from_file(file_descriptor, ingestion_properties=ingestion_props)
client.ingest_from_file("{filename}.csv", ingestion_properties=ingestion_props)

# ingest from dataframe
import pandas

fields = ["id", "name", "value"]
rows = [[1, "abc", 15.3], [2, "cde", 99.9]]

df = pandas.DataFrame(data=rows, columns=fields)

client.ingest_from_dataframe(df, ingestion_properties=ingestion_props)

# ingest from stream
byte_sequence = b"56,56,56"
bytes_stream = io.BytesIO(byte_sequence)
client.ingest_from_stream(bytes_stream, ingestion_properties=ingestion_properties)

stream_descriptor = StreamDescriptor(bytes_stream)
client.ingest_from_stream(stream_descriptor, ingestion_properties=ingestion_properties)

str_sequence = u"57,57,57"
str_stream = io.StringIO(str_sequence)
client.ingest_from_stream(str_stream, ingestion_properties=ingestion_properties)
