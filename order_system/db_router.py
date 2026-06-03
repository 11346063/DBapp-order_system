import os
import random


class PrimaryReplicaRouter:
    """
    讀寫分離 Router。
    db_for_read  → replica（SELECT），僅在 DB_REPLICA_HOST 已設定時啟用；
                   否則回傳 default，確保測試環境與單機開發不受影響。
    db_for_write → default（Primary，INSERT/UPDATE/DELETE）
    transaction.atomic() 內 Django 自動將讀也導向 default，無需額外處理。
    """

    REPLICAS = ["replica"]

    @staticmethod
    def _replica_configured():
        return bool(os.getenv("DB_REPLICA_HOST"))

    def db_for_read(self, model, **hints):
        if self._replica_configured():
            return random.choice(self.REPLICAS)
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        db_set = {"default", *self.REPLICAS}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
