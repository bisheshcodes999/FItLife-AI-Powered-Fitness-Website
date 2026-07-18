"""Download real images for workout/meal/success records into media/ and fix
records whose ImageField contains a URL string (bad seed data) or is empty.

Usage:  python manage.py fetch_images
Safe to run repeatedly — skips records that already have a proper local image.
If a download fails (offline), generates a styled placeholder with Pillow.
"""

import io
import random
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from ...models import MealPlan, SuccessStory, WorkoutPlan

WORKOUT_URLS = [
    "https://images.unsplash.com/photo-1571019614242-c955c175d3f3?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1534258936925-c58bed479fc3?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1581009137042-c552e485697a?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1517343985841-f8b2d66e010b?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1576678927484-cc907957088c?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=900&q=80&fm=jpg",
]
MEAL_URLS = [
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900&q=80&fm=jpg",
]
SUCCESS_URLS = [
    "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1541532713592-79a0317b6b77?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1549068106-b024baf5062d?w=900&q=80&fm=jpg",
    "https://images.unsplash.com/photo-1581044777550-4cfa60707c03?w=900&q=80&fm=jpg",
]

GRADIENTS = [((16, 185, 129), (6, 78, 59)), ((59, 130, 246), (30, 27, 75)),
             ((249, 115, 22), (69, 26, 3)), ((236, 72, 153), (76, 5, 25))]


def download(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception:
        return None


def placeholder(title: str) -> bytes:
    """Gradient placeholder with the plan title (offline fallback)."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 900, 500
    top, bottom = random.choice(GRADIENTS)
    img = Image.new("RGB", (W, H))
    for y in range(H):
        t = y / H
        img.paste(tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
                  (0, y, W, y + 1))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 44)
    except Exception:
        font = ImageFont.load_default()
    text = title[:40]
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - bbox[2]) / 2, (H - bbox[3]) / 2), text,
              fill=(255, 255, 255), font=font)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def needs_image(field) -> bool:
    """True if empty or contains a URL string instead of a real file."""
    if not field or not field.name:
        return True
    return field.name.startswith("http") or "images.unsplash.com" in field.name


class Command(BaseCommand):
    help = "Download/generate images for workouts, meals and success stories"

    def fix(self, obj, field_name, urls, label):
        field = getattr(obj, field_name)
        if not needs_image(field):
            return False
        title = getattr(obj, "title", None) or getattr(obj, "name", str(obj))
        data = download(random.choice(urls)) or placeholder(title)
        fname = f"{obj.pk}_{title[:30].replace(' ', '_').lower()}.jpg"
        getattr(obj, field_name).save(fname, ContentFile(data), save=True)
        self.stdout.write(f"  ✓ {label}: {title}")
        return True

    def handle(self, *args, **options):
        fixed = 0
        self.stdout.write("Workout plans...")
        for w in WorkoutPlan.objects.all():
            fixed += self.fix(w, "thumbnail", WORKOUT_URLS, "workout")
        self.stdout.write("Meal plans...")
        for m in MealPlan.objects.all():
            fixed += self.fix(m, "image", MEAL_URLS, "meal")
        self.stdout.write("Success stories...")
        for s in SuccessStory.objects.all():
            for f in ("image", "before_image", "after_image"):
                if hasattr(s, f):
                    fixed += self.fix(s, f, SUCCESS_URLS, f"story {f}")
        self.stdout.write(self.style.SUCCESS(f"Done — {fixed} images fixed."))
