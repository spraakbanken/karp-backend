from apitest import TestBaseCase, URL


class HealthTest(TestBaseCase):
    def test_healthz(self):
        response = self.app.get(URL + '/healthz')
        assert response.status == '200 OK'
