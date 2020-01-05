from random import randint
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from spectree import SpecTree, Response

from .common import Query, Resp, JSON, LowerHeaders, Cookies


api = SpecTree('starlette')


@api.validate(headers=LowerHeaders, tags=['test', 'health'])
def ping(request):
    return JSONResponse({'msg': 'pong'})


@api.validate(
    query=Query,
    json=JSON,
    cookies=Cookies,
    resp=Response('HTTP_401', HTTP_200=Resp),
    tags=['api', 'test'])
async def user_score(request):
    score = [randint(0, request.context.json.limit) for _ in range(5)]
    score.sort(reverse=request.context.query.order)
    assert request.context.cookies.pub == 'abcdefg'
    return JSONResponse({
        'name': request.context.json.name,
        'score': score
    })


app = Starlette(routes=[
    Route('/ping', ping),
    Route('/api/user/{name}', user_score, methods=['POST']),
])
api.register(app)


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_starlette_validate(client):
    resp = client.get('/ping')
    assert resp.status_code == 422

    resp = client.get('/ping', headers={'lang': 'en-US'})
    assert resp.json() == {'msg': 'pong'}

    resp = client.post('/api/user/starlette')
    assert resp.status_code == 422

    resp = client.post(
        '/api/user/starlette?order=1',
        json=dict(name='starlette', limit=10),
        cookies=dict(pub='abcdefg'),
    ).json()
    assert resp['name'] == 'starlette'
    assert resp['score'] == sorted(resp['score'], reverse=1)

    resp = client.post(
        '/api/user/starlette?order=0',
        json=dict(name='starlette', limit=10),
        cookies=dict(pub='abcdefg'),
    ).json()
    assert resp['name'] == 'starlette'
    assert resp['score'] == sorted(resp['score'], reverse=0)


def test_starlette_doc(client):
    resp = client.get('/apidoc/openapi.json')
    assert resp.json() == api.spec

    resp = client.get('/apidoc/redoc')
    assert resp.status_code == 200

    resp = client.get('/apidoc/swagger')
    assert resp.status_code == 200