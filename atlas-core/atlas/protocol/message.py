import json
import time
import uuid
from typing import Dict, Any, Optional, List

class TIPMessage:
    """
    Base message format for the Topology Interchange Protocol (TIP).
    """
    def __init__(self, sender_id: str, payload: Dict[str, Any], msg_type: str):
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.timestamp = int(time.time())
        self.msg_type = msg_type
        self.payload = payload
        self.version = "1.0"
        
    def to_json(self) -> str:
        return json.dumps({
            "header": {
                "message_id": self.message_id,
                "sender_id": self.sender_id,
                "timestamp": self.timestamp,
                "type": self.msg_type,
                "version": self.version
            },
            "payload": self.payload
        })
        
    @classmethod
    def from_json(cls, json_str: str) -> 'TIPMessage':
        data = json.loads(json_str)
        header = data["header"]
        msg = cls(
            sender_id=header["sender_id"],
            payload=data["payload"],
            msg_type=header["type"]
        )
        msg.message_id = header["message_id"]
        msg.timestamp = header["timestamp"]
        msg.version = header.get("version", "1.0")
        return msg

class TopologyAdvertisement(TIPMessage):
    """
    A message broadcasting a node's topological signature for dataset discovery.
    """
    def __init__(self, sender_id: str, signature_hash: str, domain: str, tags: Optional[List[str]] = None):
        payload = {
            "signature": signature_hash,
            "domain": domain,
            "tags": tags or []
        }
        super().__init__(sender_id=sender_id, payload=payload, msg_type="TOPOLOGY_ADVERT")

class SimilarityQuery(TIPMessage):
    """
    A message querying the network for datasets similar to the provided signature.
    """
    def __init__(self, sender_id: str, query_signature: str, threshold: float = 0.8):
        payload = {
            "query_signature": query_signature,
            "threshold": threshold # Minimum Hamming similarity required
        }
        super().__init__(sender_id=sender_id, payload=payload, msg_type="SIMILARITY_QUERY")
