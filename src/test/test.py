import json
from typing import List

from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder


# class EMREKSVirtualCluster(BaseModel):
class EMREKSVirtualCluster(BaseModel):
    name: str


def get_virtual_clusters() -> List[EMREKSVirtualCluster]:
    r_value = [
        EMREKSVirtualCluster(name="xxx"),
        EMREKSVirtualCluster(name="yyy"),
    ]

    return r_value


res = get_virtual_clusters()
jsonable_dict = jsonable_encoder(res)

json_str = json.dumps(jsonable_dict)

print(json_str)