import pytest

from yeelib.upnp import SSDPMessage, SSDPResponse, SSDPRequest
from . import fixtures


class TestSSDPMessage:
    def test_headers_copy(self):
        headers = [('Cache-Control', 'max-age=3600')]
        msg = SSDPMessage(headers=headers)
        assert msg.headers == headers
        assert msg.headers is not headers

    def test_headers_dict(self):
        headers = {'Cache-Control': 'max-age=3600'}
        msg = SSDPMessage(headers=headers)
        assert msg.headers == [('Cache-Control', 'max-age=3600')]

    def test_headers_none(self):
        msg = SSDPMessage(headers=None)
        assert msg.headers == []

    def test_parse(self):
        with pytest.raises(NotImplementedError):
            SSDPMessage.parse('')

    def test_parse_headers(self):
        headers = SSDPMessage.parse_headers('Cache-Control: max-age=3600')
        assert headers == [('Cache-Control', 'max-age=3600')]


class TestSSDPResponse:
    def test_parse(self):
        response = SSDPResponse.parse(fixtures.response.decode())
        assert response.status_code == 200
        assert response.reason == 'OK'


class TestSSDPRequest:
    def test_parse(self):
        request = SSDPRequest.parse(fixtures.request.decode())
        assert request.method == 'NOTIFY'
        assert request.uri == '*'

    def test_str(self):
        request = SSDPRequest('NOTIFY', '*', headers=[('Cache-Control', 'max-age=3600')])
        assert str(request) == (
            'NOTIFY * HTTP/1.1\n'
            'Cache-Control: max-age=3600'
        )

    def test_bytes(self):
        request = SSDPRequest.parse(fixtures.request.decode())
        assert bytes(request) == fixtures.request
