"""Ortak cekirdek: kimlik, tip, durum ve onay yonetimi.

Disa aktarilan yuzey (P0-1 sonunda etkinlesir):

- ``tools.atw.ids``   -- kimlik uretimi ve dogrulama
- ``tools.atw.types`` -- calisma-zamani tipleri
- ``tools.atw.state`` -- sema yukleme, durum kaydetme/dogrulama, PRISMA

``tools.atw.approval`` P0-4'te eklenir; onay kapilari P0-1'de
``state.APPROVAL_GATES`` ve ``state.human_approvals`` ile temsil edilir.
"""
