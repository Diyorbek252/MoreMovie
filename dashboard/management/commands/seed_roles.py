"""Rollarni (Django guruhlarini) ``dashboard/roles.py`` dagi lug'atdan yaratadi.

Ishlatish:
    python manage.py seed_roles
    python manage.py seed_roles --dry-run
    python manage.py seed_roles --assign-existing-staff "Content Manager"

Data migration emas, boshqaruv komandasi — sababi: ``Permission``
qatorlari ``post_migrate`` signali orqali yaratiladi, shuning uchun
xotira (migration) faylida ularni izlash yangi bazada muvaffaqiyatsiz
tugashi mumkin. Bu komanda esa istalgan vaqt qayta ishga tushirilishi
mumkin (idempotent) — mavjud guruhning ruxsatlari to'liq almashtiriladi,
yangi rol qo'shilsa yaratiladi.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

from dashboard.roles import ROLES

User = get_user_model()


class Command(BaseCommand):
    help = "Rol guruhlarini (Content Manager, Moderator, Editor, Analyst) yaratadi/yangilaydi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Hech narsa yozmasdan, faqat nima qilinishini ko'rsatadi.",
        )
        parser.add_argument(
            "--assign-existing-staff", metavar="ROL_NOMI",
            help=(
                "Superuser bo'lmagan, hech qanday guruhga tegishli bo'lmagan "
                "mavjud xodimlarni shu rolga qo'shadi (masalan 'Content Manager') "
                "— ruxsat tizimi yoqilganda hech kim panel'dan chetlab qolmasligi uchun."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        for role_name, codenames in ROLES.items():
            self._sync_group(role_name, codenames, dry_run=dry_run)

        if options["assign_existing_staff"]:
            self._assign_existing_staff(options["assign_existing_staff"], dry_run=dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: hech narsa saqlanmadi."))

    def _sync_group(self, role_name, codenames, dry_run):
        permissions = []
        missing = []

        for full_code in codenames:
            app_label, codename = full_code.split(".", 1)
            try:
                permissions.append(
                    Permission.objects.get(content_type__app_label=app_label, codename=codename)
                )
            except Permission.DoesNotExist:
                missing.append(full_code)

        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"«{role_name}»: {len(missing)} ta ruxsat hali topilmadi "
                    f"(model/migratsiya hali yaratilmagan bo'lishi mumkin): "
                    f"{', '.join(missing)}"
                )
            )

        if dry_run:
            self.stdout.write(f"«{role_name}»: {len(permissions)} ta ruxsat qo'llanadi (dry-run).")
            return

        group, created = Group.objects.get_or_create(name=role_name)
        group.permissions.set(permissions)

        verb = "yaratildi" if created else "yangilandi"
        self.stdout.write(
            self.style.SUCCESS(f"«{role_name}» guruhi {verb} — {len(permissions)} ta ruxsat.")
        )

    def _assign_existing_staff(self, role_name, dry_run):
        try:
            group = Group.objects.get(name=role_name)
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"«{role_name}» nomli guruh topilmadi."))
            return

        # Superuser va allaqachon biror guruhga tegishli xodimlarni tegmaymiz.
        orphan_staff = User.objects.filter(is_staff=True, is_superuser=False).filter(
            Q(groups__isnull=True)
        ).distinct()

        count = orphan_staff.count()

        if dry_run:
            self.stdout.write(f"{count} ta xodim «{role_name}» ga qo'shiladi (dry-run).")
            return

        for user in orphan_staff:
            user.groups.add(group)

        self.stdout.write(
            self.style.SUCCESS(f"{count} ta mavjud xodim «{role_name}» guruhiga qo'shildi.")
        )
