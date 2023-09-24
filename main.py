from pydantic import BaseModel
import json

from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.responses import FileResponse


from main_utils import (
    setup_network,
    ask_info,
    pay_from_to,
    get_node_details,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.nodes = setup_network()
    yield
    # Clean up the ML models and release the resources

app = FastAPI(lifespan=lifespan)


@app.get("/info")
async def get_info():
    data = ask_info(app)
    blocks = data["blocks"]
    last_block = blocks[-1]
    return {
        "block_height": len(blocks),
        "num_peers": len(app.nodes),
        "current_difficulty": last_block["header"]["difficulty"],
    }


@app.get("/peers")
async def get_peers():
    data = ask_info(app)
    return data["peers"]


@app.get("/blocks")
async def get_blocks():
    data = ask_info(app)
    blocks = data["blocks"]
    return {
        "block_height": len(blocks),
        "blocks": blocks,
    }


class Pay(BaseModel):
    from_id: str
    to_id: str
    amount: int


@app.post("/pay")
async def pay(data: Pay):
    pay_from_to(app, data.from_id, data.to_id, data.amount)
    return {
        "success": True
    }


class NodeInfoReq(BaseModel):
    node_id: str


@app.post("/nodeinfo")
async def node_info(nodeinfo: NodeInfoReq):
    node = [x for x in app.nodes if x.nid == nodeinfo.node_id]
    if not node:
        return {
            "success": False,
            "error": "No such node",
        }
    return {
        "success": True,
        "message": get_node_details(node[0]),
    }


@app.get("/")
async def home():
    return FileResponse("index.html")
