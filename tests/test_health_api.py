from base_testcase import APITestBaseCase, URL


class HealthTest(APITestBaseCase):
    def test_healthz(self):
        response = self.app.get(URL + '/healthz')
        assert response.status == '200 OK'
