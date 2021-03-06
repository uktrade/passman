from django.core.management.base import BaseCommand
from django.db import transaction

from django.contrib.auth.models import Group

import psycopg2
import psycopg2.extras

from audit.models import Audit
from secret.models import Secret
from user.models import User

GET_CRED_SQL = (
    "SELECT cc.*, ag.name as owner_group_name FROM cred_cred as cc "
    "LEFT JOIN auth_group as ag ON cc.group_id = ag.id "
    "WHERE cc.latest_id is null;"
)
GET_GROUP_SQL = "SELECT name FROM auth_group;"
GET_VIEWER_GROUPS = (
    "SELECT ag.name from auth_group as ag "
    "INNER JOIN cred_cred_groups as ccg ON ag.id = ccg.group_id "
    "WHERE ccg.cred_id = {};"
)
GET_AUDIT_SQL = (
    "SELECT cca.audittype, au.email, cca.time FROM cred_credaudit cca "
    "INNER JOIN auth_user au ON cca.user_id = au.id "
    "WHERE cca.cred_id = {} "
    "ORDER BY time;"
)
GET_USER_SQL = (
    "SELECT au.email, string_agg(ag.name, '|') as groups FROM auth_group ag "
    "INNER JOIN auth_user_groups aug on aug.group_id = ag.id "
    "INNER JOIN auth_user au on aug.user_id = au.id "
    "WHERE au.is_active=true "
    "GROUP BY au.email;"
)

CHANGE_PERM = "change_secret"
VIEW_PERM = "view_secret"

# rattic audit actions
CREDADD = "A"
CREDCHANGE = "C"
CREDMETACHANGE = "M"
CREDVIEW = "V"
CREDEXPORT = "X"
CREDPASSVIEW = "P"
CREDDELETE = "D"
CREDSCHEDCHANGE = "S"
CREDAUDITCHOICES = dict(
    (
        (CREDADD, "Added"),
        (CREDCHANGE, "Changed"),
        (CREDMETACHANGE, "Only Metadata Changed"),
        (CREDVIEW, "Only Details Viewed"),
        (CREDEXPORT, "Exported"),
        (CREDDELETE, "Deleted"),
        (CREDSCHEDCHANGE, "Scheduled For Change"),
        (CREDPASSVIEW, "Password Viewed"),
    )
)


class Command(BaseCommand):
    help = (
        "Import credential, group and audit data from an existing Ratticweb database "
        "NOTE: this command is not idempotent"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Non destructive / do not updated database",
        )
        parser.add_argument("--dbname", required=True)
        parser.add_argument("--user")
        parser.add_argument("--host", default="localhost")
        parser.add_argument("--password")

    def connect_to_rattic_db(self, dbname, user, host, password):
        conn_str = f"dbname='{dbname}' host='{host}'"
        if user:
            conn_str += f" user='{user}'"

        if password:
            conn_str += f" password='{password}'"

        try:
            return psycopg2.connect(conn_str)
        except BaseException:
            redacted_conn = conn_str.replace(f"password='{password}'", "password='*******'")
            self.stdout.write(
                self.style.ERROR(f"cannot connect to the database with: {redacted_conn}")
            )
            raise

    def get_viewer_groups(self, conn, cred_id):
        """return a list of viewer groups"""
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(GET_VIEWER_GROUPS.format(cred_id))

        rows = cur.fetchall()
        for row in rows:
            yield row[0]

    def get_audit_events(self, conn, cred_id):
        """return a list of audit events"""
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(GET_AUDIT_SQL.format(cred_id))

        rows = cur.fetchall()
        for row in rows:
            yield row[0], row[1], row[2]

    def import_groups(self, conn, dry_run):
        """ Import groups from rattic into passman """
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(GET_GROUP_SQL)

        rows = cur.fetchall()
        for count, row in enumerate(rows, 1):
            self.stdout.write("importing group: " + row[0])
            if not dry_run:
                Group.objects.get_or_create(name=row[0])

        return count

    def import_secrets(self, conn, dry_run):
        """ Import creds/secrets and set the owner/viewer groups """

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(GET_CRED_SQL)

        rows = cur.fetchall()

        for count, row in enumerate(rows, 1):
            self.stdout.write("importing secret: " + row[1])

            if not dry_run:
                secret = Secret.objects.create(
                    name=row[1], url=row[7], username=row[2], password=row[3], details=row[4],
                )

            # owner group
            og_name = row[-1]
            if og_name:
                self.stdout.write(f"giving change permissions for owner group: {og_name}")

                if not dry_run:
                    og = Group.objects.get(name=og_name)

                    secret.set_permission(og, CHANGE_PERM)

            cred_id = row[0]

            for vg_name in self.get_viewer_groups(conn, cred_id):
                if og_name and og_name == vg_name:
                    continue

                self.stdout.write(f"giving view permissions for viewer group: {vg_name}")

                if not dry_run:
                    vg = Group.objects.get(name=vg_name)

                    secret.set_permission(vg, VIEW_PERM)

            anon_user = User.objects.get(email="AnonymousUser")

            # import audit events
            for audit_type, user, timestamp in self.get_audit_events(conn, cred_id):
                audit_display = CREDAUDITCHOICES[audit_type]
                audit_details = f"[Rattic Import] {audit_display} by {user}"

                self.stdout.write(f"adding audit event: {audit_display}")

                if not dry_run:
                    audit = Audit.objects.create(
                        timestamp=timestamp,
                        user=anon_user,
                        secret=secret,
                        action="imported",
                        description=audit_details,
                    )

                    audit.timestamp = timestamp
                    audit.save()

        return count

    def import_users(self, conn, dry_run):
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(GET_USER_SQL)

        rows = cur.fetchall()

        for count, row in enumerate(rows, 1):

            email, groups = row[0].lower(), row[1].split("|")

            self.stdout.write(f"importing user: {email} with groups: {groups}")

            if not dry_run:
                user, created = User.objects.get_or_create(email=email)

                if created:
                    self.stdout.write(f"user created {email}")
                else:
                    self.stdout.write(f"user found {email}")

                for group in groups:
                    group = Group.objects.get(name=group)
                    user.groups.add(group)

                    self.stdout.write(f"adding {email} to {group}")

        return count

    @transaction.atomic
    def handle(self, *args, **options):

        try:
            conn = self.connect_to_rattic_db(
                options["dbname"], options["user"], options["host"], options["password"]
            )
        except BaseException:
            exit(1)

        total = self.import_groups(conn, options["dry_run"])

        self.stdout.write(f"\nSuccessfully imported {total} groups\n\n\n")

        total = self.import_secrets(conn, options["dry_run"])

        self.stdout.write(f"\nSuccessfully imported {total} secrets")

        total = self.import_users(conn, options["dry_run"])

        self.stdout.write(f"\nSuccessufly imported {total} users")

        self.stdout.write(self.style.SUCCESS("Done."))
