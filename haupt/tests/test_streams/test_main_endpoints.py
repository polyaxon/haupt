# import pytest
#
# from starlette.exceptions import HTTPException
#
# from polyaxon._utils.test_utils import set_store
# from tests.base.case import BaseTest
#
#
# @pytest.mark.endpoints_mark
# class TestMainEndpoints(BaseTest):
#     def setUp(self):
#         super().setUp()
#         set_store()
#
#     def test_index_404(self):
#         response = self.client.get("/")
#         assert response.status_code == 404
#
#     def test_404_page(self):
#         response = self.client.get("/404")
#         assert response.status_code == 404
#
#     def test_500_page(self):
#         with self.assertRaises(HTTPException):
#             self.client.get("/500")
#
#     def test_health_page(self):
#         response = self.client.get("/healthz")
#         assert response.status_code == 200
