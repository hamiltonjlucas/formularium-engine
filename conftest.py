# Test-time path shim: protoc emits absolute sibling imports inside gen/ (e.g.
# `import hamiltonjlucas_formularium_types_messages_pb2`) because messages.proto
# embeds imported types. The platform service runtime has gen/ on its path; this
# gives pytest the same view. Not generated — safe to keep.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen"))
