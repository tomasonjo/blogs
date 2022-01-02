import pyarrow as pa
import pyarrow.flight as flight
import base64
import json
import struct
import time as _time
from enum import Enum
from os import environ as env

_JOB_CYPHER = "cypherRead"
_JOB_GDS_READ = "gds.read"      # TODO: rename
_JOB_GDS_WRITE_NODES = "gds.write.nodes"
_JOB_GDS_WRITE_RELS = "gds.write.relationships"
_JOB_KHOP = "khop"
_JOB_STATUS = "jobStatus"
_JOB_INFO = "info"

_DEFAULT_HOST = env.get('NEO4J_ARROW_HOST', 'localhost')
_DEFAULT_PORT = int(env.get('NEO4J_ARROW_PORT', '9999'))

pa.enable_signal_handlers(True)

class JobStatus(Enum):
    INITIALIZING = "INITIALIZING"
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    PRODUCING = "PRODUCING"

class Neo4jArrow:
    """
    A client for interacting with a remote Neo4j Arrow service. Useful for
    working with large datasets, retrieving bulk data, and async batch jobs!
    """

    def __init__(self, user, password, location=(), tls=False, verifyTls=True):
        token = base64.b64encode(f'{user}:{password}'.encode('utf8'))
        self._options = flight.FlightCallOptions(headers=[
            (b'authorization', b'Basic ' + token)
        ])

        host, port = _DEFAULT_HOST, _DEFAULT_PORT
        if len(location) > 0:
            host = location[0]
        if len(location) > 1:
            port = location[1]
        if tls:
            self._location = flight.Location.for_grpc_tls(host, port)
        else:
            self._location = flight.Location.for_grpc_tcp(host, port)
        self._client = flight.FlightClient(self._location,
                disable_server_verification=(not verifyTls))

    def list_actions(self):
        """List all actions available on the server."""
        return list(self._client.list_actions(options=self._options))

    def list_flights(self):
        """List all known flights. (No filtering support yet.)"""
        return list(self._client.list_flights(options=self._options))

    def info(self):
        """Get info on the Neo4j Arrow server"""
        result = self._client.do_action((_JOB_INFO, b''), options=self._options) 
        return json.loads(next(result).body.to_pybytes())

    def _submit(self, action):
        """Attempt to ticket the given action/job"""
        results = self._client.do_action(action, options=self._options)
        return pa.flight.Ticket.deserialize((next(results).body.to_pybytes()))

    def cypher(self, cypher, database='neo4j', params={}):
        """Submit a Cypher job with optional parameters. Returns a ticket."""
        cypher_bytes = cypher.encode('utf8')
        db_bytes = database.encode('utf8')
        params_bytes = json.dumps(params).encode('utf8')

        # Our CypherMessage format is simple:
        #   - 16 bit unsigned length of the cypher byte string
        #   - the cypher byte string payload
        #   - 16 bit unsigned length of the database byte string
        #   - the database byte string payload
        #   - 16 bit unsigned length of the param json payload
        #   - the param json byte string payload
        fmt = f"!H{len(cypher_bytes)}sH{len(db_bytes)}sH{len(params_bytes)}s"
        buffer = struct.pack(fmt,
            len(cypher_bytes), cypher_bytes, 
            len(db_bytes), db_bytes,
            len(params_bytes), params_bytes)
        return self._submit((_JOB_CYPHER, buffer))

    def gds_nodes(self, graph, properties=[], database='neo4j', node_id='', filters=[], extra={}):
        """Submit a GDS job for streaming Node properties. Returns a ticket."""
        params = {
            'db': database,
            'graph': graph,
            'type': 'node',
            'node_id': node_id,
            'properties': properties,
            'filters': filters,
        }
        params.update(extra)
        params_bytes = json.dumps(params).encode('utf8')
        return self._submit((_JOB_GDS_READ, params_bytes))

    def gds_write_nodes(self, graph, database='neo4j', idField='_node_id_', labelsField='_labels_'):
        """Submit a GDS Write Job for creating Nodes and Node Properties."""
        params = {
             'db': database,
             'graph': graph,
             'idField': idField,
             'labelsField': labelsField,
         }
        params_bytes = json.dumps(params).encode('utf8')
        return self._submit((_JOB_GDS_WRITE_NODES, params_bytes))

    def gds_write_relationships(self, graph, database='neo4j', sourceField='_source_id_', targetField='_target_id_', typeField='_type_'):
        """Submit a GDS Write Job for creating Rels and Rel Properties."""
        params = {
             'db': database,
             'graph': graph,
             'sourceField': sourceField,
             'targetField': targetField,
             'typeField': typeField,
         }
        params_bytes = json.dumps(params).encode('utf8')
        return self._submit((_JOB_GDS_WRITE_RELS, params_bytes))

    def gds_relationships(self, graph, properties=[], database='neo4j', node_id='', filters=[], extra={}):
        """
        Submit a GDS job for streaming Relationship properties.
        Returns a ticket.
        """
        params = {
            'db': database,
            'graph': graph,
            'type': 'relationship',
            'node_id': node_id,
            'properties': properties,
            'filters': filters,
        }
        params.update(extra)
        params_bytes = json.dumps(params).encode('utf8')
        return self._submit((_JOB_GDS_READ, params_bytes))

    def khop(self, graph, database='neo4j', node_id='', rel_property='_type_', extra={}):
        """ Experimental K-Hop Job support """
        params = {
            'db': database,
            'graph': graph,
            'node_id': node_id,
            'type': 'khop',
            'properties': [rel_property],
            'filters': [],
        }
        params.update(extra)
        params_bytes = json.dumps(params).encode('utf8')
        return self._submit((_JOB_GDS_READ, params_bytes))

    def status(self, ticket):
        """Check job status for a ticket."""
        if type(ticket) == pa.flight.Ticket:
            buffer = ticket.serialize()
        else:
            buffer = ticket
        action = (_JOB_STATUS, buffer)
        results = self._client.do_action(action, options=self._options)
        return JobStatus(next(results).body.to_pybytes().decode('utf8'))
    
    def wait_for_job(self, ticket, status=JobStatus.PRODUCING, timeout=60):
        """Block until a given job (specified by a ticket) reaches a status."""
        start = _time.time()
        while _time.time() - start < timeout:
            try:
                if self.status(ticket) == status:
                    return True
            except Exception as e:
                print(f"no job (yet?): {e}")
            _time.sleep(1)
        return False
    
    def stream(self, ticket, timeout=60):
        """Read the stream associated with the given ticket."""
        self.wait_for_job(ticket, timeout=timeout)
        return self._client.do_get(ticket, options=self._options)

    def put_stream(self, ticket, data):
        """Write a stream to the server"""
        if type(data) is not pa.lib.Table:
            table = pa.table(data=data)
        else:
            table = data
        try:
            descriptor = pa.flight.FlightDescriptor.for_command(ticket.serialize())
            writer, _ = self._client.do_put(descriptor, table.schema, options=self._options)
            writer.write_table(table, max_chunksize=8192)
            writer.close()
            # TODO: server should be telling us what the results were...shouldn't assume!
            return table.num_rows, table.nbytes
        except Exception as e:
            printf("error during put_stream: {e}")
            return 0, 0

    def put_stream_batches(self, ticket, results):
        """Write a stream using a batch producer"""
        descriptor = pa.flight.FlightDescriptor.for_command(ticket.serialize())
        nbytes, num = 0, 0
        writer, _ = self._client.do_put(descriptor, results.schema, options=self._options)
        for (batch, _) in results:
            nbytes = nbytes + batch.nbytes
            writer.write_batch(batch)
            num = num + 1
        writer.close()
        print(f"wrote {num:,} batches, {nbytes:,} bytes")
        return (num, nbytes)

