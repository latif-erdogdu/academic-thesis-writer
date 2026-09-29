"""Ortak cekirdek: kimlik, tip, durum ve onay yonetimi.

Disa aktarilan yuzey:

- ``tools.atw.ids``   -- kimlik uretimi ve dogrulama
- ``tools.atw.types`` -- calisma-zamani tipleri
- ``tools.atw.state`` -- sema yukleme, durum kaydetme/dogrulama, PRISMA

Onay kapilari ``state.APPROVAL_GATES`` ve ``state.human_approvals``
ile temsil edilir; kapilari ``tools.atw.approval`` uygular.
"""
