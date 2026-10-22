"""Serve only uploaded images referenced by the public catalogue."""
import mimetypes
from pathlib import PurePosixPath
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe
from category.models import Category, HeroPoster
from store.models import Product


@require_safe
def catalogue_image(request, image_path):
    if '..' in PurePosixPath(image_path).parts or '\\' in image_path:
        raise Http404
    content_type = mimetypes.guess_type(image_path)[0]
    if content_type not in {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/avif'}:
        raise Http404
    referenced = (
        Product.objects.filter(Q(image_1=image_path) | Q(image_2=image_path) | Q(image_3=image_path)).exists()
        or Category.objects.filter(category_image=image_path).exists()
        or HeroPoster.objects.filter(image=image_path).exists()
    )
    if not referenced:
        raise Http404
    try:
        file = default_storage.open(image_path, 'rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404 from None
    response = FileResponse(file, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
