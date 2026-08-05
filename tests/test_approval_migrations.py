from pathlib import Path

from scripts.apply_users_approval_migrations import MIGRATIONS, migration_body


def test_approval_migrations_are_ordered_and_transaction_body_is_clean():
    assert [path.name for path in MIGRATIONS] == [
        "v004_users-approval.sql",
        "v005_approval-rls.sql",
    ]
    for path in MIGRATIONS:
        assert isinstance(path, Path)
        body = migration_body(path)
        assert not body.upper().startswith("BEGIN;")
        assert not body.upper().endswith("COMMIT;")


def test_approval_rls_requires_an_active_user_and_avoids_recursive_policy():
    rls = migration_body(MIGRATIONS[1])
    assert "status = 'active'" in rls
    assert "SECURITY DEFINER" in rls
    assert "public.current_app_user_id()" in rls
    assert "SELECT role FROM users WHERE" not in rls
