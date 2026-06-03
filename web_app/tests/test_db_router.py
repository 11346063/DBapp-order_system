from unittest import mock

from django.test import TestCase

from order_system.db_router import PrimaryReplicaRouter
from web_app.models.order import Order


class PrimaryReplicaRouterTest(TestCase):
    def setUp(self):
        self.router = PrimaryReplicaRouter()

    def test_read_routes_to_default_when_no_replica_configured(self):
        # DB_REPLICA_HOST 未設定（測試/本機環境）→ 讀取走 default
        with mock.patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("DB_REPLICA_HOST", None)
            self.assertEqual(self.router.db_for_read(Order), "default")

    def test_read_routes_to_replica_when_configured(self):
        with mock.patch.dict("os.environ", {"DB_REPLICA_HOST": "192.168.1.2"}):
            db = self.router.db_for_read(Order)
            self.assertIn(db, PrimaryReplicaRouter.REPLICAS)

    def test_write_routes_to_default(self):
        self.assertEqual(self.router.db_for_write(Order), "default")

    def test_migrate_only_on_default(self):
        self.assertTrue(self.router.allow_migrate("default", "web_app"))
        self.assertFalse(self.router.allow_migrate("replica", "web_app"))

    def test_allow_relation_within_db_set(self):
        class FakeObj:
            class _state:
                db = "default"

        class FakeObjReplica:
            class _state:
                db = "replica"

        self.assertTrue(self.router.allow_relation(FakeObj(), FakeObjReplica()))

    def test_allow_relation_outside_db_set(self):
        class FakeObj:
            class _state:
                db = "other_db"

        self.assertIsNone(self.router.allow_relation(FakeObj(), FakeObj()))
